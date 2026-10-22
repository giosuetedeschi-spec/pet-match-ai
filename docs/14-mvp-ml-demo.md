# Modelli ML dimostrativi nell'MVP

Aggiornato: 2026-10-13.

## Cosa vede ciascun ruolo

Il tab pubblico **CompatibilitÃ ** continua a classificare gli animali con le regole deterministiche esistenti. Informa che PetMatch usa modelli ML a supporto dei rifugi, ma non mostra stime sull'esito atteso di una persona o di una coppia.

Dopo il login come rifugio, Streamlit mostra due funzioni sperimentali:

1. **Esito dell'animale:** probabilitÃ  di adozione tra gli esiti storici registrati e permanenza media stimata, condizionata al fatto che l'animale venga adottato.
2. **Esito della coppia cane-adottante:** indicatore di rischio di restituzione dopo l'adozione, basato su un dataset Kaggle sintetico. Ãˆ utilizzabile solo per discutere eventuale supporto aggiuntivo.

Nessuna stima puÃ² rifiutare un adottante o un animale. Il modello di coppia Ã¨ solo per cani; il modello storico Austin copre cani e gatti.

## Dati, riproducibilitÃ  e risultati

### Esito e permanenza

Fonte: [Austin Animal Center Shelter Intakes and Outcomes su Kaggle](https://www.kaggle.com/datasets/aaronschlegel/austin-animal-center-shelter-intakes-and-outcomes), giÃ  presente in `training-data/aac_intakes_outcomes.csv`.

Il training usa una regressione logistica per adozione rispetto agli altri esiti osservati, e un regressore per la permanenza dei soli animali poi adottati. Le variabili di esito e di durata non entrano tra le feature. La valutazione usa le date di intake: training prima del 2017, validazione nel primo semestre 2017, test dal luglio 2017.

- Adozione: ROC-AUC 0,6507; average precision 0,5925; Brier 0,2303 sul test temporale (10.776 righe; base rate 48,13%).
- Permanenza condizionata all'adozione: MAE 20,36 giorni sul test temporale (5.186 adozioni).
- Limiti: dati storici di Austin, Texas; il file unito contiene esiti completati, non gli animali ancora in attesa; le metriche non convalidano l'uso in rifugi italiani e la durata non Ã¨ una data promessa.

### Rischio di restituzione della coppia

Fonte: [Dog Adoption Success â€” Does the Match Last? su Kaggle](https://www.kaggle.com/datasets/sergionefedov/dog-adoption-success-does-the-match-last). La scheda Kaggle lo descrive come sintetico, con 42.000 righe e 15% di esiti di restituzione; la licenza Ã¨ indicata come `Other`.

Il modello usa 16 attributi del cane e della famiglia. Esclude identificatore, target, motivo e giorni alla restituzione, oltre ai due campi di mismatch pre-calcolati. Lo split Ã¨ stratificato 80/20, seed 42.

- ROC-AUC 0,6172; average precision 0,2223; Brier 0,1244 (baseline costante 0,1274) sul test (8.400 righe; base rate 14,99%).
- Questi risultati sono deboli e derivano da dati sintetici: l'indicatore non Ã¨ una probabilitÃ  calibrata per il mondo reale e non costituisce un modello validato di compatibilitÃ .
- La riga CSV Kaggle va scaricata manualmente nella cartella `training-data/` e salvata come `dog_adoption_master.csv`. Non redistribuire il dataset finchÃ© la licenza `Other` non Ã¨ stata chiarita.

## Addestramento e avvio

Il training riproducibile Ã¨ in `services/ml/train_models.py`. Dalla radice del repository:

```powershell
.venv/Scripts/python.exe services/ml/train_models.py --data-dir training-data --output-dir services/ml/models
```

La compilazione dell'immagine Compose esegue lo stesso training e include i modelli nell'immagine. Per usare Streamlit:

```powershell
docker compose up -d --build mysql mail ml django streamlit
```

Le inferenze ML sono dietro l'area Streamlit Rifugi e gli endpoint FastAPI richiedono il bearer token di servizio. L'account locale generato dal seed Ã¨ `rifugio_esperanza` / `DemoRifugio123!`.

## Decisione

Il codice ora usa modelli addestrati anzichÃ© il vecchio mock, ma **non** supera una validazione di produzione. La stima sintetica di restituzione resta utile solo come dimostrazione tecnica; una ricostruzione attendibile richiede esiti reali e collegati tra candidature, profili adottanti e animali, raccolti con un follow-up post-adozione.
