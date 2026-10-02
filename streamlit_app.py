import json
import os
from urllib.parse import urlencode

import requests
import streamlit as st

API_BASE = os.getenv("PET_MATCH_API_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = 20


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


def upload_images(animal_id, uploaded_files, token):
    files = [
        ("images", (file.name, file.getvalue(), file.type or "application/octet-stream"))
        for file in uploaded_files
    ]
    return api_request(
        "POST",
        f"animals/{animal_id}/images/upload/",
        token=token,
        files=files,
    )


def publish_animal(animal_id, token):
    return api_request(
        "POST",
        f"shelter/animals/{animal_id}/publish/",
        token=token,
    )


def render_catalog():
    st.header("Animali in cerca di casa")
    with st.form("catalog_filters"):
        search = st.text_input("Cerca per nome, razza o rifugio")
        c1, c2, c3 = st.columns(3)
        species = c1.selectbox("Specie", ["Tutte", "DOG", "CAT"])
        city = c2.text_input("Città")
        gender = c3.selectbox("Sesso", ["Tutti", "M", "F"])
        submitted = st.form_submit_button("Cerca")

    if "catalog_filters" not in st.session_state:
        st.session_state.catalog_filters = {"search": "", "species": "", "city": "", "gender": ""}
    if "catalog_page" not in st.session_state:
        st.session_state.catalog_page = 1
    if submitted:
        st.session_state.catalog_page = 1
        st.session_state.catalog_filters = {
            "search": search.strip(),
            "species": "" if species == "Tutte" else species,
            "city": city.strip(),
            "gender": "" if gender == "Tutti" else gender,
        }

    params = {key: value for key, value in st.session_state.catalog_filters.items() if value}
    params["page"] = st.session_state.catalog_page
    query = urlencode(params)
    try:
        payload = api_request("GET", "catalog/animals/" + (f"?{query}" if query else ""))
    except ApiError as exc:
        st.error(str(exc))
        return

    animals = list_results(payload)
    if not animals:
        st.info("Nessun animale corrisponde ai filtri. Prova a cambiarli.")
        return

    for offset in range(0, len(animals), 3):
        columns = st.columns(3)
        for column, animal in zip(columns, animals[offset:offset + 3]):
            with column:
                if animal.get("primary_image"):
                    st.image(animal["primary_image"], use_container_width=True)
                st.subheader(animal.get("name", "Animale"))
                st.caption(
                    f"{animal.get('species_display', animal.get('species', ''))} · "
                    f"{animal.get('breed_name', 'Meticcio')} · "
                    f"{animal.get('city', '')}"
                )
                st.write(f"Età: {animal.get('age_years', 0)} anni e {animal.get('age_months', 0)} mesi")
                if st.button("Dettagli", key=f"animal-{animal['id']}"):
                    st.session_state.selected_animal_id = animal["id"]

    if isinstance(payload, dict) and (payload.get("previous") or payload.get("next")):
        previous, summary, following = st.columns([1, 4, 1])
        page = st.session_state.catalog_page
        total_pages = max(1, (payload.get("count", len(animals)) + 11) // 12)
        summary.write(f"Pagina {page} di {total_pages}")
        if payload.get("previous") and previous.button("Precedenti"):
            st.session_state.catalog_page -= 1
            st.rerun()
        if payload.get("next") and following.button("Successivi"):
            st.session_state.catalog_page += 1
            st.rerun()

    selected_id = st.session_state.get("selected_animal_id")
    if selected_id:
        try:
            detail = api_request("GET", f"catalog/animals/{selected_id}/")
            st.divider()
            st.subheader(detail.get("name", "Scheda animale"))
            st.write(detail.get("description", ""))
            shelter = detail.get("shelter_info") or {}
            st.caption(
                f"Rifugio: {shelter.get('shelter_name', '—')} · "
                f"{shelter.get('city', '')} ({shelter.get('province', '')})"
            )
            if detail.get("images"):
                st.image([image["image"] for image in detail["images"] if image.get("image")], use_container_width=True)
            if st.button("Chiudi scheda", key="close-animal-detail"):
                del st.session_state.selected_animal_id
                st.rerun()
        except ApiError as exc:
            st.error(str(exc))


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
                st.session_state.shelter_access_token = result["access"]
                st.rerun()
            except (ApiError, KeyError) as exc:
                st.error(str(exc) or "Credenziali non valide.")
        return

    top = st.columns([5, 1])
    top[0].write("Sessione rifugio autenticata")
    if top[1].button("Esci"):
        del st.session_state.shelter_access_token
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
        intake_date = st.date_input("Ingresso in rifugio *")
        photos = st.file_uploader(
            "Foto * (almeno una, JPG/PNG/WebP, max 5 MB ciascuna)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )
        submitted = st.form_submit_button("Crea bozza e pubblica")

    if submitted:
        if not name.strip() or not description.strip():
            st.error("Nome e descrizione sono obbligatori.")
        elif not photos:
            st.error("Carica almeno una foto prima di pubblicare.")
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
                "date_entry_shelter": intake_date.isoformat(),
            }
            try:
                draft = api_request("POST", "shelter/animals/", token=token, json=animal)
                upload_images(draft["id"], photos, token)
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
            if animal.get("images"):
                st.image([image["image"] for image in animal["images"] if image.get("image")], width=180)
            if animal.get("status") == "DRAFT":
                photos = st.file_uploader(
                    "Aggiungi foto alla bozza",
                    type=["jpg", "jpeg", "png", "webp"],
                    accept_multiple_files=True,
                    key=f"draft-photos-{animal_id}",
                )
                if photos and st.button("Carica foto", key=f"upload-{animal_id}"):
                    try:
                        upload_images(animal_id, photos, token)
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


def main():
    st.set_page_config(page_title="PetMatch AI", page_icon="🐾", layout="wide")
    st.title("PetMatch AI 🐾")
    st.caption("Animali dei rifugi, pronti a incontrare una famiglia.")
    catalog_tab, shelter_tab = st.tabs(["Catalogo", "Rifugi"])
    with catalog_tab:
        render_catalog()
    with shelter_tab:
        render_shelter()


if __name__ == "__main__":
    main()
