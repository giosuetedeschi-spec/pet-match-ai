import json
import os
import re
from datetime import date
from urllib.parse import urlencode

import requests
import streamlit as st
import pandas as pd

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
    denies_children = bool(re.search(r"\b(non|not|without|no)\b.{0,28}\b(adatt\w*|compatibil\w*|good|suitable|safe)\b.{0,24}\b(bambin\w*|bimbi|children|kids)\b", text, re.IGNORECASE))
    if asks_for_children and not denies_children:
        filters["good_with_children"] = True
        params["good_with_children"] = "true"
    city_matches = re.finditer(r"\b(?:vicino\s+a|near|around|in|a)\s+([\wÀ-ÿ'’-]+(?:\s+[\wÀ-ÿ'’-]+){0,3}?)(?=\s+(?:adatt\w*|con\b|per\b|ai?\b|bambin\w*|children\b|kids\b|with\b|good\b|suitable\b|for\b|in\b|near\b|around\b|and\b|or\b)|[,;.!?]|$)", text, re.IGNORECASE)
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
    st.info("PetMatch usa modelli ML solo per supportare il lavoro interno dei rifugi. Le relative stime non vengono mostrate a chi adotta e non decidono l'accesso a un'adozione.")
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
        try:
            st.session_state.matching_preview = preview_matches(answers)
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
            with st.expander(f'{preview["excluded_total"]} animali esclusi per incompatibilità dichiarate'):
                for animal in preview.get("excluded", []):
                    st.write(f'**{animal["name"]}**: {", ".join(animal["reasons"])}')
        return

    for animal in preview["results"]:
        with st.container(border=True):
            st.subheader(animal["name"])
            st.caption(f"{animal['species']} · {animal['breed']} · {animal['city']} · {animal['shelter']}")
            st.metric("Compatibilità indicativa (regole)", f"{animal['score']}%")
            for caution in animal.get("cautions", []):
                st.warning(caution)
            with st.expander("Dettaglio del punteggio"):
                breakdown = animal.get("breakdown") or {}
                if isinstance(breakdown, dict):
                    for dimension, value in breakdown.items():
                        if isinstance(value, dict):
                            score = value.get("score")
                            contribution = value.get("contribution")
                            st.write(f"**{dimension.replace('_', ' ').capitalize()}**: {score if score is not None else '—'}/100")
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
    for item in history:
        with st.chat_message(item["role"]):
            st.write(item["content"])
            reply = item.get("reply")
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
                if filters.get("good_with_children"):
                    st.caption("Compatibilità da verificare comunque con il rifugio." if italian else "Confirm compatibility with the shelter before adoption.")
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
                    {"name": row.get("name", ""), "species": row.get("species_display", row.get("species", "")), "breed": row.get("breed_name", ""), "city": row.get("city", ""), "shelter": row.get("shelter_name", ""), "slug": "", "description": ""}
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
    catalog_tab, matching_tab, assistant_tab, shelter_tab = st.tabs(["Catalogo", "Compatibilità", "Assistente", "Rifugi"])
    with catalog_tab:
        render_catalog()
    with matching_tab:
        render_matching()
    with assistant_tab:
        render_assistant()
    with shelter_tab:
        render_shelter()


if __name__ == "__main__":
    main()
