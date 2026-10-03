# Roadmap operativa PetMatch AI

Aggiornata: 2026-10-03. La specifica prodotto in `docs/` resta la fonte di requisiti e non viene modificata.

## Priorità MVP Django + Streamlit

- [x] Pubblicazione degli animali da parte dei rifugi e catalogo esplorabile dagli adottanti.
- [x] Dati ISTAT e ricerca geografica di base.
- [ ] Consolidare i flussi MVP di gestione animali e le verifiche CI prima di passare a matching e funzionalità successive.

## Release parallela Next.js + Prisma

- [x] Fondazione Prisma per comuni, utenti, rifugi, membri, animali, media e profilo comportamentale; database `petmatch_web` separato su MySQL condiviso.
- [x] Migration applicata all’avvio Compose e health check collegato alla tabella `comuni`.
- [x] Catalogo pubblico Next.js con ricerca testo, specie, taglia e paginazione; include solo animali pubblicati di rifugi attivi.
- [ ] Flusso rifugio per creare e pubblicare animali con validazione.
- [ ] Foto salvate nel volume media Django per l’MVP; definire integrazione media della release Next senza introdurre object storage in questa fase.

## Procedura per ogni unità

1. Branch dedicato e checkpoint in `STATE.md`.
2. Una unità concreta per PR; documentazione originale `docs/` invariata.
3. Eseguire i gate pertinenti e attendere CI verde.
4. Merge con merge commit; eliminare il branch dopo il merge.

## Stato unità corrente

PR #22 merged con CI verde in `631ff394ea0b0aa507b3632682ee0e6c9e595e64`; il branch è stato eliminato. Unità corrente: `codex/phase1-next-public-catalog`, per il catalogo pubblico Next.js. Le foto attendono l’integrazione media; dettagli in `STATE.md`.
