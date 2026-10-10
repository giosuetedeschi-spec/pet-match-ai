"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type ShelterChoice = { id: string; name: string; status: "pending" | "active" | "suspended" | "archived" };
type PhotoEntry = { file: File; altTextIt: string; altTextEn: string };
type ManagedPhoto = { id: string; altTextIt: string | null; altTextEn: string | null; isPrimary: boolean; sortOrder: number };
type InitialAnimal = { id: string; shelterId: string; fields: Record<string, string>; behavior: Record<string, string>; photos: ManagedPhoto[] };

const labels: Record<string, string> = {
  dog: "Cane", cat: "Gatto", male: "Maschio", female: "Femmina", unknown: "Non noto",
  small: "Piccola", medium: "Media", large: "Grande", xlarge: "Molto grande",
  yes: "Sì", no: "No", selective: "Selettivo", older_only: "Solo con bambini più grandi",
  partially: "In parte", preferred: "Preferibile", apartment: "Appartamento", house_no_garden: "Casa senza giardino",
  house_with_garden: "Casa con giardino", farm: "Casa con terreno",
};

function select(name: string, title: string, values: string[], required = false, defaultValue = "") {
  return <label>{title}<select name={name} defaultValue={defaultValue} required={required}><option value="" disabled>Seleziona</option>{values.map((value) => <option key={value} value={value}>{labels[value] ?? value}</option>)}</select></label>;
}

