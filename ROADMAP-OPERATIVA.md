# Roadmap operativa PetMatch AI

Aggiornata: 2026-10-08. `docs/` descrive il prodotto e l'architettura di riferimento; questo file registra lo stato effettivo dell'implementazione.

## MVP Django + Streamlit

- [x] Gestione e pubblicazione degli animali da parte dei rifugi.
- [x] Catalogo pubblico e ricerca geografica di base con dati ISTAT.
- [x] API per candidature, revisione lato rifugio, richieste dell'adottante e programmazione visite.
- [ ] Consolidare i flussi di gestione MVP e le verifiche CI prima di estendere il prodotto.

## Release parallela Next.js + Prisma

- [x] Schema Prisma e database `petmatch_web` separato su MySQL condiviso.
- [x] Migrazione eseguita all'avvio Compose e health check collegato al database.
- [x] Catalogo pubblico italiano `/it/animali`: animali pubblicati di rifugi attivi, ricerca testuale, filtri per specie e taglia, paginazione.
- [ ] Creazione e pubblicazione di animali da parte dei rifugi, con validazione.
- [ ] Definire la consegna delle foto per Next.js. Nell'MVP Django le foto sono sul volume media; per ora non è previsto object storage.

## ML

- [x] Scaffold del servizio FastAPI incluso in Docker Compose.
- [ ] Configurare e servire un modello tramite API. Al momento `/health` riporta `model: not-configured`; le previsioni non sono una funzionalità live.
- [ ] Validare il modello rispetto ai criteri e ai limiti specificati in [`docs/05-ml-spec.md`](./docs/05-ml-spec.md).

## Procedura per ogni unità

1. Lavorare su un branch dedicato e aggiornare `STATE.md` come checkpoint.
2. Consegnare un'unità concreta per PR.
3. Eseguire i gate pertinenti e attendere CI verde.
4. Unire con merge commit e rimuovere il branch dopo il merge.
5. Aggiornare questa roadmap e `STATE.md` quando cambia lo stato.

## Stato corrente

Il catalogo pubblico Next.js è stato unito in PR #23. Il repository locale è su `main`, sincronizzato con `origin/main` al commit `10ad3ff` (merge di PR #23), senza modifiche locali al momento dell'aggiornamento. La prossima unità pianificata è il flusso rifugio per creare e pubblicare animali in Next.js; l'integrazione foto resta una decisione separata.
