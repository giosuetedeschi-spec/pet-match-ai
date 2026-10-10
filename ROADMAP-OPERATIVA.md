# Roadmap operativa PetMatch AI

Aggiornata: 2026-10-09. `docs/` descrive il prodotto e l'architettura di riferimento; questo file registra lo stato effettivo dell'implementazione.

## MVP Django + Streamlit

- [x] Gestione e pubblicazione degli animali da parte dei rifugi.
- [x] Catalogo pubblico e ricerca geografica di base con dati ISTAT.
- [x] API per candidature, revisione lato rifugio, richieste dell'adottante e programmazione visite.
- [ ] Consolidare i flussi di gestione MVP e le verifiche CI prima di estendere il prodotto.

## Release parallela Next.js + Prisma

- [x] Schema Prisma e database `petmatch_web` separato su MySQL condiviso.
- [x] Migrazione eseguita all'avvio Compose e health check collegato al database.
- [x] Catalogo pubblico italiano `/it/animali`: animali pubblicati di rifugi attivi, ricerca testuale, filtri per specie e taglia, paginazione.
- [x] Matching adottanti completo per la release Next.js: questionario anonimo riprendibile, profilo modificabile/cancellabile, account con verifica email e trasferimento del profilo, preferiti, risultati spiegati, filtri di sicurezza, raggio e catalogo ordinabile per compatibilità.
- [x] Cache e invalidazione degli abbinamenti, spiegazione Claude opzionale con fallback deterministico, notifiche in-app/email e disiscrizione senza login.
- [x] Worker schedulato per ricalcolo e digest, con limite di una notifica email ogni 48 ore per profilo.
- [ ] Completare il test d'usabilità con tre persone e verificare end-to-end invio digest e disiscrizione email. GitHub CI ha già avviato Compose e verificato la connessione MySQL.
- [x] Portale Next.js per membri di rifugi: bozze animali, dati e comportamento validati, pubblicazione consentita solo a strutture attive.
- [x] Foto: upload fino a 10 MB, testo alternativo, conversione WebP, varianti adattive, rimozione dei metadati EXIF, copertina e ordine gestibili, rimozione logica, storage locale persistente o bucket S3 compatibile privato.
- [x] Onboarding Next.js dei rifugi: account e struttura pending nella stessa transazione, verifica email, selezione comune ISTAT, revisione admin, approvazione/rifiuto con motivazione e bootstrap admin CLI.
- [x] Interfaccia e contenuti leggibili in italiano/inglese tramite servizio self-hosted LibreTranslate/Argos; i testi originali rimangono intatti.

Il matching Next.js supporta profili anonimi e account verificati. Gli account del portale rifugio devono essere membri di una struttura attiva; onboarding e approvazione sono gestiti fuori da questo flusso.

## ML

- [x] API FastAPI privata con health, model-info, inferenza singola e batch; autenticazione bearer e triage rifugi collegato con storico append-only.
- [x] Mock deterministico dichiarato esplicitamente per integrare e verificare il flusso. L'artefatto Cox ? escluso per leakage (`duration_days`, `is_adopted`); nessun numero ? presentato come previsione validata.
- [ ] Validare il modello rispetto ai criteri e ai limiti specificati in [`docs/05-ml-spec.md`](./docs/05-ml-spec.md).

## Procedura per ogni unità

1. Lavorare su un branch dedicato e aggiornare `STATE.md` come checkpoint.
2. Consegnare un'unità concreta per PR.
3. Eseguire i gate pertinenti e attendere CI verde.
4. Unire con merge commit e rimuovere il branch dopo il merge.
5. Aggiornare questa roadmap e `STATE.md` quando cambia lo stato.

## Stato corrente

Onboarding, revisione admin, servizio ML mock, triage e traduzione automatica sono implementati localmente nel branch `chore/clean-modules-types-docs`; le modifiche non sono ancora unite. Restano la validazione scientifica del modello, i test di usabilit? con tre persone e la verifica end-to-end di email, digest e disiscrizione.