export default function AnimalForm({ shelters, initial, published = false }: { shelters: ShelterChoice[]; initial?: InitialAnimal; published?: boolean }) {
  const router = useRouter();
  const [shelterId, setShelterId] = useState(initial?.shelterId ?? shelters[0]?.id ?? "");
  const [photos, setPhotos] = useState<PhotoEntry[]>([]);
  const [existingPhotos, setExistingPhotos] = useState<ManagedPhoto[]>(initial?.photos ?? []);
  const [photoBusy, setPhotoBusy] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [savedId, setSavedId] = useState(initial?.id ?? "");

  function changeFiles(files: FileList | null) {
    setPhotos(Array.from(files ?? []).slice(0, Math.max(0, 10 - existingPhotos.length)).map((file) => ({ file, altTextIt: "", altTextEn: "" })));
  }

  function setAlt(index: number, language: "altTextIt" | "altTextEn", value: string) {
    setPhotos((current) => current.map((photo, photoIndex) => photoIndex === index ? { ...photo, [language]: value } : photo));
  }

  function setExistingAlt(id: string, language: "altTextIt" | "altTextEn", value: string) {
    setExistingPhotos((current) => current.map((photo) => photo.id === id ? { ...photo, [language]: value } : photo));
  }

  async function managePhoto(id: string, operation: { altTextIt?: string; altTextEn?: string; move?: "up" | "down"; makePrimary?: true } | "delete") {
    if (operation === "delete" && !window.confirm("Rimuovere questa foto dalla scheda? L'oggetto resta archiviato e non sarà più visibile.")) return;
    setPhotoBusy(id); setError(""); setMessage("");
    try {
      const response = await fetch(`/api/shelter/animals/${savedId}/media/${id}`, {
        method: operation === "delete" ? "DELETE" : "PATCH",
        ...(operation === "delete" ? {} : { headers: { "Content-Type": "application/json" }, body: JSON.stringify(operation) }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Aggiornamento foto non riuscito.");
      setExistingPhotos(result.photos as ManagedPhoto[]);
      setMessage("Foto aggiornate.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Richiesta non riuscita.");
    } finally { setPhotoBusy(""); }
  }

  async function uploadSelectedPhotos(animalId: string) {
    for (const photo of [...photos]) {
      const photoForm = new FormData();
      photoForm.set("file", photo.file);
      photoForm.set("altTextIt", photo.altTextIt);
      photoForm.set("altTextEn", photo.altTextEn);
      const uploaded = await fetch(`/api/shelter/animals/${animalId}/media`, { method: "POST", body: photoForm });
      const uploadResult = await uploaded.json();
      if (!uploaded.ok) throw new Error(uploadResult.error || `Upload non riuscito per ${photo.file.name}.`);
      setExistingPhotos((current) => [...current, uploadResult.media as ManagedPhoto]);
      setPhotos((current) => current.filter((pending) => pending !== photo));
    }
  }

  async function uploadPublishedPhotos() {
    if (!savedId || !photos.length) return;
    setBusy(true); setError(""); setMessage("");
    try {
      await uploadSelectedPhotos(savedId);
      setMessage("Foto caricate.");
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Caricamento non riuscito.");
    } finally { setBusy(false); }
  }

  async function submit(event: FormEvent<HTMLFormElement>, publish = false) {
    event.preventDefault();
    setBusy(true); setError(""); setMessage("");
    try {
      const form = new FormData(event.currentTarget);
      const behavior: Record<string, FormDataEntryValue> = {};
      for (const [name, value] of form.entries()) if (name.startsWith("behavior.")) behavior[name.slice("behavior.".length)] = value;
      const body = Object.fromEntries([...form.entries()].filter(([name]) => !name.startsWith("behavior.") && name !== "photoFiles"));
      const isUpdate = Boolean(savedId);
      const response = await fetch(isUpdate ? `/api/shelter/animals/${savedId}` : "/api/shelter/animals", {
        method: isUpdate ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...body, shelterId, behavior }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.errors?.join(" ") || result.error || "Salvataggio non riuscito.");
      const currentId = result.animal.id as string;
      setSavedId(currentId);

      await uploadSelectedPhotos(currentId);

      if (publish) {
        const published = await fetch(`/api/shelter/animals/${currentId}/publish`, { method: "POST" });
        const publishResult = await published.json();
        if (!published.ok) throw new Error(publishResult.blockers?.join(" · ") || publishResult.error || "Pubblicazione non riuscita.");
        window.location.assign(`/it/animali/${publishResult.animal.slug}`);
        return;
      }
      setMessage("Bozza salvata. Puoi continuare a modificarla o pubblicarla quando è pronta.");
      window.history.replaceState(null, "", `/it/rifugio/animali/${currentId}`);
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Richiesta non riuscita.");
    } finally { setBusy(false); }
  }

  const activeShelter = shelters.find((shelter) => shelter.id === shelterId);

  return <main className="catalog-page shelter-page">
    <a className="catalog-home" href="/it/rifugio/animali">← Tutti gli animali</a>
    <header className="catalog-heading"><p className="eyebrow">Area rifugi</p><h1>{published ? "Gestisci le foto" : initial?.id ? "Completa la scheda" : "Nuovo animale"}</h1><p className="intro">{published ? "Aggiorna l’ordine, la copertina e i testi alternativi delle foto." : "Salva una bozza in qualsiasi momento. Prima della pubblicazione controlliamo i dati e l'accessibilità delle foto."}</p></header>
    {shelters.length === 0 ? <section className="catalog-empty"><h2>Nessun rifugio associato</h2><p>Chiedi all'amministrazione di associare il tuo account a una struttura.</p></section> : <form className="animal-editor" onSubmit={(event) => { if (published) { event.preventDefault(); return; } void submit(event, (event.nativeEvent as SubmitEvent).submitter?.getAttribute("data-publish") === "true"); }}>
      {shelters.length > 1 && <label>Rifugio<select value={shelterId} onChange={(event) => setShelterId(event.target.value)}>{shelters.map((shelter) => <option key={shelter.id} value={shelter.id}>{shelter.name}</option>)}</select></label>}
      {activeShelter?.status !== "active" && <p className="animal-editor-note">La struttura è in attesa di approvazione: puoi preparare bozze, ma non pubblicarle.</p>}

      {!published && <><fieldset><legend>Informazioni principali</legend><div className="animal-editor-grid">
        {select("species", "Specie", ["dog", "cat"], true, initial?.fields.species)}
        <label>Nome<input name="name" maxLength={80} defaultValue={initial?.fields.name} /></label>
        <label>Codice interno (facoltativo)<input name="internalCode" maxLength={40} defaultValue={initial?.fields.internalCode} /></label>
        {select("sex", "Sesso", ["male", "female", "unknown"], true, initial?.fields.sex)}
        <label>Età approssimativa (mesi)<input name="ageMonths" type="number" min="0" max="360" defaultValue={initial?.fields.ageMonths} /></label>
        <label>Data di nascita stimata<input name="birthDate" type="date" defaultValue={initial?.fields.birthDate} /></label>
        <label className="animal-editor-check"><input name="birthDateEstimated" type="checkbox" defaultChecked={initial?.fields.birthDateEstimated !== "false"} /> Data approssimativa</label>
        <label>Ingresso nel rifugio<input name="intakeDate" type="date" required defaultValue={initial?.fields.intakeDate ?? new Date().toISOString().slice(0, 10)} /></label>
        {select("size", "Taglia", ["small", "medium", "large", "xlarge"], false, initial?.fields.size)}
        <label>Razza indicativa<input name="breedPrimary" maxLength={80} defaultValue={initial?.fields.breedPrimary} /></label>
        <label>Colore del mantello<input name="coatColor" maxLength={60} defaultValue={initial?.fields.coatColor} /></label>
        <label>Peso in kg<input name="weightKg" type="number" min="0.1" max="999.99" step="0.01" defaultValue={initial?.fields.weightKg} /></label>
        <label>Microchip (15 cifre)<input name="microchipNumber" inputMode="numeric" pattern="[0-9]{15}" maxLength={15} defaultValue={initial?.fields.microchipNumber} /></label>
      </div></fieldset>

      <fieldset><legend>Descrizione e salute</legend><div className="animal-editor-grid">
        <label>Titolo in italiano<input name="headlineIt" maxLength={140} defaultValue={initial?.fields.headlineIt} /></label>
        <label>Title in English<input name="headlineEn" maxLength={140} defaultValue={initial?.fields.headlineEn} /></label>
        <label className="animal-editor-wide">Storia e carattere (italiano)<textarea name="storyIt" rows={5} maxLength={20000} defaultValue={initial?.fields.storyIt} /></label>
        <label className="animal-editor-wide">Story and character (English)<textarea name="storyEn" rows={5} maxLength={20000} defaultValue={initial?.fields.storyEn} /></label>
        {select("isSterilized", "Sterilizzazione", ["yes", "no", "unknown"], true, initial?.fields.isSterilized)}
        {select("isVaccinatedSummary", "Vaccinazioni", ["yes", "no", "unknown"], false, initial?.fields.isVaccinatedSummary)}
        <label className="animal-editor-check"><input name="hasSpecialNeeds" type="checkbox" defaultChecked={initial?.fields.hasSpecialNeeds === "true"} /> Il rifugio segnala esigenze speciali</label>
        <label className="animal-editor-wide">Sintesi pubblica delle esigenze<input name="specialNeedsSummary" maxLength={255} defaultValue={initial?.fields.specialNeedsSummary} /></label>
        <label>Contributo spese (€)<input name="adoptionFeeEur" type="number" min="0" max="42949672" step="0.01" defaultValue={initial?.fields.adoptionFeeEur} /></label>
      </div></fieldset>

      <fieldset><legend>Profilo comportamentale</legend><p className="animal-editor-note">Usa “non noto” quando non hai ancora verificato una compatibilità. Il profilo viene registrato con il tuo account e la data di valutazione.</p><div className="animal-editor-grid">
        <label>Energia (1–5)<input name="behavior.energyLevel" type="number" min="1" max="5" defaultValue={initial?.behavior.energyLevel} /></label>
        <label>Socievolezza con le persone (1–5)<input name="behavior.sociabilityPeople" type="number" min="1" max="5" defaultValue={initial?.behavior.sociabilityPeople} /></label>
        {select("behavior.goodWithChildren", "Compatibilità bambini", ["yes", "older_only", "no", "unknown"], false, initial?.behavior.goodWithChildren)}
        {select("behavior.goodWithDogs", "Compatibilità cani", ["yes", "selective", "no", "unknown"], false, initial?.behavior.goodWithDogs)}
        {select("behavior.goodWithCats", "Compatibilità gatti", ["yes", "selective", "no", "unknown"], false, initial?.behavior.goodWithCats)}
        {select("behavior.houseTrained", "Abitudine alla casa", ["yes", "partially", "no", "unknown"], false, initial?.behavior.houseTrained)}
        {select("behavior.leashTrained", "Abitudine al guinzaglio", ["yes", "partially", "no", "unknown"], false, initial?.behavior.leashTrained)}
        <label>Tolleranza ai rumori (1–5)<input name="behavior.noiseTolerance" type="number" min="1" max="5" defaultValue={initial?.behavior.noiseTolerance} /></label>
        <label>Ore che può stare solo<input name="behavior.aloneToleranceHours" type="number" min="0" max="24" defaultValue={initial?.behavior.aloneToleranceHours} /></label>
        <label>Bisogno di addestramento (1–5)<input name="behavior.trainingNeeds" type="number" min="1" max="5" defaultValue={initial?.behavior.trainingNeeds} /></label>
        <label>Bisogno di toelettatura (1–5)<input name="behavior.groomingNeeds" type="number" min="1" max="5" defaultValue={initial?.behavior.groomingNeeds} /></label>
        <label>Minuti di attività al giorno<input name="behavior.exerciseMinPerDay" type="number" min="0" max="1440" defaultValue={initial?.behavior.exerciseMinPerDay} /></label>
        {select("behavior.suitableForFirstTime", "Prima adozione", ["yes", "no", "unknown"], false, initial?.behavior.suitableForFirstTime)}
        {select("behavior.needsGarden", "Giardino", ["yes", "preferred", "no", "unknown"], false, initial?.behavior.needsGarden)}
        <label className="animal-editor-wide">Note (italiano)<textarea name="behavior.notesIt" rows={3} maxLength={10000} defaultValue={initial?.behavior.notesIt} /></label>
        <label className="animal-editor-wide">Notes (English)<textarea name="behavior.notesEn" rows={3} maxLength={10000} defaultValue={initial?.behavior.notesEn} /></label>
      </div></fieldset></>}

      <fieldset><legend>Foto</legend><p className="animal-editor-note">JPEG, PNG, WebP o HEIC · massimo 10 foto da 10 MB ciascuna. Orientamento corretto e metadati personali rimossi automaticamente.</p>
        <label>Seleziona dal dispositivo<input name="photoFiles" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/avif" multiple onChange={(event) => changeFiles(event.target.files)} /></label>
        {existingPhotos.length > 0 && <div className="animal-photo-manager"><p>Foto già caricate. La copertina appare per prima nel catalogo.</p>{existingPhotos.map((photo, index) => <section className="animal-photo-entry" key={photo.id}>
          <img src={`/api/media/${photo.id}?width=320`} alt={photo.altTextIt || photo.altTextEn || "Foto animale"} />
          <div className="animal-photo-fields">
            <label>Testo alternativo in italiano<input maxLength={255} value={photo.altTextIt ?? ""} onChange={(event) => setExistingAlt(photo.id, "altTextIt", event.target.value)} /></label>
            <label>Testo alternativo in inglese<input maxLength={255} value={photo.altTextEn ?? ""} onChange={(event) => setExistingAlt(photo.id, "altTextEn", event.target.value)} /></label>
            <div className="animal-photo-actions">
              <button type="button" className="button secondary" disabled={Boolean(photoBusy)} onClick={() => managePhoto(photo.id, { altTextIt: photo.altTextIt ?? "", altTextEn: photo.altTextEn ?? "" })}>Salva testo</button>
              <button type="button" className="button secondary" disabled={Boolean(photoBusy) || index === 0} onClick={() => managePhoto(photo.id, { move: "up" })}>Sposta su</button>
              <button type="button" className="button secondary" disabled={Boolean(photoBusy) || index === existingPhotos.length - 1} onClick={() => managePhoto(photo.id, { move: "down" })}>Sposta giù</button>
              <button type="button" className="button secondary" disabled={Boolean(photoBusy) || photo.isPrimary} onClick={() => managePhoto(photo.id, { makePrimary: true })}>{photo.isPrimary ? "Copertina" : "Imposta copertina"}</button>
              <button type="button" className="button secondary" disabled={Boolean(photoBusy)} onClick={() => managePhoto(photo.id, "delete")}>Rimuovi dalla scheda</button>
            </div>
          </div>
        </section>)}</div>}
        {photos.map((photo, index) => <div className="animal-photo-entry" key={`${photo.file.name}-${photo.file.lastModified}`}>
          <p>{photo.file.name} ({Math.ceil(photo.file.size / 1024)} KB)</p>
          <label>Testo alternativo in italiano<input required={!photo.altTextEn.trim()} maxLength={255} value={photo.altTextIt} onChange={(event) => setAlt(index, "altTextIt", event.target.value)} /></label>
          <label>Testo alternativo in inglese<input required={!photo.altTextIt.trim()} maxLength={255} value={photo.altTextEn} onChange={(event) => setAlt(index, "altTextEn", event.target.value)} /></label>
        </div>)}
        {published && <button type="button" className="button" disabled={busy || photos.length === 0} onClick={uploadPublishedPhotos}>{busy ? "Caricamento…" : "Carica foto"}</button>}
      </fieldset>

      {error && <p className="match-error" role="alert">{error}</p>}{message && <p role="status">{message}</p>}
      {!published && <div className="animal-editor-actions"><button className="button secondary" type="submit" disabled={busy}>{busy ? "Salvataggio…" : "Salva bozza"}</button><button className="button" type="submit" data-publish="true" disabled={busy || activeShelter?.status !== "active"}>{busy ? "Pubblicazione…" : "Salva e pubblica"}</button></div>}
    </form>}
  </main>;
}
