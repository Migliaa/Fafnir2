# Specifica della fase 6: backtest al minuto, file d'esperimento, lancio

Scritta il 2026-11-22. Prima di scrivere codice leggere: `motore/motori/eventi.py` (formato della regola e convenzioni ProRealTime, da non cambiare), `motore/condizioni.py`, `motore/metriche.py`, `motore/validazione.py`, `motore/dati.py`, `motore/cli.py`, e in `ricerca/progetto-software.md` le sezioni "Chi usa il software" e "Validazione".

## Vincoli

- Python 3.14, numpy, polars, numba 0.68; niente pacchetti nuovi. Cicli in numba con `cache=True`.
- Solo anni della scoperta (`config.SCOPERTA`); i holdout non si leggono da nessun comando di questa fase.
- I test usano solo dati finti (sostituendo `dati.barre` e la nuova funzione dei minuti, come fa `motore/test_mappa.py`), mai `Dati/`.
- Riassunti per l'IA compatti (pochi KB), file completi a parte; `metriche.pulisci` per il JSON.

## 1. `motore/dati.py`: minuti con cache

`minuti(nome)` → barre da 1 minuto del simbolo o del cross (usa `_sorgente`), con cache su disco come `barre`, colonne `apre o h l c`.

## 2. `motore/motori/eventi.py`: piccola rifattorizzazione

Estrarre `candidati(tabella, regola) -> np.ndarray` (indici delle barre di decisione) da `prova`, senza cambiare il comportamento: i test esistenti devono passare invariati.

## 3. `motore/motori/backtest.py`

`simula(nome, minuti, regola, tabella=None, m1=None) -> (riassunto, trade)`:
- stessi candidati, stessa regola, stesse uscite a tempo di `eventi.prova` (l'istante d'uscita a tempo si calcola sulle barre come lì);
- percorso seguito sui minuti fra l'apertura della barra d'ingresso e l'istante d'uscita a tempo: stop, target e pareggio controllati minuto per minuto; nello stesso minuto stop e target → vince lo stop; se un minuto apre oltre il livello, si esce all'apertura di quel minuto;
- nuova chiave della regola `pareggio`: `{"attiva": x, "a": y}` in escursioni: quando il guadagno massimo raggiunto tocca `x`, lo stop si sposta a ingresso + `y` (nel verso del lato);
- una posizione alla volta e `max_al_giorno` come in `eventi`; costi dal catalogo come in `eventi`;
- colonne dei trade: quelle di `eventi` più `motivo` (`stop`, `target`, `pareggio`, `tempo`);
- il riassunto ha gli stessi campi di quello di `eventi`.

## 4. File d'esperimento (`esperimenti/<nome>.json`) e `motore/esperimento.py`

Campi obbligatori: `nome`, `ipotesi`, `meccanismo`, `fonte` (tipo di fonte), `direzione` (attesa, "long"/"short"), `modo` ("ampiezza" o "verticale"), `prodotti` (lista), `barre` (minuti), `regola` (formato di `eventi`). Facoltativi: `griglia` (chiave → lista di valori; la chiave è un percorso puntato nella regola, con indici numerici per le liste: `"cond.0.2": [3, 4, 5]`, `"uscita.barre": [50, 100]`), `specchio` (bool, prova anche la regola speculare come famiglia a parte), `sr_obiettivo` (default 1.0), `k` (candidati da approfondire, default 10).

`controlla(file) -> dict`: campi presenti e tipi; prodotti nel catalogo (avviso se `adatto=False`); chiavi della griglia esistenti nella regola; direzione coerente con `regola.lato`; numero di prove = combinazioni × prodotti (× 2 con lo specchio) più quelle già nel registro per la stessa famiglia; budget = `metriche.prove_ammesse(13, sr_obiettivo)`; in modo "verticale" budget dimezzato. Se si sfora, errore con il numero massimo di combinazioni ammesso. Nessun lancio senza `controlla` superato.

`lancia(file) -> dict`:
1. per ogni prodotto, `eventi.base` una volta sola; per ogni combinazione della griglia `eventi.prova`; serie giornaliera (giorni di borsa del prodotto, zeri compresi) registrata con `validazione.registra(esperimento, famiglia, prodotto, parametri, giorn, date)`, famiglia = `<nome>` (e `<nome>-specchio`);
2. per famiglia e prodotto: matrice giorni × combinazioni → `validazione.pbo` (se almeno 4 combinazioni) e `validazione.cpcv_selezione`; per ogni combinazione `metriche.dsr` con `validazione.conteggio(famiglia)` (numero effettivo di prove e varianza degli Sharpe);
3. ordinamento per DSR; i primi `k` passano a `backtest.simula` e a `metriche.scheda` (con DSR, PBO, CPCV, Monte Carlo);
4. scrittura in `risultati/esperimenti/<nome>/`: `riassunto.json` (intestazione, prove, budget, PBO per famiglia e prodotto, una riga compatta per candidato: prodotto, parametri, n, media, PF, Sharpe, DSR, anni positivi, media 2019-2023, passa/non passa le soglie DSR > 0,95 e PBO < 0,2), `candidati/<id>.json` (scheda completa), `candidati/<id>_trade.parquet`, `candidati/<id>_giorn.parquet`;
5. un file d'esperimento già lanciato non si rilancia (controllo sull'esistenza di `riassunto.json`), coerente con la regola "validazione una volta sola".

## 5. Comandi in `motore/cli.py`

`esperimento controlla <file>`, `esperimento lancia <file>`, `esperimento riassunto <nome>` (stampa `riassunto.json`), `backtest <prodotto> <regola.json> --barre N`.

## 6. Test

- `test_backtest.py`: (a) senza stop, target e pareggio, `backtest.simula` dà gli stessi trade e lo stesso netto di `eventi.prova` sulla stessa tabella finta; (b) uno stop toccato nel primo minuto di una barra in cui alla chiusura sarebbe stato toccato anche il target: esce in stop; (c) un target toccato prima dello stop dentro la stessa barra oraria (ordine visibile solo nei minuti): esce in target, mentre `eventi` dà stop; (d) pareggio: dopo il guadagno di `attiva` il prezzo torna all'ingresso → esce a ingresso + `a`; (e) apertura di un minuto oltre lo stop → esce all'apertura.
- `test_esperimento.py`: `controlla` rifiuta un campo mancante, una chiave di griglia inesistente e una griglia oltre il budget; `lancia` su dati finti con un vantaggio inserito in una combinazione (es. un'ora in cui il prezzo sale sempre) la mette prima nel riassunto, e un secondo `lancia` dello stesso file è rifiutato.
- Ogni test visto fallire con un errore introdotto apposta, poi ripristinato; i test vecchi devono continuare a passare.
