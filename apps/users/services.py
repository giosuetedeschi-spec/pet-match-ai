import json
import io
import zipfile
from typing import Dict, Any
from django.contrib.auth import get_user_model

User = get_user_model()


class GDPRExportService:
    """
    Servizio per la raccolta e l'esportazione di tutti i dati personali dell'utente
    in ottemperanza all'Art. 20 del GDPR (Diritto alla Portabilità dei Dati).
    """

    @staticmethod
    def aggregate_user_data(user: User) -> Dict[str, Any]:
        """
        Raccoglie tutti i dati utente da ogni modulo del sistema in una struttura dizionario.
        """
        data = {
            "account_information": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "phone_number": user.phone_number,
                "address": user.address,
                "city": user.city,
                "province": user.province,
                "postal_code": user.postal_code,
                "gdpr_consent": user.gdpr_consent,
                "gdpr_consent_date": user.gdpr_consent_date.isoformat() if user.gdpr_consent_date else None,
                "marketing_consent": user.marketing_consent,
                "date_joined": user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
            },
            "profile": {},
            "gdpr_consent_logs": [],
            "applications": [],
            "match_results": []
        }

        # 1. Profilo Adottante o Rifugio
        if user.role == User.Role.ADOPTER and hasattr(user, 'adopter_profile'):
            p = user.adopter_profile
            data["profile"] = {
                "housing_type": p.housing_type,
                "garden_sqm": p.garden_sqm,
                "family_members_count": p.family_members_count,
                "has_children": p.has_children,
                "children_ages_info": p.children_ages_info,
                "has_other_pets": p.has_other_pets,
                "other_pets_details": p.other_pets_details,
                "hours_away_from_home": p.hours_away_from_home,
                "activity_level": p.activity_level,
                "experience_level": p.experience_level,
                "monthly_budget_approx": str(p.monthly_budget_approx),
                "preferred_species": p.preferred_species
            }
        elif user.role == User.Role.SHELTER and hasattr(user, 'shelter_profile'):
            s = user.shelter_profile
            data["profile"] = {
                "shelter_name": s.shelter_name,
                "tax_code_vat": s.tax_code_vat,
                "official_email": s.official_email,
                "website_url": s.website_url,
                "description": s.description,
                "capacity_total": s.capacity_total,
                "is_verified": s.is_verified
            }

        # 2. Registro Audit Consensi GDPR
        for log in user.gdpr_consent_logs.all():
            data["gdpr_consent_logs"].append({
                "consent_type": log.consent_type,
                "granted": log.granted,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "privacy_policy_version": log.privacy_policy_version,
                "timestamp": log.timestamp.isoformat()
            })

        # 3. Candidature d'Adozione Inviate
        if hasattr(user, 'applications'):
            for app in user.applications.all():
                data["applications"].append({
                    "application_id": app.id,
                    "animal_id": app.animal_id,
                    "animal_name": app.animal.name,
                    "shelter_name": app.animal.shelter.shelter_name,
                    "status": app.status,
                    "motivational_notes": app.motivational_notes,
                    "compatibility_score_at_submission": app.compatibility_score_at_submission,
                    "submitted_at": app.submitted_at.isoformat(),
                    "updated_at": app.updated_at.isoformat()
                })

        # 4. Risultati Matching Salvati
        if hasattr(user, 'match_results'):
            for m in user.match_results.all():
                data["match_results"].append({
                    "animal_id": m.animal_id,
                    "animal_name": m.animal.name,
                    "overall_score": m.overall_score,
                    "score_breakdown": m.score_breakdown,
                    "calculated_at": m.calculated_at.isoformat()
                })

        return data

    @classmethod
    def generate_zip_export(cls, user: User) -> bytes:
        """
        Genera in memoria un archivio ZIP contenente il file JSON e gli allegati multimediali.
        """
        raw_data = cls.aggregate_user_data(user)
        json_bytes = json.dumps(raw_data, indent=4, ensure_ascii=False).encode('utf-8')

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Aggiunge il dump JSON dei dati
            zip_file.writestr('data_export.json', json_bytes)

            # Aggiunge l'eventuale foto avatar del profilo
            if user.avatar and hasattr(user.avatar, 'path'):
                try:
                    zip_file.write(user.avatar.path, arcname=f"media/{user.avatar.name}")
                except (FileNotFoundError, ValueError):
                    pass

        return zip_buffer.getvalue()