"use client";

import { useEffect, useState } from "react";
import type { AdopterAnswers } from "@/lib/matching";

type ComuneOption = { id: number; name: string; provinceCode: string; region: string };
type ProfileResponse = AdopterAnswers & { completedAt: string | null };

const defaults: AdopterAnswers = {
  currentStep: 0,
  preferredSpecies: "either",
  housingType: "apartment",
  housingSizeSqm: 50,
  hasOutdoorSpace: false,
  outdoorSpaceSqm: 0,
  householdAdults: 1,
  childrenAges: [],
  existingDogs: 0,
  existingCats: 0,
  hoursAlonePerDay: 4,
  activityLevel: 3,
  experienceLevel: "first_time",
  groomingCapacity: 3,
  trainingCapacity: 3,
  monthlyBudgetEur: null,
  preferredSizes: [],
  preferredAgeBands: [],
  preferredSex: "any",
  searchComuneId: null,
  searchRadiusKm: 50,
  dealbreakers: [],
};

const ageOptions = [
  { value: 5, label: "0–5 anni" },
  { value: 6, label: "6–11 anni" },
  { value: 12, label: "12–17 anni" },
];

const dealbreakerOptions = [
  ["must_be_house_trained", "Deve essere già abituato alla vita in casa"],
  ["no_special_needs", "Non posso accogliere un animale con esigenze speciali"],
  ["no_dogs_over_25kg", "Cerco un cane sotto i 25 kg"],
  ["must_be_good_with_children", "Deve essere compatibile con i bambini"],
  ["must_be_good_with_cats", "Deve essere compatibile con i gatti"],
  ["must_be_good_with_dogs", "Deve essere compatibile con i cani"],
  ["no_puppies", "Non cerco un cucciolo"],
  ["must_be_sterilized", "Deve essere già sterilizzato"],
] as const;

