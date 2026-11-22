# Specifica: decine di migliaia di sistemi, i filtri di Andrea, prova finale, schermata essenziale

Scritta il 2026-11-22 dopo il primo giro di Andrea sul cruscotto. Prima di scrivere codice leggere `motore/esperimento.py`, `motore/validazione.py`, `motore/giudizio.py`, `motore/robustezza.py`, `motore/motori/eventi.py`, `motore/catalogo.py`, `cruscotto/server.py`, `cruscotto/static/*`, `ricerca/progetto-cruscotto.md`.

## Cosa ha chiesto Andrea

- Il software deve provare **10.000 sistemi o più** in un esperimento: ne servono migliaia per trovarne un paio.
- Gli interessano pochi numeri: **guadagno medio a trade in €** (1 CFD IG), **utile / drawdown**, **se il guadagno copre spread e costi**, **tempo in mercato** (ogni posizione blocca margine), **regolarità della curva**, e vedere **quale periodo è in-sample e quale fuori campione**. Il resto è rumore e va tolto dalla vista principale.
- Regole di scarto, deterministiche (costanti modificabili in cima a `giudizio.py`):
  - guadagno medio netto per trade, 1 CFD IG: almeno **20 €** se la durata media del trade è fino a 36 ore; almeno **30 €** fino a 72 ore; almeno **50 €** oltre;
  - almeno **12 trade l'anno** in media (circa uno al mese);
  - curva regolare: R² della curva netta ≥ 0,85 e anni positivi ≥ 70%;
  - fuori campione convincente (sotto, prova finale): utile positivo e guadagno medio ≥ 50% di quello in-sample;
  - chi non le passa è **scartato**, senza vie di mezzo: l'esito "da rivedere" sparisce. Restano DSR e PBO come cancello statistico (sotto).
- Meno clic: le informazioni principali tutte nella prima schermata della scheda; il grafico della curva **quasi quadrato** (proporzione circa 1:1, mai più largo di 4:3) per giudicarne la forma a occhio.

## 1. Scala

Misurare prima i tempi (stampa a schermo, niente file) e poi correggere. Problemi già visti nel codice:
- `validazione.registra` rilegge e riscrive con una join il parquet della famiglia a ogni prova: con 10.000 prove è quadratico. Accumulare in memoria e scrivere una volta per famiglia e prodotto (`registra_molti`), stessa forma dei file.
- `validazione.n_indipendenti`: `eigvalsh` su una correlazione N×N e il raggruppamento gerarchico non reggono N = 10.000. Calcolare gli autovalori dalla SVD della matrice giorni × prove standardizzata (T ≈ 3.300 < N), e il raggruppamento su un campione casuale di al più 2.000 prove (scalando il risultato) con seme fisso; dichiararlo nel risultato.
- `esperimento.lancia` prova le combinazioni una alla volta: parallelizzare su processi (`concurrent.futures.ProcessPoolExecutor`, `os.cpu_count() - 1` lavoratori, la tabella `eventi.base` costruita una volta per processo), con una barra di avanzamento su stderr e salvataggi intermedi ogni 1.000 combinazioni per riprendere dopo un'interruzione (`lancia --riprendi`).
- I filtri di Andrea si applicano **prima** delle parti costose (backtest al minuto, robustezza, Monte Carlo), sui risultati del motore degli eventi: costano poco e scartano quasi tutto.
- Budget di prove: resta la MinBTL, ma è il file d'esperimento a dichiarare lo Sharpe che cerca (`sr_obiettivo`). Con 13 anni: 10.000 prove richiedono `sr_obiettivo` ≥ 1,19; `controlla` deve dire, oltre al massimo di combinazioni, lo Sharpe minimo che quel numero di prove impone, e il DSR lo applica comunque.
- Obiettivo misurato: 10.000 combinazioni su FDAX a 5 minuti in meno di 30 minuti sul PC di Andrea (12 thread). Misurarlo con un esperimento finto su dati veri FDAX ma con registro e risultati in cartelle temporanee (il registro vero non va toccato) e riportare i tempi per fase.

## 2. Prova finale (fuori campione)

