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
- [x] Matching adottanti completo per la release Next.js: questionario anonimo riprendibile, profilo modificabile/cancellabile, account con verifica email e trasferimento del profilo, preferiti, risultati spiegati, filtri di sicurezza, raggio e catalogo ordinabile per compatibilità.
- [x] Cache e invalidazione degli abbinamenti, spiegazione Claude opzionale con fallback deterministico, notifiche in-app/email e disiscrizione senza login.
- [x] Worker schedulato per ricalcolo e digest, con limite di una notifica email ogni 48 ore per profilo.
- [ ] Completare il test d'usabilità con tre persone e una verifica live su MySQL/SMTP.
- [ ] Creazione e pubblicazione di animali da parte dei rifugi, con validazione.
- [ ] Definire la consegna delle foto per Next.js. Nell'MVP Django le foto sono sul volume media; per ora non è previsto object storage.

Il matching Next.js supporta profili anonimi e account verificati. I dati mancanti sono trattati in modo prudente e mostrati come verifiche da fare con il rifugio. Build, typecheck e test automatici del matching sono passati; account, database e invio SMTP richiedono ancora una verifica live con i servizi attivi.

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
