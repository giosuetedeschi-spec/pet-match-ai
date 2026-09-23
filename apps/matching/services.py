import os
import logging
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from django.conf import settings
from django.utils import timezone

from apps.users.models import User, AdopterProfile
from apps.core.models import Animal, AnimalSize, AnimalEnergy, Species
from apps.matching.models import MatchResult

logger = logging.getLogger(__name__)


class CoxSurvivalModelLoader:
    """
    Singleton class per il caricamento lazy e thread-safe del modello Cox Survival.
    Evita di ricaricare il file .joblib ad ogni singola richiesta di inferenza.
    """
    _instance: Optional['CoxSurvivalModelLoader'] = None
    _model: Any = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CoxSurvivalModelLoader, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        # Percorso predefinito all'interno del progetto
        model_path = getattr(
            settings,
            'COX_MODEL_PATH',
            os.path.join(settings.BASE_DIR, 'trained-model', 'cox_survival_model.joblib')
        )

        if os.path.exists(model_path):
            try:
                self._model = joblib.load(model_path)
                logger.info(f"Modello ML Cox Survival caricato con successo da {model_path}")
            except Exception as e:
                logger.error(f"Errore durante il caricamento del modello ML: {str(e)}")
                self._model = None
        else:
            logger.warning(f"File modello non trovato in {model_path}. L'inferenza ML userà valori di fallback.")
            self._model = None

    def predict(self, feature_df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        """
        Esegue l'inferenza usando il modello caricato.
        Ritorna: (tempo_stimato_giorni, probabilita_adozione_30giorni)
        """
        if self._model is None:
            # Fallback se il modello non è disponibile
            return None, None

        try:
            # Previsione del tempo mediano o atteso dal modello di sopravvivenza
            if hasattr(self._model, 'predict_expectation'):
                predicted_days = float(self._model.predict_expectation(feature_df).iloc[0])
            elif hasattr(self._model, 'predict'):
                predicted_days = float(self._model.predict(feature_df)[0])
            else:
                predicted_days = 45.0  # Valore stimato di default

            # Probabilità di essere ancora nel rifugio al giorno 30 (S(30))
            # Probabilità di adozione entro 30gg = 1 - S(30)
            if hasattr(self._model, 'predict_survival_function'):
                surv_func = self._model.predict_survival_function(feature_df)
                # Estrazione valore al giorno 30
                surv_30_prob = float(surv_func.loc[30].iloc[0]) if 30 in surv_func.index else 0.50
                adoption_prob_30d = float(np.clip(1.0 - surv_30_prob, 0.0, 1.0))
            else:
                adoption_prob_30d = 0.50

            return round(predicted_days, 1), round(adoption_prob_30d, 4)

        except Exception as e:
            logger.error(f"Errore durante l'inferenza del modello ML Cox: {str(e)}")
            return None, None


class MatchingService:
    """
    Servizio di business logic per il calcolo del punteggio di affinità
    e l'integrazione del modello predittivo tra Adottante ed Animale.
    """

    @staticmethod
    def calculate_match_score(adopter_profile: AdopterProfile, animal: Animal) -> Tuple[float, Dict[str, Any]]:
        """
        Calcola il punteggio di compatibilità deterministico pesato (0-100).
        Scompone il punteggio nelle sottocategorie: space, family, lifestyle, experience.
        """
        breakdown = {
            'space_score': 0.0,
            'family_score': 0.0,
            'lifestyle_score': 0.0,
            'experience_score': 0.0,
            'penalties': []
        }

        # 1. COMPATIBILITÀ SPAZIO E ABITAZIONE (Peso Max: 25 Punti)
        space_score = 25.0
        if animal.requires_garden:
            if adopter_profile.housing_type in [
                AdopterProfile.HousingType.APARTMENT_NO_BALCONY,
                AdopterProfile.HousingType.APARTMENT_BALCONY
            ] and adopter_profile.garden_sqm < 20:
                space_score -= 15.0
                breakdown['penalties'].append("L'animale richiede un giardino o uno spazio verde adeguato.")

        breakdown['space_score'] = max(0.0, space_score)

        # 2. COMPATIBILITÀ FAMIGLIA E ALTRI ANIMALI (Peso Max: 25 Punti)
        family_score = 25.0
        if adopter_profile.has_children and animal.good_with_children is False:
            family_score -= 20.0
            breakdown['penalties'].append("L'animale non è indicato per nuclei familiari con bambini.")

        if adopter_profile.has_other_pets:
            if animal.species == Species.DOG and animal.good_with_dogs is False:
                family_score -= 15.0
                breakdown['penalties'].append("Non idoneo alla convivenza con altri cani.")
            if animal.good_with_cats is False:
                family_score -= 15.0
                breakdown['penalties'].append("Non idoneo alla convivenza con gatti.")

        breakdown['family_score'] = max(0.0, family_score)

        # 3. COMPATIBILITÀ STILE DI VITA ED ENERGIA (Peso Max: 25 Punti)
        lifestyle_score = 25.0
        # Ore di solitudine
        if adopter_profile.hours_away_from_home > animal.max_hours_alone_per_day:
            diff = adopter_profile.hours_away_from_home - animal.max_hours_alone_per_day
            penalty = diff * 4.0
            lifestyle_score -= penalty
            breakdown['penalties'].append(f"Le ore di assenza ({adopter_profile.hours_away_from_home}h) superano la soglia consigliata ({animal.max_hours_alone_per_day}h).")

        # Livello di energia
        energy_map = {
            AnimalEnergy.LOW: 1,
            AnimalEnergy.MEDIUM: 2,
            AnimalEnergy.HIGH: 3,
            AnimalEnergy.VERY_HIGH: 4
        }
        activity_map = {
            AdopterProfile.ActivityLevel.SEDENTARY: 1,
            AdopterProfile.ActivityLevel.MODERATE: 2,
            AdopterProfile.ActivityLevel.ACTIVE: 4
        }
        
        e_val = energy_map.get(animal.energy_level, 2)
        a_val = activity_map.get(adopter_profile.activity_level, 2)
        energy_diff = abs(e_val - a_val)

        if energy_diff > 1:
            lifestyle_score -= (energy_diff * 5.0)
            breakdown['penalties'].append("Discrepanza tra il livello di energia dell'animale e lo stile di vita dell'adottante.")

        breakdown['lifestyle_score'] = max(0.0, lifestyle_score)

        # 4. COMPATIBILITÀ ESPERIENZA (Peso Max: 25 Punti)
        experience_score = 25.0
        exp_levels = {
            AdopterProfile.ExperienceLevel.BEGINNER: 1,
            AdopterProfile.ExperienceLevel.INTERMEDIATE: 2,
            AdopterProfile.ExperienceLevel.EXPERT: 3
        }

        user_exp = exp_levels.get(adopter_profile.experience_level, 1)
        req_exp = exp_levels.get(animal.required_experience_level, 1)

        if user_exp < req_exp:
            experience_score -= 15.0
            breakdown['penalties'].append("L'animale richiede un livello di esperienza cinofila/felina superiore.")

        breakdown['experience_score'] = max(0.0, experience_score)

        # Calcolo Punteggio Finale Globale
        overall_score = sum([
            breakdown['space_score'],
            breakdown['family_score'],
            breakdown['lifestyle_score'],
            breakdown['experience_score']
        ])

        return float(np.clip(overall_score, 0.0, 100.0)), breakdown

    @staticmethod
    def _prepare_ml_features(adopter_profile: AdopterProfile, animal: Animal) -> pd.DataFrame:
        """
        Trasforma i dati dell'animale e dell'adottante nel DataFrame richiesto dal modello ML Cox Survival.
        """
        size_encoded = {'SMALL': 1, 'MEDIUM': 2, 'LARGE': 3, 'GIANT': 4}.get(animal.size, 2)
        energy_encoded = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'VERY_HIGH': 4}.get(animal.energy_level, 2)
        exp_encoded = {'BEGINNER': 1, 'INTERMEDIATE': 2, 'EXPERT': 3}.get(adopter_profile.experience_level, 1)

        feature_dict = {
            'age_months': [animal.total_age_in_months],
            'size_encoded': [size_encoded],
            'energy_encoded': [energy_encoded],
            'is_spayed_neutered': [int(animal.is_spayed_neutered)],
            'is_vaccinated': [int(animal.is_vaccinated)],
            'good_with_children': [int(animal.good_with_children or False)],
            'good_with_dogs': [int(animal.good_with_dogs or False)],
            'good_with_cats': [int(animal.good_with_cats or False)],
            'requires_garden': [int(animal.requires_garden)],
            'adopter_experience_level': [exp_encoded],
            'adopter_hours_away': [adopter_profile.hours_away_from_home],
            'adopter_has_children': [int(adopter_profile.has_children)],
            'adopter_has_other_pets': [int(adopter_profile.has_other_pets)]
        }

        return pd.DataFrame(feature_dict)

    @classmethod
    def process_and_save_match(cls, adopter_user: User, animal: Animal) -> MatchResult:
        """
        Esegue il matching completo, interroga il modello ML e salva/aggiorna il record MatchResult.
        """
        try:
            adopter_profile = adopter_user.adopter_profile
        except AdopterProfile.DoesNotExist:
            raise ValueError(f"L'utente {adopter_user.username} non possiede un profilo Adottante completo.")

        # 1. Calcolo punteggio deterministico
        score, breakdown = cls.calculate_match_score(adopter_profile, animal)

        # 2. Preparazione Feature e Inferenza ML Cox
        feature_df = cls._prepare_ml_features(adopter_profile, animal)
        ml_loader = CoxSurvivalModelLoader()
        predicted_days, surv_30d_prob = ml_loader.predict(feature_df)

        # 3. Salvataggio o Aggiornamento a DB
        match_record, created = MatchResult.objects.update_or_create(
            adopter=adopter_user,
            animal=animal,
            defaults={
                'overall_score': round(score, 2),
                'score_breakdown': breakdown,
                'predicted_adoption_time_days': predicted_days,
                'survival_probability_30d': surv_30d_prob,
                'calculated_at': timezone.now()
            }
        )

        return match_record

    @classmethod
    def get_top_matches_for_adopter(cls, adopter_user: User, limit: int = 10):
        """
        Ricalcola (se necessario) ed estrae i migliori animali per l'adottante ordinati per punteggio.
        """
        available_animals = Animal.objects.filter(status='AVAILABLE')
        results = []

        for animal in available_animals:
            match_res = cls.process_and_save_match(adopter_user, animal)
            results.append(match_res)

        # Ordinamento descrescente per punteggio di compatibilità
        results.sort(key=lambda x: x.overall_score, reverse=True)
        return results[:limit]