Il periodo 2024 → maggio 2025 (`config.HOLDOUT_AVANTI`) si guarda una volta sola, e solo per i sistemi che hanno già passato tutti i filtri sulla scoperta (al massimo `k` per esperimento):
- `motore/prova_finale.py`: rifà `backtest.simula` sullo stesso prodotto e regola sugli anni dell'holdout in avanti (la tabella base va costruita con un parametro `anni=(2024, 2025)`; il lettore continua a tagliare al 2025-11-21 e i dati finiscono a maggio 2025) e anche sull'holdout all'indietro (inizio dati → 2010) se ci sono dati;
- segna nel registro (campo `holdout_usato` del tentativo) che quel sistema ha consumato la prova: non si ripete, e un sistema che la fallisce resta scartato e visibile come tale;
- salva le serie giornaliere dei due holdout accanto a quella della scoperta, così la curva le mostra in colori diversi.

## 3. Giudizio

`giudizio.py` diventa: **filtri di Andrea** (sopra) + **cancello statistico** (DSR ≥ 0,95 sul numero effettivo di prove dell'esperimento; PBO della famiglia < 0,2 quando la famiglia ha almeno 4 combinazioni) + prova finale. Esiti: `candidato` (passa tutto, compresa la prova finale), `scartato` (con il motivo principale in una frase: "guadagno medio 4 € sotto i 20 €", "11 trade l'anno", "fuori campione negativo"…). I sei gruppi colorati restano come dettaglio, non come esito.

Unità: 1 CFD IG da 1 € a punto per indici (DAX, Euro Stoxx, S&P, Nasdaq, Dow, Russell: i contratti "(1€)" di IG sono in euro, non in dollari) e per l'oro "(E1)"; per gli altri prodotti `euro_punto = None` e il sistema non è giudicabile sui filtri in euro (esito `scartato`, motivo "valore del punto non noto").

## 4. Schermata

Scheda, tutto nella prima vista senza clic:
- a sinistra la **curva netta quasi quadrata** con tre fasce di colore: holdout all'indietro, scoperta (in-sample), holdout in avanti (fuori campione), con le date scritte sotto; drawdown sotto in piccolo;
- a destra **sei numeri grandi** con la soglia accanto e il colore: guadagno medio €/trade, utile / drawdown, guadagno lordo / costi (spread + notte), tempo in mercato (ore medie per trade e % del tempo), regolarità (R²), trade l'anno; sotto, una riga per il fuori campione (trade, utile, guadagno medio rispetto all'in-sample);
- sotto, esito e motivo in una frase, poi il commento dell'IA se c'è;
- tutto il resto (gruppi, CPCV, Monte Carlo, robustezza, calendario, trade, codice) in sezioni chiuse che si aprono con un clic, nello stesso ordine di oggi; niente schede.

Elenco dei sistemi: per default mostra solo i candidati; colonne: nome, prodotto, lato, €/trade, utile/DD, lordo/costi, ore in mercato, R², trade/anno, fuori campione (€/trade), esito; un mini-grafico quadrato della curva in ogni riga (SVG piccolo). Clic sulla riga apre la scheda. Gli scartati si vedono con un interruttore, con il motivo.

## 5. Test

- Scala: un test su dati finti che chiama `lancia` con 2.000 combinazioni e verifica che il registro abbia 2.000 righe e i file delle curve una colonna per prova; `n_indipendenti` su 3.000 serie finte (20 gruppi di serie quasi uguali) restituisce circa 20 con entrambi i metodi.
- Filtri: casi limite delle tre soglie in euro per durata, dei 12 trade l'anno, dell'R².
- Prova finale: non legge niente oltre maggio 2025 e non si ripete sullo stesso tentativo.
- Ogni test visto fallire con un errore introdotto apposta; i test vecchi continuano a passare (aggiornando quelli che controllano l'esito "da rivedere", che non esiste più).
- Rilanciare `arricchisci` (e la prova finale) sull'esperimento `dax-long-5m-momento-chiusura`: con 4,4 €/trade tutti i candidati devono risultare scartati per il guadagno medio.