export default function MatchWizard() {
  const [profile, setProfile] = useState<AdopterAnswers>(defaults);
  const [step, setStep] = useState(0);
  const [complete, setComplete] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [comuneQuery, setComuneQuery] = useState("");
  const [comuni, setComuni] = useState<ComuneOption[]>([]);

  useEffect(() => {
    fetch("/api/matching/profile")
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error ?? "Profilo non disponibile.");
        const saved = data as ProfileResponse;
        setProfile({
          ...defaults,
          ...saved,
          housingType: saved.housingType ?? defaults.housingType,
          housingSizeSqm: saved.housingSizeSqm ?? defaults.housingSizeSqm,
          hasOutdoorSpace: saved.hasOutdoorSpace ?? defaults.hasOutdoorSpace,
          outdoorSpaceSqm: saved.outdoorSpaceSqm ?? defaults.outdoorSpaceSqm,
          householdAdults: saved.householdAdults ?? defaults.householdAdults,
          childrenAges: Array.isArray(saved.childrenAges) ? saved.childrenAges : [],
          hoursAlonePerDay: saved.hoursAlonePerDay ?? defaults.hoursAlonePerDay,
          activityLevel: saved.activityLevel ?? defaults.activityLevel,
          experienceLevel: saved.experienceLevel ?? defaults.experienceLevel,
          groomingCapacity: saved.groomingCapacity ?? defaults.groomingCapacity,
          trainingCapacity: saved.trainingCapacity ?? defaults.trainingCapacity,
          preferredSizes: Array.isArray(saved.preferredSizes) ? saved.preferredSizes : [],
          preferredAgeBands: Array.isArray(saved.preferredAgeBands) ? saved.preferredAgeBands : [],
          dealbreakers: Array.isArray(saved.dealbreakers) ? saved.dealbreakers : [],
          searchComuneId: saved.searchComuneId ?? null,
          searchRadiusKm: saved.searchRadiusKm ?? defaults.searchRadiusKm,
        });
        setStep(Math.min(saved.currentStep ?? 0, 13));
        setComplete(Boolean(saved.completedAt));
        if (saved.searchComune) setComuneQuery(`${saved.searchComune.name} (${saved.searchComune.provinceCode})`);
        setProfileLoaded(true);
        setLoaded(true);
      })
      .catch((cause) => {
        setError(cause instanceof Error ? cause.message : "Profilo non disponibile.");
        setLoaded(true);
      });
  }, []);

  useEffect(() => {
    if (step !== 13 || comuneQuery.trim().length < 2 || profile.searchComuneId !== null) {
      setComuni([]);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      fetch(`/api/comuni?q=${encodeURIComponent(comuneQuery.trim())}`, { signal: controller.signal })
        .then((response) => response.json())
        .then((data: ComuneOption[]) => setComuni(Array.isArray(data) ? data : []))
        .catch(() => undefined);
    }, 200);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [comuneQuery, profile.searchComuneId, step]);

  function update<K extends keyof AdopterAnswers>(key: K, value: AdopterAnswers[K]) {
    setProfile((current) => ({ ...current, [key]: value }));
    setComplete(false);
  }

  function toggleNumber(key: "childrenAges", value: number, checked: boolean) {
    const next = checked
      ? [...profile.childrenAges, value].sort((a, b) => a - b)
      : profile.childrenAges.filter((age) => age !== value);
    update(key, next);
  }

  function toggleChoice(key: "preferredSizes" | "preferredAgeBands" | "dealbreakers", value: string, checked: boolean) {
    const current = profile[key] as string[];
    update(key, (checked ? [...current, value] : current.filter((item) => item !== value)) as AdopterAnswers[typeof key]);
  }

  async function save(nextStep: number) {
    const response = await fetch("/api/matching/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile, currentStep: nextStep }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error ?? "Non riesco a salvare le risposte.");
    return data as ProfileResponse;
  }

  async function next() {
    setBusy(true);
    setError("");
    try {
      const nextStep = step + 1;
      const saved = await save(nextStep);
      setProfile((current) => ({ ...current, ...saved }));
      if (nextStep === 14) {
        setComplete(true);
        window.location.assign("/it/abbinamento/risultati");
      } else {
        setStep(nextStep);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Non riesco a salvare le risposte.");
    } finally {
      setBusy(false);
    }
  }

  async function back() {
    const previousStep = Math.max(0, step - 1);
    setBusy(true);
    setError("");
    try {
      const saved = await save(previousStep);
      setProfile((current) => ({ ...current, ...saved }));
      setStep(previousStep);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Non riesco a salvare le risposte.");
    } finally {
      setBusy(false);
    }
  }

  async function deleteProfile() {
    setBusy(true);
    try {
      await fetch("/api/matching/profile", { method: "DELETE" });
      window.location.assign("/it/abbinamento");
    } finally {
      setBusy(false);
    }
  }

  if (!loaded) return <p role="status">Caricamento del questionario…</p>;
  if (!profileLoaded) return <section className="catalog-empty"><p role="alert">{error}</p><button className="button" type="button" onClick={() => window.location.reload()}>Riprova</button></section>;
  if (error && !loaded) return <p role="alert">{error}</p>;

  if (complete) {
    return (
      <section className="match-complete">
        <h2>Il tuo profilo è pronto</h2>
        <p>Le risposte sono salvate in modo privato in questo browser. Puoi rivederle, vedere i risultati o cancellarle.</p>
        <div className="actions">
          <a className="button" href="/it/abbinamento/risultati">Vedi gli abbinamenti</a>
          <button className="button secondary" type="button" onClick={() => { setComplete(false); setStep(0); }}>Modifica le risposte</button>
          <button className="button secondary" type="button" disabled={busy} onClick={deleteProfile}>Cancella profilo e preferiti</button>
        </div>
      </section>
    );
  }

  const checkboxes = (
    values: readonly (readonly [string, string])[],
    selected: string[],
    key: "preferredSizes" | "preferredAgeBands" | "dealbreakers",
  ) => values.map(([value, label]) => (
    <label className="match-check" key={value}>
      <input type="checkbox" checked={selected.includes(value)} onChange={(event) => toggleChoice(key, value, event.target.checked)} /> {label}
    </label>
  ));

  return (
    <section className="match-wizard">
      <div className="match-progress">
        <label htmlFor="match-progress">Domanda {step + 1} di 14</label>
        <progress id="match-progress" value={step + 1} max={14} />
      </div>
      <fieldset className="match-question">
        {step === 0 && <>
          <legend>Che tipo di animale stai cercando?</legend>
          {[ ["either", "Sono aperto/a a entrambi"], ["dog", "Cane"], ["cat", "Gatto"] ].map(([value, label]) => <label className="match-choice" key={value}><input type="radio" name="species" checked={profile.preferredSpecies === value} onChange={() => update("preferredSpecies", value as AdopterAnswers["preferredSpecies"])} /> {label}</label>)}
        </>}
        {step === 1 && <>
          <legend>Dove vivi?</legend>
          {[["apartment", "Appartamento"], ["house_no_garden", "Casa senza giardino"], ["house_with_garden", "Casa con giardino"], ["farm", "Cascina o campagna"]].map(([value, label]) => <label className="match-choice" key={value}><input type="radio" name="housingType" checked={profile.housingType === value} onChange={() => update("housingType", value as AdopterAnswers["housingType"])} /> {label}</label>)}
        </>}
        {step === 2 && <>
          <legend>Quanto è grande, all’incirca, la tua casa?</legend>
          <label>Metri quadrati
            <select value={profile.housingSizeSqm} onChange={(event) => update("housingSizeSqm", Number(event.target.value))}>
              <option value={40}>Meno di 50 m²</option><option value={65}>50–80 m²</option><option value={100}>80–120 m²</option><option value={150}>Più di 120 m²</option>
            </select>
          </label>
        </>}
        {step === 3 && <>
          <legend>Hai uno spazio esterno tuo?</legend>
          {[["0", "No"], ["5", "Balcone o terrazzo"], ["50", "Giardino piccolo"], ["200", "Giardino grande"]].map(([value, label]) => <label className="match-choice" key={value}><input type="radio" name="outdoor" checked={profile.outdoorSpaceSqm === Number(value)} onChange={() => { update("outdoorSpaceSqm", Number(value)); update("hasOutdoorSpace", Number(value) > 0); }} /> {label}</label>)}
        </>}
        {step === 4 && <>
          <legend>Chi vive con te?</legend>
          <label>Numero di adulti in casa
            <select value={profile.householdAdults} onChange={(event) => update("householdAdults", Number(event.target.value))}>{[1, 2, 3, 4, 5, 6].map((count) => <option key={count} value={count}>{count}</option>)}</select>
          </label>
          <p>Se ci sono bambini, indica le fasce d’età. Ti chiediamo queste informazioni per valutare la convivenza in modo prudente.</p>
          {ageOptions.map(({ value, label }) => <label className="match-check" key={value}><input type="checkbox" checked={profile.childrenAges.includes(value)} onChange={(event) => toggleNumber("childrenAges", value, event.target.checked)} /> {label}</label>)}
        </>}
        {step === 5 && <>
          <legend>Hai già animali in casa?</legend>
          <label>Numero di cani<select value={profile.existingDogs} onChange={(event) => update("existingDogs", Number(event.target.value))}>{[0, 1, 2, 3, 4, 5].map((count) => <option key={count} value={count}>{count}</option>)}</select></label>
          <label>Numero di gatti<select value={profile.existingCats} onChange={(event) => update("existingCats", Number(event.target.value))}>{[0, 1, 2, 3, 4, 5].map((count) => <option key={count} value={count}>{count}</option>)}</select></label>
        </>}
        {step === 6 && <>
          <legend>Quante ore al giorno l’animale resterebbe solo?</legend>
          <label>Ore al giorno<select value={profile.hoursAlonePerDay} onChange={(event) => update("hoursAlonePerDay", Number(event.target.value))}>{[0, 2, 4, 6, 8, 10].map((hours) => <option key={hours} value={hours}>{hours === 10 ? "Più di 8" : `${hours} ore`}</option>)}</select></label>
        </>}
        {step === 7 && <>
          <legend>Quanto sei attivo/a?</legend>
          <label>Livello di attività<select value={profile.activityLevel} onChange={(event) => update("activityLevel", Number(event.target.value))}>{[[1, "Poco attivo/a"], [2, "Un po’ attivo/a"], [3, "Moderatamente attivo/a"], [4, "Molto attivo/a"], [5, "Molto sportivo/a"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        </>}
        {step === 8 && <>
          <legend>Hai già avuto animali?</legend>
          {[["first_time", "È la prima volta"], ["some", "Ho già avuto animali"], ["experienced", "Ho molta esperienza"]].map(([value, label]) => <label className="match-choice" key={value}><input type="radio" name="experience" checked={profile.experienceLevel === value} onChange={() => update("experienceLevel", value as AdopterAnswers["experienceLevel"])} /> {label}</label>)}
        </>}
        {step === 9 && <>
          <legend>Quanto tempo puoi dedicare alla cura del pelo?</legend>
          <label>Disponibilità<select value={profile.groomingCapacity} onChange={(event) => update("groomingCapacity", Number(event.target.value))}>{[[1, "Il minimo"], [2, "Poco"], [3, "Abbastanza"], [4, "Molto"], [5, "Anche ogni giorno"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        </>}
        {step === 10 && <>
          <legend>Quanto tempo puoi dedicare all’educazione?</legend>
          <label>Disponibilità<select value={profile.trainingCapacity} onChange={(event) => update("trainingCapacity", Number(event.target.value))}>{[[1, "Il minimo"], [2, "Poco"], [3, "Abbastanza"], [4, "Molto"], [5, "Anche ogni giorno"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        </>}
        {step === 11 && <>
          <legend>Hai preferenze su taglia, età o sesso?</legend>
          <p>Puoi selezionare più opzioni o non indicare preferenze.</p>
          {checkboxes([["small", "Piccola"], ["medium", "Media"], ["large", "Grande"], ["xlarge", "Molto grande"]] as const, profile.preferredSizes, "preferredSizes")}
          {checkboxes([["puppy", "Cucciolo"], ["young", "Giovane"], ["adult", "Adulto"], ["senior", "Senior"]] as const, profile.preferredAgeBands, "preferredAgeBands")}
          <label>Sesso preferito<select value={profile.preferredSex} onChange={(event) => update("preferredSex", event.target.value as AdopterAnswers["preferredSex"])}><option value="any">Nessuna preferenza</option><option value="male">Maschio</option><option value="female">Femmina</option></select></label>
        </>}
        {step === 12 && <>
          <legend>C’è qualcosa che per te è escluso?</legend>
          <p>Le condizioni selezionate escludono gli animali che non le rispettano; la pagina risultati mostrerà quante schede sono state filtrate.</p>
          {checkboxes(dealbreakerOptions, profile.dealbreakers, "dealbreakers")}
        </>}
        {step === 13 && <>
          <legend>Dove cerchi?</legend>
          <label htmlFor="comune-search">Comune di partenza</label>
          <input id="comune-search" type="search" value={comuneQuery} onChange={(event) => { setComuneQuery(event.target.value); update("searchComuneId", null); }} autoComplete="off" aria-controls="comune-options" aria-expanded={comuni.length > 0} />
          {comuni.length > 0 && <ul className="comune-options" id="comune-options" role="listbox">{comuni.map((comune) => <li key={comune.id}><button type="button" role="option" onClick={() => { update("searchComuneId", comune.id); setComuneQuery(`${comune.name} (${comune.provinceCode})`); setComuni([]); }}>{comune.name} ({comune.provinceCode}) · {comune.region}</button></li>)}</ul>}
          {!profile.searchComuneId && <p>Scrivi almeno due lettere e seleziona un comune dai risultati.</p>}
          <label>Raggio di ricerca<select value={profile.searchRadiusKm} onChange={(event) => update("searchRadiusKm", Number(event.target.value))}>{[10, 25, 50, 100, 200].map((km) => <option value={km} key={km}>{km} km</option>)}</select></label>
          <label>Budget mensile indicativo (€), facoltativo<input type="number" min="0" max="100000" step="10" value={profile.monthlyBudgetEur ?? ""} onChange={(event) => update("monthlyBudgetEur", event.target.value === "" ? null : Number(event.target.value))} /></label>
        </>}
      </fieldset>
      {error && <p role="alert" className="match-error">{error}</p>}
      <div className="match-wizard-controls">
        <button className="button secondary" type="button" onClick={back} disabled={step === 0 || busy}>Indietro</button>
        <button className="button" type="button" onClick={next} disabled={busy || (step === 13 && !profile.searchComuneId)}>
          {busy ? "Salvo…" : step === 13 ? "Salva e mostra i risultati" : "Continua"}
        </button>
      </div>
      <p className="match-privacy">Il profilo anonimo resta disponibile in questo browser per 6 mesi. Puoi cancellarlo dalla pagina dei risultati.</p>
    </section>
  );
}
