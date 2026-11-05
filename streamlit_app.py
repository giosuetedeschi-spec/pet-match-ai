import json
import os
import re
from datetime import date, datetime, time
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import requests
import streamlit as st
import pandas as pd
import joblib
from pathlib import Path

API_BASE = os.getenv("PET_MATCH_API_URL", "http://127.0.0.1:8000").rstrip("/")
ML_BASE = os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
ML_TOKEN = os.getenv("ML_SERVICE_TOKEN", "local-development-token")
CHAT_BASE = os.getenv("CHAT_SERVICE_URL", "http://127.0.0.1:8002").rstrip("/")
CHAT_TOKEN = os.getenv("CHAT_SERVICE_TOKEN", "local-chat-token")
TIMEOUT = 20
MAX_IMAGE_SIZE = 5 * 1024 * 1024


class ApiError(RuntimeError):
    pass


def _headers(token=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def api_request(method, path, token=None, **kwargs):
    url = f"{API_BASE}/{path.lstrip('/')}"
    try:
        response = requests.request(
            method,
            url,
            headers={**_headers(token), **kwargs.pop("headers", {})},
            timeout=TIMEOUT,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise ApiError(f"Backend non raggiungibile ({API_BASE}). Avvia Django e riprova.") from exc

    if not response.ok:
        try:
            payload = response.json()
            detail = payload.get("detail") or json.dumps(payload, ensure_ascii=False)
        except (ValueError, AttributeError):
            detail = response.text or response.reason
        raise ApiError(f"{response.status_code}: {detail}")

    if not response.content:
        return None
    return response.json()


def list_results(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("results", [])
    return []


def comune_options(query):
    if len(query.strip()) < 2:
        return []
    return list_results(api_request("GET", "geo/comuni/?" + urlencode({"q": query.strip()})))


def reset_catalog_page():
    st.session_state.catalog_page = 1


def upload_images(animal_id, uploaded_files, alt_texts, token):
    if len(uploaded_files) != len(alt_texts) or any(not text.strip() for text in alt_texts):
        raise ApiError("Aggiungi una descrizione accessibile per ogni foto.")
    if any(file.size > MAX_IMAGE_SIZE for file in uploaded_files):
        raise ApiError("Ogni foto deve essere al massimo di 5 MB.")
    files = [
        ("images", (file.name, file.getvalue(), file.type or "application/octet-stream"))
        for file in uploaded_files
    ]
    data = [("alt_texts", text.strip()) for text in alt_texts]
    return api_request(
        "POST",
        f"animals/{animal_id}/images/upload/",
        token=token,
        files=files,
        data=data,
    )


def publish_animal(animal_id, token):
    return api_request(
        "POST",
        f"shelter/animals/{animal_id}/publish/",
        token=token,
    )


def preview_matches(answers):
    return api_request("POST", "matching/preview/", json=answers)


def public_return_risk_features(animal, answers):
    """Build dog return-risk inputs without filling unknown answers with guesses."""
    energy = {"LOW": 2, "MEDIUM": 5, "HIGH": 8, "VERY_HIGH": 10}.get(animal.get("energy_level"))
    size = {"SMALL": "small", "MEDIUM": "medium", "LARGE": "large", "GIANT": "xlarge"}.get(animal.get("size"))
    home_type = answers.get("ml_home_type")
    if home_type == "unknown":
        home_type = None
    medical_needs = None if animal.get("special_needs") is None else ("chronic" if animal["special_needs"] else "none")
    age_years = animal.get("age_years")
    age_months = animal.get("age_months")
    return {
        "age_years": float(age_years) + float(age_months or 0) / 12 if age_years is not None else (float(age_months) / 12 if age_months is not None else None),
        "size": size,
        "medical_needs": medical_needs,
        "neutered": int(bool(animal["is_spayed_neutered"])) if animal.get("is_spayed_neutered") is not None else None,
        "energy_level": energy,
        "first_time_owner": answers.get("ml_first_time_owner"),
        "household_has_kids": int(bool(answers["has_children"])),
        "household_has_pets": int(bool(answers["has_dogs"] or answers["has_cats"])),
        "home_type": home_type,
        "has_yard": int(float(answers["garden_sqm"]) > 0),
        "hours_alone_per_day": answers["hours_away_from_home"],
        "adopter_activity_level": {"SEDENTARY": 0, "MODERATE": 5, "ACTIVE": 10}.get(answers["activity_level"]),
        "visits_before_adoption": answers.get("ml_visits_before_adoption"),
        "met_resident_pets": answers.get("ml_met_resident_pets"),
        "adoption_counseling": answers.get("ml_adoption_counseling"),
        "expectation_score": answers.get("ml_expectation_score"),
    }


@st.cache_resource
def load_public_return_risk_model(model_dir=None):
    directory = Path(model_dir or os.getenv("ML_MODEL_DIR", Path(__file__).parent / "services" / "ml" / "models"))
    metadata = json.loads((directory / "model_metadata.json").read_text(encoding="utf-8"))
    return joblib.load(directory / "return_risk.joblib"), metadata["compatibility_return_risk"]


def score_public_return_risk(features, model_dir=None):
    model, metadata = load_public_return_risk_model(model_dir)
    columns = metadata["features"]
    row = pd.DataFrame([{key: features.get(key) for key in columns}], columns=columns)
    score = float(model.predict_proba(row)[0][1])
    return {"return_risk_score": round(score, 4), "model_version": metadata["version"]}


def ml_request(path, ref, features):
    """Call a staff-only model endpoint; never expose its output in adopter views."""
    try:
        response = requests.post(
            f"{ML_BASE}/{path.lstrip('/')}",
            headers={"Authorization": f"Bearer {ML_TOKEN}", "Accept": "application/json"},
            json={"ref": str(ref), "features": features},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ApiError(f"Servizio ML non raggiungibile ({ML_BASE}). Avvia il servizio ML e riprova.") from exc
    return response.json()["prediction"]


def chat_request(message, locale, history=None, catalog_animals=None, catalog_filters=None):
    try:
        response = requests.post(
            f"{CHAT_BASE}/chat",
            headers={"Authorization": f"Bearer {CHAT_TOKEN}", "Accept": "application/json"},
            json={"message": message, "locale": locale, "history": history or [], "catalog_animals": catalog_animals or [], "catalog_filters": catalog_filters or {}},
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ApiError(f"Assistente non raggiungibile ({CHAT_BASE}). Avvia il servizio assistant e riprova.") from exc
    return response.json()


def assistant_catalog_filters(message):
    """Parse explicit catalog constraints consistently for Django and RAG."""
    filters = {}
    params = {}
    text = message.strip()
    if re.search(r"\b(gatt\w*|cat|cats|kitten|kittens)\b", text, re.IGNORECASE) != bool(re.search(r"\b(can\w*|dog|dogs|puppy|puppies)\b", text, re.IGNORECASE)):
        species = "cat" if re.search(r"\b(gatt\w*|cat|cats|kitten|kittens)\b", text, re.IGNORECASE) else "dog"
        filters["species"] = species
        params["species"] = species.upper()
    asks_for_children = bool(re.search(r"\b(bambin\w*|bimbi|children|kids)\b", text, re.IGNORECASE))
    denies_children = bool(
        re.search(r"\b(non|not|without|no)\b.{0,28}\b(adatt\w*|compatibil\w*|good|suitable|safe)\b.{0,24}\b(bambin\w*|bimbi|children|kids)\b", text, re.IGNORECASE)
        or re.search(r"\b(senza|without|no)\b.{0,24}\b(bambin\w*|bimbi|children|kids)\b", text, re.IGNORECASE)
    )
    if asks_for_children and not denies_children:
        filters["good_with_children"] = True
        params["good_with_children"] = "true"
    city_matches = re.finditer(r"\b(?:vicino\s+a|near|around|in|a)\s+([\wÀ-ÿ'’-]+(?:\s+[\wÀ-ÿ'’-]+){0,3}?)(?=\s+(?:adatt\w*|compatibil\w*|senza\b|without\b|con\b|per\b|ai?\b|bambin\w*|children\b|kids\b|with\b|good\b|suitable\b|for\b|in\b|near\b|around\b|and\b|or\b)|[,;.!?]|$)", text, re.IGNORECASE)
    city = next((match.group(1).strip() for match in city_matches if not re.search(r"\b(dog|dogs|cat|cats|kitten|kittens|pet|pets)\b", match.group(1), re.IGNORECASE)), None)
    if city:
        filters["city"] = city
        params["city"] = city
    return params, filters


def predict_animal_outcome(animal):
    age = animal.get("total_age_in_months", animal.get("age_months", 0))
    intake_date = animal.get("date_entry_shelter")
    if intake_date:
        try:
            days_in_care = max(0, (date.today() - date.fromisoformat(intake_date[:10])).days)
            age = max(0, age - days_in_care / 30.4375)
        except ValueError:
            pass
    breed = (animal.get("breed_detail") or {}).get("name") or animal.get("breed_name") or "unknown"
    return ml_request("predict", animal["id"], {
        "age_months": age,
        "gender": animal.get("gender"),
        "species": animal.get("species"),
        "breed": breed,
    })


CATALOG_TEXT = {
    "it": {
        "title": "Animali in cerca di casa", "search": "Cerca per nome, razza o rifugio",
        "species": "Specie", "all_species": "Tutte", "city": "Comune", "province": "Provincia",
        "min_age": "Età minima", "max_age": "Età massima", "any_age": "Qualsiasi", "gender": "Sesso",
        "all_genders": "Tutti", "find": "Cerca", "empty": "Nessun animale corrisponde ai filtri. Prova a cambiarli.",
        "age": "Età: {years} anni e {months} mesi", "details": "Dettagli", "page": "Pagina {page} di {total}",
        "previous": "Precedenti", "next": "Successivi", "record": "Scheda animale", "shelter": "Rifugio",
        "close": "Chiudi scheda", "fallback": "Testo originale in italiano",
    },
    "en": {
        "title": "Animals looking for a home", "search": "Search by name, breed, or shelter",
        "species": "Species", "all_species": "All", "city": "Town", "province": "Province",
        "min_age": "Min age", "max_age": "Max age", "any_age": "Any", "gender": "Gender",
        "all_genders": "All", "find": "Search", "empty": "No animals match these filters. Try changing them.",
        "age": "Age: {years} years and {months} months", "details": "Details", "page": "Page {page} of {total}",
        "previous": "Previous", "next": "Next", "record": "Animal profile", "shelter": "Shelter",
        "close": "Close profile", "fallback": "Italian text (original)",
    },
}


def render_catalog():
    language = st.selectbox("Lingua / Language", ["Italiano", "English"], key="catalog_language")
    language_code = "en" if language == "English" else "it"
    text = CATALOG_TEXT[language_code]
    st.header(text["title"])
    origin_label = "Comune di partenza" if language_code == "it" else "Starting town"
    origin_query = st.text_input(
        "Cerca " + origin_label.lower() if language_code == "it" else "Search " + origin_label.lower(),
        key="catalog_origin_query",
    )
    try:
        origin_options = comune_options(origin_query)
    except ApiError as exc:
        st.error(str(exc))
        origin_options = []
    origin_labels = {item["istat_code"]: f'{item["name"]} ({item["province_abbreviation"]})' for item in origin_options}
    origin_codes = [item["istat_code"] for item in origin_options]
    if st.session_state.get("catalog_origin_comune") not in origin_codes:
        st.session_state.catalog_origin_comune = ""
    location_cols = st.columns([3, 1])
    origin_comune = location_cols[0].selectbox(
        origin_label,
        ["", *origin_codes],
        format_func=lambda code: origin_labels.get(code, "Qualsiasi comune" if language_code == "it" else "Any town"),
        key="catalog_origin_comune",
        on_change=reset_catalog_page,
    )
    radius = location_cols[1].selectbox(
        "Raggio (km)" if language_code == "it" else "Radius (km)",
        [25, 50, 100, 200, 500], index=1, key="catalog_radius_km",
        on_change=reset_catalog_page,
    )
    with st.form("catalog_filter_form"):
        search = st.text_input(text["search"])
        c1, c2, c3 = st.columns([2, 1, 1])
        species = c1.selectbox(text["species"], [text["all_species"], "DOG", "CAT"], format_func=lambda value: {"DOG": "Dog" if language_code == "en" else "Cane", "CAT": "Cat" if language_code == "en" else "Gatto"}.get(value, value))
        city = c2.text_input(text["city"])
        province = c3.text_input(text["province"], max_chars=10)
        ages = [text["any_age"], *range(41)]
        c4, c5, c6 = st.columns(3)
        min_age = c4.selectbox(text["min_age"], ages)
        max_age = c5.selectbox(text["max_age"], ages)
        gender = c6.selectbox(text["gender"], [text["all_genders"], "M", "F"], format_func=lambda value: {"M": "Male" if language_code == "en" else "Maschio", "F": "Female" if language_code == "en" else "Femmina"}.get(value, value))
        submitted = st.form_submit_button(text["find"])

    if "catalog_filter_values" not in st.session_state:
        st.session_state.catalog_filter_values = {"search": "", "species": "", "city": "", "province": "", "min_age_years": "", "max_age_years": "", "gender": ""}
    if "catalog_page" not in st.session_state:
        st.session_state.catalog_page = 1
    if submitted:
        st.session_state.catalog_page = 1
        st.session_state.catalog_filter_values = {
            "search": search.strip(),
            "species": "" if species == text["all_species"] else species,
            "city": city.strip(),
            "province": province.strip(),
            "min_age_years": "" if min_age == text["any_age"] else min_age,
            "max_age_years": "" if max_age == text["any_age"] else max_age,
            "gender": "" if gender == text["all_genders"] else gender,
        }

    params = {key: value for key, value in st.session_state.catalog_filter_values.items() if value}
    if origin_comune:
        params.update(comune=origin_comune, radius_km=radius)
    params["page"] = st.session_state.catalog_page
    query = urlencode(params)
    try:
        payload = api_request("GET", "catalog/animals/" + (f"?{query}" if query else ""))
    except ApiError as exc:
        st.error(str(exc))
        return

    animals = list_results(payload)
    if not animals:
        st.info(text["empty"])
        return

    locations = [
        {"lat": animal["latitude"], "lon": animal["longitude"], "name": animal.get("name", "")}
        for animal in animals if animal.get("latitude") is not None and animal.get("longitude") is not None
    ]
    if locations:
        st.map(pd.DataFrame(locations), latitude="lat", longitude="lon", size=12)

    for offset in range(0, len(animals), 3):
        columns = st.columns(3)
        for column, animal in zip(columns, animals[offset:offset + 3]):
            with column:
                if animal.get("primary_image"):
                    st.image(
                        animal["primary_image"],
                        caption=animal.get("primary_image_caption") or animal.get("name", "Animale"),
                        width="stretch",
                    )
                st.subheader(animal.get("name", "Animale"))
                species_labels = {"DOG": "Dog" if language_code == "en" else "Cane", "CAT": "Cat" if language_code == "en" else "Gatto"}
                st.caption(
                    f"{species_labels.get(animal.get('species'), animal.get('species_display', ''))} · "
                    f"{animal.get('breed_name') or ('Mixed breed' if language_code == 'en' else 'Meticcio')} · "
                    f"{animal.get('city', '')}"
                )
                if animal.get("distance_km") is not None:
                    unit = "km" if language_code == "it" else "km away"
                    st.caption(f'{animal["distance_km"]} {unit}')
                st.write(text["age"].format(years=animal.get('age_years', 0), months=animal.get('age_months', 0)))
                if st.button(text["details"], key=f"animal-{animal['id']}"):
                    st.session_state.selected_animal_id = animal["id"]

    if isinstance(payload, dict) and (payload.get("previous") or payload.get("next")):
        previous, summary, following = st.columns([1, 4, 1])
        page = st.session_state.catalog_page
        total_pages = max(1, (payload.get("count", len(animals)) + 11) // 12)
        summary.write(text["page"].format(page=page, total=total_pages))
        if payload.get("previous") and previous.button(text["previous"]):
            st.session_state.catalog_page -= 1
            st.rerun()
        if payload.get("next") and following.button(text["next"]):
            st.session_state.catalog_page += 1
            st.rerun()

    selected_id = st.session_state.get("selected_animal_id")
    if selected_id:
        try:
            detail = api_request("GET", f"catalog/animals/{selected_id}/")
            st.divider()
            st.subheader(detail.get("name", text["record"]))
            description = detail.get("description_en") if language_code == "en" else detail.get("description")
            if not description:
                description = detail.get("description", "")
                if language_code == "en" and description:
                    st.caption(text["fallback"])
            st.write(description)
            yes_no = {True: "Sì" if language_code == "it" else "Yes", False: "No", None: "Non valutato" if language_code == "it" else "Unknown"}
            st.markdown("**Comportamento**" if language_code == "it" else "**Behaviour**")
            behavior_columns = st.columns(3)
            behavior_labels = (
                "Con bambini" if language_code == "it" else "With children",
                "Con cani" if language_code == "it" else "With dogs",
                "Con gatti" if language_code == "it" else "With cats",
            )
            behavior_values = (
                yes_no[detail.get("good_with_children")],
                yes_no[detail.get("good_with_dogs")],
                yes_no[detail.get("good_with_cats")],
            )
            for column, label, value in zip(behavior_columns, behavior_labels, behavior_values):
                column.metric(label, value)
            st.caption(
                f"{('Sterilizzato' if language_code == 'it' else 'Neutered')}: {yes_no[detail.get('is_spayed_neutered')]} · "
                f"{('Vaccinato' if language_code == 'it' else 'Vaccinated')}: {yes_no[detail.get('is_vaccinated')]}"
            )
            if detail.get("special_needs_summary"):
                st.info(detail["special_needs_summary"])
            shelter = detail.get("shelter_info") or {}
            st.caption(
                f"{text['shelter']}: {shelter.get('shelter_name', '—')} · "
                f"{shelter.get('city', '')} ({shelter.get('province', '')})"
            )
            for image in detail.get("images", []):
                if image.get("image"):
                    st.image(image["image"], caption=image.get("caption") or detail.get("name"), width="stretch")
            if st.button(text["close"], key="close-animal-detail"):
                del st.session_state.selected_animal_id
                st.rerun()
        except ApiError as exc:
            st.error(str(exc))


def render_matching():
    st.header("Compatibilità con gli animali")
    st.caption("Questo questionario MVP usa regole deterministiche Django. Il portale web ha un motore separato; i punteggi delle due demo non sono direttamente confrontabili.")
    st.info("La compatibilità è calcolata con regole deterministiche. Per i cani mostriamo anche, separatamente e solo a scopo dimostrativo, un rischio di restituzione sperimentale basato su dati sintetici; non è una compatibilità né una previsione affidabile per questa coppia.")
    with st.form("matching-preview-form"):
        preferred_species = st.selectbox("Specie", ["ANY", "DOG", "CAT"], format_func=lambda value: {"ANY": "Cane o gatto", "DOG": "Cane", "CAT": "Gatto"}[value])
        housing_type = st.selectbox("Abitazione", ["APARTMENT_NO_BALCONY", "APARTMENT_BALCONY", "HOUSE_GARDEN", "VILLA_PARK"], format_func=lambda value: {
            "APARTMENT_NO_BALCONY": "Appartamento senza balcone",
            "APARTMENT_BALCONY": "Appartamento con balcone o terrazzo",
            "HOUSE_GARDEN": "Casa con giardino",
            "VILLA_PARK": "Villa o casa con terreno",
        }[value])
        garden_sqm = st.number_input("Spazio verde disponibile (m²)", min_value=0, max_value=10000, value=0, step=5)
        has_children = st.checkbox("In casa ci sono bambini")
        has_dogs = st.checkbox("In casa ci sono già cani")
        has_cats = st.checkbox("In casa ci sono già gatti")
        hours_away_from_home = st.slider("Ore al giorno fuori casa", 0, 24, 4)
        activity_level = st.selectbox("Attività quotidiana", ["SEDENTARY", "MODERATE", "ACTIVE"], format_func=lambda value: {
            "SEDENTARY": "Bassa", "MODERATE": "Moderata", "ACTIVE": "Alta",
        }[value])
        experience_level = st.selectbox("Esperienza con animali", ["BEGINNER", "INTERMEDIATE", "EXPERT"], format_func=lambda value: {
            "BEGINNER": "Prima esperienza", "INTERMEDIATE": "Intermedia", "EXPERT": "Esperta",
        }[value])
        with st.expander("Dati facoltativi per l'indicatore sperimentale sui cani"):
            ml_first_time_owner = st.selectbox("Prima esperienza come proprietario di un cane", [None, 1, 0], format_func=lambda value: {None: "Non specificato", 1: "Sì", 0: "No"}[value])
            ml_home_type = st.selectbox("Situazione abitativa", ["unknown", "apartment", "house_owned", "house_rented"], format_func=lambda value: {
                "unknown": "Non specificata", "apartment": "Appartamento", "house_owned": "Casa di proprietà", "house_rented": "Casa in affitto",
            }[value])
            ml_visits = st.selectbox("Incontri già svolti con il cane", [None, 1, 2, 3, 4], format_func=lambda value: "Non specificato" if value is None else str(value))
            ml_met_resident_pets = st.selectbox("Il cane ha già incontrato gli animali di casa?", [None, 1, 0], format_func=lambda value: {None: "Non specificato", 1: "Sì", 0: "No"}[value])
            ml_adoption_counseling = st.selectbox("Colloquio di preparazione con il rifugio", [None, 1, 0], format_func=lambda value: {None: "Non specificato", 1: "Sì", 0: "No"}[value])
            ml_has_expectations = st.checkbox("Indica la chiarezza delle aspettative iniziali")
            ml_expectation_score = st.slider("Chiarezza delle aspettative (0-10)", 0, 10, 5, disabled=not ml_has_expectations)
        min_age, max_age = st.slider("Età preferita (mesi)", 0, 360, (0, 360), step=6)
        submitted = st.form_submit_button("Calcola compatibilità")

    if submitted:
        answers = {
            "preferred_species": preferred_species,
            "housing_type": housing_type,
            "garden_sqm": garden_sqm,
            "has_children": has_children,
            "has_other_pets": has_dogs or has_cats,
            "has_dogs": has_dogs,
            "has_cats": has_cats,
            "hours_away_from_home": hours_away_from_home,
            "activity_level": activity_level,
            "experience_level": experience_level,
            "preferred_age_min_months": min_age,
            "preferred_age_max_months": max_age,
        }
        ml_answers = {
            "ml_first_time_owner": ml_first_time_owner,
            "ml_home_type": ml_home_type,
            "ml_visits_before_adoption": ml_visits,
            "ml_met_resident_pets": ml_met_resident_pets,
            "ml_adoption_counseling": ml_adoption_counseling,
            "ml_expectation_score": ml_expectation_score if ml_has_expectations else None,
        }
        try:
            st.session_state.matching_preview = preview_matches(answers)
            st.session_state.matching_preview_ml = {}
            for animal in st.session_state.matching_preview.get("results", []):
                if animal.get("species") != "DOG":
                    continue
                try:
                    detail = api_request("GET", f"catalog/animals/{animal['animal_id']}/")
                    features = public_return_risk_features(detail, {**answers, **ml_answers})
                    st.session_state.matching_preview_ml[str(animal["animal_id"])] = score_public_return_risk(features)
                except (ApiError, OSError, ValueError, KeyError) as exc:
                    st.session_state.matching_preview_ml[str(animal["animal_id"])] = {"error": str(exc)}
        except ApiError as exc:
            st.error(str(exc))
            return

    preview = st.session_state.get("matching_preview")
    if not preview:
        return
    st.caption(f"{preview['total']} animali disponibili nella fascia scelta · compatibilità calcolata con regole deterministiche")
    if not preview["results"]:
        st.info("Non ci sono animali compatibili con questi filtri.")
        if preview.get("excluded_total"):
            with st.expander(f"{preview['excluded_total']} animali esclusi per incompatibilità dichiarate"):
                for animal in preview.get("excluded", []):
                    st.write(f"**{animal['name']}**: {', '.join(animal['reasons'])}")
        return

    for animal in preview["results"]:
        with st.container(border=True):
            st.subheader(animal["name"])
            st.caption(f"{animal['species']} · {animal['breed']} · {animal['city']} · {animal['shelter']}")
            st.metric("Compatibilità indicativa (regole)", f"{animal['score']}%")
            if animal.get("species") == "DOG":
                ml_result = (st.session_state.get("matching_preview_ml") or {}).get(str(animal["animal_id"]), {})
                if ml_result.get("error"):
                    st.caption("Rischio di restituzione sperimentale: indicatore non disponibile.")
                elif ml_result:
                    st.metric("Rischio di restituzione sperimentale (modello separato)", f"{ml_result['return_risk_score']:.0%}")
                    st.caption(
                        f"Modello {ml_result['model_version']}, addestrato su dati sintetici. "
                        "L'indicatore non misura la compatibilità e non è una probabilità affidabile per questa coppia. "
                        "Gli input non specificati sono lasciati mancanti; il risultato non decide l'adozione."
                    )
            for caution in animal.get("cautions", []):
                st.warning(caution)
            with st.expander("Dettaglio del punteggio"):
                breakdown = animal.get("breakdown") or {}
                if isinstance(breakdown, dict):
                    for dimension, value in breakdown.items():
                        if isinstance(value, dict):
                            score = value.get("score")
                            contribution = value.get("contribution")
                            st.write(f"**{dimension.replace('_', ' ').capitalize()}**: {score if score is not None else '-'} / 100")
                            if contribution is not None:
                                st.caption(f"Contributo al totale: {contribution:.1f} punti")
                        else:
                            st.write(f"**{dimension.replace('_', ' ').capitalize()}**: {value}")
                else:
                    st.caption("Dettaglio del punteggio non disponibile.")


def render_assistant():
    language = st.selectbox("Lingua / Language", ["Italiano", "English"], key="assistant_language")
    locale = "en" if language == "English" else "it"
    italian = locale == "it"
    engine_labels = {
        "pretrained_model_rag": "Modello linguistico + fonti" if italian else "Language model + sources",
        "retrieval_fallback": "Estratto dalla fonte (modello non configurato o risposta generata non accettata)" if italian else "Source excerpt (model not configured or generated answer rejected)",
        "controlled_source": "Fonte sanitaria controllata; generazione esclusa" if italian else "Controlled health source; generation disabled",
        "safety_guidance": "Indicazione di sicurezza" if italian else "Safety guidance",
        "catalog_lookup": "Ricerca in sola lettura nel catalogo pubblico" if italian else "Read-only public catalogue lookup",
        "no_answer": "Astensione: fonti insufficienti" if italian else "Abstained: insufficient sources",
    }
    st.header("Assistente informativo" if italian else "Information assistant")
    st.caption("Fonti curate, domande di follow-up e ricerca in sola lettura degli animali pubblicati. Nessun dato della conversazione viene salvato sul database." if italian else "Curated sources, follow-up questions, and read-only search of published animals. Conversation data is not saved to the database.")
    with st.expander("Come funziona / How it works"):
        st.markdown("1. Controllo di sicurezza e ambito\n2. Ricerca nel corpus per lingua, specie e pertinenza\n3. Modello opzionale con affermazioni collegate alle fonti, altrimenti estratto della fonte\n4. Astensione quando non esistono fonti sufficienti")
        st.caption("Prova: “Quale negozio vende Royal Canin a Torino?” oppure “Quale cibo per un coniglio?” → il sistema deve astenersi. / Try a local shop or rabbit-food question → the assistant should abstain.")
        st.caption("Dati di negozi, prezzi e disponibilità commerciale non sono collegati: non verranno inventati.")

    if "assistant_history" not in st.session_state:
        st.session_state.assistant_history = []
    history = st.session_state.assistant_history
    for turn_index, item in enumerate(history):
        with st.chat_message(item["role"]):
            reply = item.get("reply")
            if not reply or not reply.get("claims"):
                st.write(item["content"])
            if not reply:
                continue
            for claim in reply.get("claims", []):
                st.write(claim["text"])
                citations = {source["id"]: source for source in reply.get("citations", [])}
                for source_id in claim.get("source_ids", []):
                    source = citations.get(source_id)
                    if source:
                        st.markdown(f'- [{source["organization"]}: {source["title"]}]({source["url"]}) · {source["verified_at"]}')
            if reply.get("catalog_animals"):
                st.markdown("**Schede pubbliche disponibili**" if italian else "**Published profiles available**")
                filters = reply.get("catalog_filters", {})
                labels = []
                if filters.get("species"):
                    labels.append(("cani" if filters["species"] == "dog" else "gatti") if italian else ("dogs" if filters["species"] == "dog" else "cats"))
                if filters.get("city"):
                    labels.append(f'{"città" if italian else "city"}: {filters["city"]}')
                if filters.get("good_with_children"):
                    labels.append("compatibilità esplicita con bambini" if italian else "explicitly assessed child compatibility")
                if labels:
                    st.caption(("Filtri applicati: " if italian else "Applied filters: ") + " · ".join(labels))
                for animal in reply["catalog_animals"]:
                    st.markdown(f'- **{animal["name"]}** · {animal["species"]} · {animal.get("breed", "")} · {animal.get("shelter", "")}, {animal.get("city", "")}')
                    if animal.get("id") and st.button("Apri scheda" if italian else "Open profile", key=f"assistant-animal-{turn_index}-{animal['id']}"):
                        st.session_state.assistant_selected_animal = (turn_index, animal["id"])
                    if st.session_state.get("assistant_selected_animal") == (turn_index, animal.get("id")):
                        try:
                            detail = api_request("GET", f"catalog/animals/{animal['id']}/")
                            st.write(detail.get("description_en") if not italian and detail.get("description_en") else detail.get("description", ""))
                            st.caption(f'{detail.get("name", "")} · {animal.get("shelter", "")}, {animal.get("city", "")}')
                        except ApiError as exc:
                            st.error(str(exc))
                if filters.get("good_with_children"):
                    st.caption("Compatibilità da verificare comunque con il rifugio." if italian else "Confirm compatibility with the shelter before adoption.")
            offers = reply.get("commerce_offers") or []
            if offers:
                st.markdown("**Offerte online verificate**" if italian else "**Verified online offers**")
                for offer in offers:
                    product_name = offer.get("product_name") or ("Prodotto" if italian else "Product")
                    retailer = offer.get("retailer", "")
                    product_url = offer.get("product_url", "")
                    if product_url:
                        st.markdown(f'- [{product_name}]({product_url}) · {retailer}')
                    else:
                        st.write(f"{product_name} · {retailer}")
                    brand = offer.get("brand")
                    price = offer.get("price_amount")
                    currency = offer.get("currency", "EUR")
                    if price:
                        st.write(f"{brand + ' · ' if brand else ''}{price} {currency}")
                    availability = offer.get("availability")
                    scope = offer.get("availability_scope")
                    timestamp_label = "Rilevato" if italian else "Checked"
                    availability_label = (
                        (("Disponibile online" if availability == "available" else "Non disponibile online") if scope == "online" else "Disponibilità non specificata")
                        if italian else
                        (("Available online" if availability == "available" else "Unavailable online") if scope == "online" else "Availability scope unspecified")
                    )
                    st.caption(f"{availability_label} · {timestamp_label}: {offer.get('fetched_at', '')}")
                st.info(
                    "Prezzo e disponibilità si riferiscono alla pagina online del rivenditore; la disponibilità nei negozi fisici non è nota."
                    if italian else
                    "Price and availability refer to the retailer's online page; local store stock is unknown."
                )
            st.caption(engine_labels.get(reply.get("engine"), reply.get("engine", "")))
            with st.expander("Traccia RAG / RAG trace"):
                for step in reply.get("pipeline", []):
                    st.write(f"→ {step}")
                if reply.get("retrieved"):
                    st.caption("Fonti candidate: " + "; ".join(source["title"] for source in reply["retrieved"]))
            st.info(reply.get("disclosure", ""))

    message = st.chat_input("La tua domanda" if italian else "Your question", max_chars=1200)
    if message and message.strip():
        animals = []
        catalog_filters = {}
        if re.search(r"(adott|cerc\w*.{0,24}(cane|gatto|animal)|looking for (a )?(dog|cat|pet)|find me (a )?(dog|cat|pet)|available animals|animali disponibili|schede disponibili)", message, re.IGNORECASE):
            params, catalog_filters = assistant_catalog_filters(message)
            try:
                payload = api_request("GET", "catalog/animals/?" + urlencode(params))
                animals = [
                    {"id": row.get("id"), "name": row.get("name", ""), "species": row.get("species_display", row.get("species", "")), "breed": row.get("breed_name", ""), "city": row.get("city", ""), "shelter": row.get("shelter_name", ""), "slug": "", "description": ""}
                    for row in list_results(payload)[:6]
                ]
            except ApiError as exc:
                st.error(str(exc))
        try:
            reply = chat_request(message.strip(), locale, [{"role": item["role"], "content": item["content"]} for item in history[-8:]], animals, catalog_filters)
            st.session_state.assistant_history.extend([
                {"role": "user", "content": message.strip()},
                {"role": "assistant", "content": reply["answer"], "reply": reply},
            ])
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))
    if st.session_state.get("assistant_history"):
        if st.button("Nuova conversazione / New conversation", key="assistant-clear-history"):
            st.session_state.assistant_history = []
            st.session_state.pop("assistant_selected_animal", None)
            st.rerun()


def render_internal_ml(animals):
    with st.expander("Previsioni ML interne (demo)"):
        st.warning(
            "Solo per il personale del rifugio. Modelli dimostrativi: il rischio di restituzione è addestrato su dati sintetici Kaggle; "
            "la previsione di adozione e la permanenza condizionale usano dati storici di Austin, Texas. "
            "Non usare questi numeri per rifiutare persone o animali."
        )
        if not animals:
            st.info("Pubblica o crea una scheda animale per provare i modelli.")
            return
        labels = {
            str(animal["id"]): f'{animal.get("name", "Animale")} · {animal.get("species", "")}'
            for animal in animals
        }
        selected_id = st.selectbox(
            "Animale da valutare",
            list(labels),
            format_func=lambda animal_id: labels[animal_id],
            key="internal_ml_animal_id",
        )
        animal = next(item for item in animals if str(item["id"]) == selected_id)

        if st.button("Stima esito e permanenza", key="ml-animal-outcome"):
            try:
                st.session_state["ml-animal-outcome-result"] = {
                    "ref": selected_id,
                    "prediction": predict_animal_outcome(animal),
                }
            except ApiError as exc:
                st.error(str(exc))
        outcome_record = st.session_state.get("ml-animal-outcome-result") or {}
        outcome = outcome_record.get("prediction") if outcome_record.get("ref") == selected_id else None
        if outcome:
            st.metric("Adozione tra gli esiti storici osservati", f'{outcome["adoption_probability"]:.0%}')
            st.metric("Permanenza stimata se adottato", f'{outcome["estimated_days_if_adopted"]:.0f} giorni')
            st.caption(
                f'ROC-AUC test adozione: {outcome["test_roc_auc"]:.2f} · MAE permanenza test: {outcome["days_mae_on_test"]:.1f} giorni · '
                f"modello `{outcome['model_version']}`. La durata è condizionale a un'adozione registrata, non una data promessa."
            )

        if animal.get("species") != "DOG":
            st.info("Il modello dimostrativo di rischio restituzione è addestrato solo su cani.")
            return

        st.markdown("**Valuta una coppia adottante–cane**")
        with st.form("internal-compatibility-ml-form"):
            c1, c2, c3 = st.columns(3)
            first_time_owner = c1.checkbox("Prima esperienza con cani")
            household_has_kids = c2.checkbox("In casa ci sono bambini")
            household_has_pets = c3.checkbox("In casa ci sono altri animali")
            home_type = st.selectbox("Abitazione", ["apartment", "house_owned", "house_rented"], format_func=lambda v: {
                "apartment": "Appartamento", "house_owned": "Casa di proprietà", "house_rented": "Casa in affitto",
            }[v])
            c4, c5, c6 = st.columns(3)
            has_yard = c4.checkbox("Giardino")
            hours_alone = c5.slider("Ore solo al giorno", 0, 14, 4)
            activity = c6.slider("Attività dell'adottante", 0, 10, 5)
            c7, c8, c9 = st.columns(3)
            visits = c7.selectbox("Incontri con il cane", [1, 2, 3, 4], index=0)
            met_pets = c8.checkbox("Il cane ha incontrato gli altri animali")
            counseling = c9.checkbox("Colloquio di preparazione svolto")
            c10, c11 = st.columns(2)
            expectations = c10.slider("Aspettative iniziali dichiarate", 0, 10, 6)
            medical_needs = c11.selectbox("Bisogni sanitari", ["none", "minor", "chronic"], format_func=lambda v: {
                "none": "Nessuno", "minor": "Gestibili", "chronic": "Continuativi",
            }[v])
            submitted = st.form_submit_button("Calcola indicatore interno di restituzione")

        size = {"SMALL": "small", "MEDIUM": "medium", "LARGE": "large", "GIANT": "xlarge"}.get(animal.get("size"), "medium")
        energy = {"LOW": 2, "MEDIUM": 5, "HIGH": 8, "VERY_HIGH": 10}.get(animal.get("energy_level"), 5)
        features = {
            "age_years": float(animal.get("age_years", 0)) + float(animal.get("age_months", 0)) / 12,
            "size": size,
            "medical_needs": medical_needs,
            "neutered": int(bool(animal.get("is_spayed_neutered"))),
            "energy_level": energy,
            "first_time_owner": int(first_time_owner),
            "household_has_kids": int(household_has_kids),
            "household_has_pets": int(household_has_pets),
            "home_type": home_type,
            "has_yard": int(has_yard),
            "hours_alone_per_day": hours_alone,
            "adopter_activity_level": activity,
            "visits_before_adoption": visits,
            "met_resident_pets": int(met_pets),
            "adoption_counseling": int(counseling),
            "expectation_score": expectations,
        }
        if submitted:
            try:
                st.session_state["ml-pair-return-result"] = {
                    "ref": selected_id,
                    "features": features,
                    "prediction": ml_request("predict/compatibility", selected_id, features),
                }
            except ApiError as exc:
                st.error(str(exc))
        pair_record = st.session_state.get("ml-pair-return-result") or {}
        pair_result = pair_record.get("prediction") if pair_record.get("ref") == selected_id and pair_record.get("features") == features else None
        if pair_result:
            st.metric("Indicatore sintetico di restituzione", f'{pair_result["return_risk_score"]:.0%}')
            st.caption(
                f'Modello `{pair_result["model_version"]}` · target: restituzione dopo l’adozione. '
                "È un punteggio non calibrato su dati sintetici, non una probabilità affidabile per questa coppia. "
                "Usalo solo per discutere eventuale supporto aggiuntivo con il rifugio."
            )


def home_visit_payload(evaluator_name, visit_date, visit_time, report_notes=""):
    scheduled = datetime.combine(visit_date, visit_time, tzinfo=ZoneInfo(os.getenv("APP_TIME_ZONE", "Europe/Rome")))
    return {
        "evaluator_name": evaluator_name.strip(),
        "scheduled_date": scheduled.isoformat(),
        "report_notes": report_notes.strip(),
    }


def _application_status_label(value):
    return {
        "SUBMITTED": "Inviata",
        "IN_REVIEW": "In valutazione",
        "HOME_VISIT": "Visita pre-affido programmata",
        "APPROVED": "Approvata",
        "REJECTED": "Rifiutata",
        "WITHDRAWN": "Ritirata",
    }.get(value, value or "Stato non disponibile")


def render_application_portal():
    st.header("Candidature di adozione")
    adopter_token = st.session_state.get("adopter_access_token")
    shelter_token = st.session_state.get("shelter_access_token")
    token = shelter_token or adopter_token
    profile = None

    if token:
        try:
            profile = api_request("GET", "users/me/", token=token)
        except ApiError as exc:
            st.error(f"Sessione scaduta: {exc}")
            st.session_state.pop("adopter_access_token", None)
            st.session_state.pop("shelter_access_token", None)
            return

    if not profile:
        mode = st.radio("Account", ["Accedi", "Crea account adottante"], horizontal=True, key="application-auth-mode")
        if mode == "Accedi":
            with st.form("adopter-login"):
                username = st.text_input("Nome utente")
                password = st.text_input("Password", type="password")
                login = st.form_submit_button("Accedi")
            if login:
                try:
                    result = api_request("POST", "users/auth/login/", json={"username": username, "password": password})
                    account = api_request("GET", "users/me/", token=result["access"])
                    if account.get("role") != "ADOPTER":
                        st.error("Questo spazio è per gli adottanti. I rifugi possono accedere dalla scheda Rifugi.")
                    else:
                        st.session_state.adopter_access_token = result["access"]
                        st.rerun()
                except (ApiError, KeyError) as exc:
                    st.error(str(exc) or "Credenziali non valide.")
        else:
            with st.form("adopter-registration", clear_on_submit=True):
                username = st.text_input("Nome utente *")
                email = st.text_input("Email *")
                first_name = st.text_input("Nome")
                last_name = st.text_input("Cognome")
                password = st.text_input("Password (almeno 8 caratteri) *", type="password")
                password_confirm = st.text_input("Conferma password *", type="password")
                gdpr_consent = st.checkbox("Accetto l'informativa privacy *")
                register = st.form_submit_button("Crea account")
            if register:
                if password != password_confirm:
                    st.error("Le password non coincidono.")
                elif not gdpr_consent:
                    st.error("Il consenso privacy è obbligatorio.")
                else:
                    try:
                        api_request("POST", "users/auth/register/", json={
                            "username": username.strip(),
                            "email": email.strip(),
                            "first_name": first_name.strip(),
                            "last_name": last_name.strip(),
                            "password": password,
                            "password_confirm": password_confirm,
                            "role": "ADOPTER",
                            "gdpr_consent": True,
                            "marketing_consent": False,
                        })
                        st.success("Account creato. Accedi per inviare e seguire le candidature.")
                    except ApiError as exc:
                        st.error(f"Registrazione non completata: {exc}")
        st.info("I rifugi accedono dalla scheda Rifugi; da lì possono gestire le candidature ricevute.")
        return

    role = profile.get("role")
    token_key = "shelter_access_token" if role == "SHELTER" else "adopter_access_token"
    if role not in ("ADOPTER", "SHELTER"):
        st.error("Il ruolo di questo account non può gestire candidature.")
        return
    top = st.columns([5, 1])
    top[0].write("Area adottante" if role == "ADOPTER" else "Candidature ricevute dal rifugio")
    if top[1].button("Esci", key="application-logout"):
        st.session_state.pop(token_key, None)
        st.rerun()

    if role == "ADOPTER":
        st.subheader("Invia una candidatura")
        try:
            animals = list_results(api_request("GET", "catalog/animals/?page_size=48"))
        except ApiError as exc:
            st.error(f"Catalogo non disponibile: {exc}")
            animals = []
        if animals:
            animal_ids = [item["id"] for item in animals]
            labels = {
                item["id"]: f"{item['name']} · {item.get('species_display', item.get('species', ''))} · {item.get('shelter_name', '')}, {item.get('city', '')}"
                for item in animals
            }
            with st.form("adoption-application-form"):
                animal_id = st.selectbox("Animale", animal_ids, format_func=lambda value: labels[value])
                motivation = st.text_area("Perché vorresti adottarlo? (almeno 50 caratteri)", max_chars=5000)
                submit_application = st.form_submit_button("Invia candidatura")
            if submit_application:
                if len(motivation.strip()) < 50:
                    st.error("Aggiungi almeno 50 caratteri per spiegare le tue motivazioni.")
                else:
                    try:
                        api_request("POST", f"animals/{animal_id}/apply/", token=token, json={"motivational_notes": motivation.strip()})
                        st.success("Candidatura inviata.")
                    except ApiError as exc:
                        st.error(f"Invio non riuscito: {exc}")
        else:
            st.info("Non ci sono animali disponibili nel catalogo.")

        st.subheader("Le tue candidature")
        try:
            applications = list_results(api_request("GET", "user/applications/", token=token))
        except ApiError as exc:
            st.error(f"Candidature non disponibili: {exc}")
            applications = []
        if not applications:
            st.info("Non hai ancora inviato candidature.")
        else:
            labels = {
                item["id"]: f"{(item.get('animal_detail') or {}).get('name', 'Animale')} · {_application_status_label(item.get('status_display') or item.get('status'))}"
                for item in applications
            }
            application_id = st.selectbox("Dettaglio candidatura", [item["id"] for item in applications], format_func=lambda value: labels[value])
            try:
                detail = api_request("GET", f"user/applications/{application_id}/", token=token)
                st.write(f"**Stato:** {_application_status_label(detail.get('status_display') or detail.get('status'))}")
                if detail.get("shelter_notes"):
                    st.write(f"**Messaggio del rifugio:** {detail['shelter_notes']}")
                visit = detail.get("home_visit")
                if visit:
                    st.write(f"**Visita pre-affido:** {visit.get('scheduled_date', 'Data da concordare')} · {visit.get('evaluator_name', '')}")
                    if visit.get("outcome"):
                        st.caption(f"Esito: {visit['outcome']}")
                    if visit.get("report_notes"):
                        st.write(visit["report_notes"])
                else:
                    st.caption("Non è ancora stata programmata una visita pre-affido.")
                contact = detail.get("shelter_contact") or {}
                if contact:
                    st.caption(f"Contatto rifugio: {contact.get('shelter_name', '')} · {contact.get('official_email', '')} · {contact.get('phone_number', '')}")
            except ApiError as exc:
                st.error(f"Dettaglio non disponibile: {exc}")
        return

    st.subheader("Candidature ricevute")
    try:
        applications = list_results(api_request("GET", "shelter/applications/", token=token))
    except ApiError as exc:
        st.error(f"Candidature non disponibili: {exc}")
        return
    if not applications:
        st.info("Non hai ancora ricevuto candidature.")
        return
    statuses = ["SUBMITTED", "IN_REVIEW", "HOME_VISIT", "APPROVED", "REJECTED", "WITHDRAWN"]
    for application in applications:
        animal = application.get("animal_detail") or {}
        adopter = application.get("adopter_detail") or {}
        title = f"{animal.get('name', 'Animale')} · {adopter.get('first_name') or adopter.get('username', 'Adottante')} · {_application_status_label(application.get('status'))}"
        with st.expander(title):
            st.write(application.get("motivational_notes", ""))
            st.caption(f"{adopter.get('email', '')} · candidatura #{application['id']}")
            visit = application.get("home_visit")
            if visit:
                st.write(f"Visita: {visit.get('scheduled_date', '')} · {visit.get('evaluator_name', '')}")
            with st.form(f"application-status-{application['id']}"):
                current_status = application.get("status") if application.get("status") in statuses else "SUBMITTED"
                new_status = st.selectbox("Stato", statuses, index=statuses.index(current_status), format_func=_application_status_label)
                shelter_notes = st.text_area("Nota per il team", value=application.get("shelter_notes", ""), key=f"application-notes-{application['id']}")
                update = st.form_submit_button("Salva stato")
            if update:
                try:
                    api_request("PATCH", f"shelter/applications/{application['id']}/", token=token, json={"status": new_status, "shelter_notes": shelter_notes})
                    st.success("Candidatura aggiornata.")
                    st.rerun()
                except ApiError as exc:
                    st.error(f"Aggiornamento non riuscito: {exc}")
            with st.form(f"schedule-visit-{application['id']}"):
                evaluator = st.text_input("Referente visita", key=f"visit-evaluator-{application['id']}")
                visit_date = st.date_input("Data visita", value=date.today(), key=f"visit-date-{application['id']}")
                visit_time = st.time_input("Ora visita", value=time(17, 0), key=f"visit-time-{application['id']}")
                visit_notes = st.text_area("Note per la visita", key=f"visit-notes-{application['id']}")
                schedule = st.form_submit_button("Programma visita pre-affido")
            if schedule:
                if not evaluator.strip():
                    st.error("Indica il referente della visita.")
                else:
                    try:
                        api_request("POST", f"shelter/applications/{application['id']}/schedule-visit/", token=token, json=home_visit_payload(evaluator, visit_date, visit_time, visit_notes))
                        st.success("Visita programmata.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(f"Programmazione non riuscita: {exc}")


def render_shelter():
    st.header("Area rifugio")
    token = st.session_state.get("shelter_access_token")
    if not token:
        with st.form("shelter_login"):
            username = st.text_input("Nome utente")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Accedi")
        if submitted:
            try:
                result = api_request("POST", "users/auth/login/", json={"username": username, "password": password})
                profile = api_request("GET", "users/me/", token=result["access"])
                if profile.get("role") != "SHELTER":
                    st.error("L'area rifugio e le stime ML sono riservate agli account rifugio.")
                else:
                    st.session_state.shelter_access_token = result["access"]
                    st.rerun()
            except (ApiError, KeyError) as exc:
                st.error(str(exc) or "Credenziali non valide.")

        with st.expander("Registra un nuovo rifugio"):
            comune_query = st.text_input("Cerca comune del rifugio *", key="registration-comune-query")
            try:
                registration_comuni = comune_options(comune_query)
            except ApiError as exc:
                st.error(str(exc))
                registration_comuni = []
            registration_labels = {
                item["istat_code"]: f'{item["name"]} ({item["province_abbreviation"]})'
                for item in registration_comuni
            }
            registration_codes = [item["istat_code"] for item in registration_comuni]
            if st.session_state.get("registration-comune") not in registration_codes:
                st.session_state["registration-comune"] = ""
            with st.form("shelter_registration", clear_on_submit=True):
                username = st.text_input("Nome utente per accesso *", key="registration-username")
                account_email = st.text_input("Email account *", key="registration-email")
                password = st.text_input("Password *", type="password", key="registration-password")
                password_confirm = st.text_input("Conferma password *", type="password", key="registration-password-confirm")
                shelter_name = st.text_input("Nome pubblico rifugio *")
                legal_name = st.text_input("Ragione sociale *")
                organization_types = {
                    "Canile comunale": "MUNICIPAL_SHELTER",
                    "Canile privato": "PRIVATE_SHELTER",
                    "Gattile": "CATTERY",
                    "Associazione": "ASSOCIATION",
                    "Rifugio": "RESCUE",
                }
                organization_label = st.selectbox("Tipo struttura *", list(organization_types))
                tax_code_vat = st.text_input("Codice fiscale / Partita IVA *")
                official_email = st.text_input("Email di contatto *")
                address = st.text_input("Indirizzo *")
                c1, c2, c3 = st.columns(3)
                comune = c1.selectbox(
                    "Comune *", ["", *registration_codes],
                    format_func=lambda code: registration_labels.get(code, "Seleziona un comune"),
                    key="registration-comune",
                )
                c2.write("Provincia ricavata automaticamente")
                postal_code = c3.text_input("CAP *", max_chars=10)
                phone_number = st.text_input("Telefono *")
                description = st.text_area("Descrizione pubblica *")
                gdpr_consent = st.checkbox("Accetto l'informativa privacy *")
                register = st.form_submit_button("Invia richiesta")

            if register:
                if not comune:
                    st.error("Seleziona il comune del rifugio.")
                elif password != password_confirm:
                    st.error("Le password non coincidono.")
                elif not gdpr_consent:
                    st.error("Il consenso privacy è obbligatorio.")
                else:
                    payload = {
                        "username": username.strip(),
                        "email": account_email.strip(),
                        "password": password,
                        "password_confirm": password_confirm,
                        "role": "SHELTER",
                        "gdpr_consent": True,
                        "shelter_name": shelter_name.strip(),
                        "legal_name": legal_name.strip(),
                        "organization_type": organization_types[organization_label],
                        "tax_code_vat": tax_code_vat.strip(),
                        "official_email": official_email.strip(),
                        "address": address.strip(),
                        "comune": comune,
                        "postal_code": postal_code.strip(),
                        "phone_number": phone_number.strip(),
                        "description": description.strip(),
                    }
                    try:
                        api_request("POST", "users/auth/register/", json=payload)
                        st.success("Richiesta inviata. Puoi accedere e creare bozze; la pubblicazione si attiva dopo l'approvazione.")
                    except ApiError as exc:
                        st.error(f"Registrazione non completata: {exc}")
        return

    top = st.columns([5, 1])
    top[0].write("Sessione rifugio autenticata")
    if top[1].button("Esci"):
        del st.session_state.shelter_access_token
        st.session_state.pop("ml-animal-outcome-result", None)
        st.session_state.pop("ml-pair-return-result", None)
        st.rerun()

    try:
        stats = api_request("GET", "shelter/dashboard/stats/", token=token)
        animal_stats = stats["animals_summary"]
        application_stats = stats["applications_summary"]
        st.subheader("Riepilogo rifugio")
        for column, label, value in zip(
            st.columns(4),
            ("Animali", "Disponibili", "Candidature da valutare", "Visite programmate"),
            (animal_stats["total"], animal_stats["available"], application_stats["pending_evaluation"], application_stats["home_visits_scheduled"]),
        ):
            column.metric(label, value)
    except (ApiError, KeyError) as exc:
        st.warning(f"Riepilogo non disponibile: {exc}")

    st.subheader("Inserisci un animale")
    with st.form("new_animal", clear_on_submit=True):
        name = st.text_input("Nome *")
        c1, c2, c3 = st.columns(3)
        species = c1.selectbox("Specie *", ["DOG", "CAT"], format_func=lambda value: "Cane" if value == "DOG" else "Gatto")
        gender = c2.selectbox("Sesso *", ["F", "M"], format_func=lambda value: "Femmina" if value == "F" else "Maschio")
        size = c3.selectbox("Taglia", ["SMALL", "MEDIUM", "LARGE", "GIANT"], index=1)
        c4, c5, c6 = st.columns(3)
        age_years = c4.number_input("Età (anni)", min_value=0, max_value=40, value=0)
        age_months = c5.number_input("Età (mesi)", min_value=0, max_value=11, value=0)
        energy = c6.selectbox("Energia", ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"], index=1)
        description = st.text_area("Descrizione *", max_chars=5000)
        description_en = st.text_area("Descrizione in inglese (facoltativa)", max_chars=5000)
        compatibility = {"Non valutato": None, "Sì": True, "No": False}
        st.markdown("**Comportamento** — indica anche “Non valutato” se non conosci ancora la risposta.")
        c7, c8, c9 = st.columns(3)
        good_with_children = c7.selectbox("Compatibile con bambini *", list(compatibility))
        good_with_dogs = c8.selectbox("Compatibile con cani *", list(compatibility))
        good_with_cats = c9.selectbox("Compatibile con gatti *", list(compatibility))
        c10, c11 = st.columns(2)
        is_spayed_neutered = c10.selectbox("Sterilizzazione *", ["Seleziona", "Sì", "No"])
        is_vaccinated = c11.selectbox("Vaccinazioni", ["Non noto", "Sì", "No"])
        special_needs = st.checkbox("Ha bisogni speciali o cure continuative")
        special_needs_summary = st.text_input("Sintesi pubblica dei bisogni speciali (se applicabile)", max_chars=255)
        health_notes = st.text_area("Note sanitarie riservate al rifugio", max_chars=5000)
        intake_date = st.date_input("Ingresso in rifugio *")
        photos = st.file_uploader(
            "Foto * (almeno una, JPG/PNG/WebP, max 5 MB ciascuna)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )
        photo_alt_texts = [
            st.text_input(f"Descrizione accessibile: {photo.name} *", max_chars=150, key=f"new-animal-alt-{index}-{photo.name}")
            for index, photo in enumerate(photos or [])
        ]
        submitted = st.form_submit_button("Crea bozza e pubblica")

    if submitted:
        if not name.strip() or not description.strip():
            st.error("Nome e descrizione sono obbligatori.")
        elif is_spayed_neutered == "Seleziona":
            st.error("Indica lo stato di sterilizzazione prima di pubblicare.")
        elif special_needs and not special_needs_summary.strip():
            st.error("Aggiungi una breve sintesi pubblica dei bisogni speciali.")
        elif not photos:
            st.error("Carica almeno una foto prima di pubblicare.")
        elif any(not alt_text.strip() for alt_text in photo_alt_texts):
            st.error("Aggiungi una descrizione accessibile per ogni foto.")
        elif any(photo.size > MAX_IMAGE_SIZE for photo in photos):
            st.error("Ogni foto deve essere al massimo di 5 MB.")
        else:
            animal = {
                "name": name.strip(),
                "species": species,
                "gender": gender,
                "size": size,
                "energy_level": energy,
                "age_years": int(age_years),
                "age_months": int(age_months),
                "description": description.strip(),
                "description_en": description_en.strip(),
                "good_with_children": compatibility[good_with_children],
                "good_with_dogs": compatibility[good_with_dogs],
                "good_with_cats": compatibility[good_with_cats],
                "behavior_profile_completed": True,
                "is_spayed_neutered": {"Sì": True, "No": False}[is_spayed_neutered],
                "is_vaccinated": {"Non noto": None, "Sì": True, "No": False}[is_vaccinated],
                "special_needs": special_needs,
                "special_needs_summary": special_needs_summary.strip(),
                "health_notes": health_notes.strip(),
                "date_entry_shelter": intake_date.isoformat(),
            }
            try:
                draft = api_request("POST", "shelter/animals/", token=token, json=animal)
                upload_images(draft["id"], photos, photo_alt_texts, token)
                publish_animal(draft["id"], token)
                st.success(f"{name} è stato pubblicato nel catalogo.")
                st.rerun()
            except (ApiError, KeyError) as exc:
                st.error(f"Pubblicazione non completata: {exc}")
                st.info("Se la bozza è stata creata, la trovi qui sotto e puoi completare il caricamento.")

    st.subheader("I tuoi animali")
    try:
        animals = list_results(api_request("GET", "shelter/animals/", token=token))
    except ApiError as exc:
        st.error(str(exc))
        return

    if not animals:
        st.info("Non hai ancora inserito animali.")
    for animal in animals:
        animal_id = animal["id"]
        title = f"{animal.get('name', 'Animale')} · {animal.get('status', '')}"
        with st.expander(title):
            for image in animal.get("images", []):
                if image.get("image"):
                    st.image(image["image"], caption=image.get("caption") or animal.get("name"), width=180)
            if animal.get("status") == "DRAFT":
                photos = st.file_uploader(
                    "Aggiungi foto alla bozza (max 5 MB ciascuna)",
                    type=["jpg", "jpeg", "png", "webp"],
                    accept_multiple_files=True,
                    key=f"draft-photos-{animal_id}",
                )
                draft_alt_texts = [
                    st.text_input(
                        f"Descrizione accessibile: {photo.name} *",
                        max_chars=150,
                        key=f"draft-alt-{animal_id}-{index}-{photo.name}",
                    )
                    for index, photo in enumerate(photos or [])
                ]
                if photos and st.button("Carica foto", key=f"upload-{animal_id}"):
                    try:
                        upload_images(animal_id, photos, draft_alt_texts, token)
                        st.success("Foto caricate.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))
                if animal.get("images") and st.button("Pubblica", key=f"publish-{animal_id}"):
                    try:
                        publish_animal(animal_id, token)
                        st.success("Animale pubblicato.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))

    render_internal_ml(animals)


def main():
    st.set_page_config(page_title="PetMatch AI", page_icon="🐾", layout="wide")
    st.title("PetMatch AI 🐾")
    st.caption("Animali dei rifugi, pronti a incontrare una famiglia.")
    catalog_tab, matching_tab, applications_tab, assistant_tab, shelter_tab = st.tabs(["Catalogo", "Compatibilità", "Candidature", "Assistente", "Rifugi"])
    with catalog_tab:
        render_catalog()
    with matching_tab:
        render_matching()
    with applications_tab:
        render_application_portal()
    with assistant_tab:
        render_assistant()
    with shelter_tab:
        render_shelter()


if __name__ == "__main__":
    main()
