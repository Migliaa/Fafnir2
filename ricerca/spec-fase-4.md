# Specifica della fase 4: metriche e validazione

Scritta il 2026-11-22 per l'implementazione (delegabile). Formule e fonti: `fonti/paper/validazione-e-metriche.md` (parti A, B, C); cosa deve contenere la scheda e quali regole valgono: `ricerca/progetto-software.md`, sezioni "Metriche oltre a quelle di ProRealTime" e "Validazione".

## Vincoli

- Python 3.14, numpy, polars, scipy, numba 0.68 (già installati; niente pacchetti nuovi). Cicli pesanti (bootstrap, SPA) in numba con `cache=True`; tutto il resto numpy vettoriale.
- Unità: i profitti arrivano già in punti o in escursioni medie; le funzioni non convertono mai in % del prezzo.
- Le funzioni ricevono array, non leggono dati: niente accesso a `Dati/` (il taglio del fuori campione resta nel lettore).
- Ogni funzione pubblica restituisce numeri o dict di numeri serializzabili in JSON (float arrotondati a 4 cifre dove escono nei riassunti, `None` invece di NaN).
- Commenti e nomi in italiano, come in `motore/dati.py`. Docstring brevi con la fonte (autore, anno, sezione del file delle fonti).
- Generatori casuali con `seed` esplicito, default 0, così i risultati sono riproducibili.

## Ingressi standard

- `giorn`: array float dei profitti giornalieri **inclusi i giorni senza posizione** (zero), un valore per giorno di borsa del prodotto; `date`: array `datetime64[D]` della stessa lunghezza.
- `trade`: array float dei profitti per trade in ordine di chiusura; opzionalmente `lato` (+1/−1).
- `matrice`: array T×N (giorni × varianti) di profitti giornalieri di una famiglia di varianti.
- Annualizzazione con 252 giorni.

## `motore/metriche.py`

1. `sharpe(giorn)` annualizzato; `sharpe_lo(giorn, q=None)` con la correzione per autocorrelazione di Lo (2002), q di default = ⌊252^(1/3)⌋ o quello indicato nelle fonti.
2. `psr(giorn, sr_rif=0.0)` e `dsr(giorn, n_prove, var_sr_prove)` (Bailey, López de Prado 2012/2014), con asimmetria e curtosi dei rendimenti; `sr_atteso_massimo(n_prove, var_sr_prove)`.
3. `min_btl(n_prove, sr_annuo)` in anni, e l'inversa `prove_ammesse(anni, sr_annuo)` (Bailey et al. 2014). Controllo: 13 anni e SR 0,7 → circa 24 prove; 6 anni e SR 1 → circa 20 (valori già scritti in `progetto-software.md`: se non tornano, segnalarlo invece di adattare la formula).
4. Regolarità della curva (curva = somma cumulata di `giorn`): `r2`, `k_ratio` (Kestner 2003, versione indicata nelle fonti), `pendenze_annue` → coefficiente di variazione delle pendenze per anno di calendario e quota di anni con pendenza positiva, `ulcer`, `drawdown` → massimo, durata massima in giorni, quota di giorni sott'acqua, `trimestri_positivi`, `sharpe_mobile(giorn, finestra=252)` → minimo, mediana, quota positiva.
5. `senza_migliori(trade, k=10)`: profitto totale togliendo i k trade migliori.
6. `simmetria(giorn_long, giorn_short)`: Sharpe dei due lati della stessa regola specchiata e rapporto min/max.
7. `z_wald_wolfowitz(trade)`: N, numero di sequenze, sequenze attese, z, e una stringa che spiega il segno (z negativo = vincenti e perdenti raggruppati).
8. Monte Carlo (`montecarlo(giorn, trade=None, regimi=None, n=5000, seed=0)`):
   - bootstrap stazionario dei giorni (Politis, Romano 1994), lunghezza media del blocco scelta automaticamente (Politis, White 2004, con la correzione di Patton et al. 2009; se troppo lunga da implementare, dalla prima autocorrelazione non significativa di rendimenti e perdite, scrivendo quale si è usata);
   - ricampionamento per regime: `regimi` è un array di etichette per giorno (es. 0 calmo, 1 agitato); si ricampionano blocchi dentro ciascun regime mantenendo la sequenza storica dei regimi;
   - rimescolamento semplice dei trade (o dei giorni se `trade` manca) per confronto;
   - uscita per ciascun metodo: percentili 5/50/95 di drawdown massimo, peggior serie di perdite consecutive, profitto finale; e `rapporto_dd` = drawdown mediano a blocchi / drawdown mediano rimescolato.
9. Portafoglio (`matrice` = sistemi in colonne): `correlazioni` (normale e di coda: correlazione sui giorni in cui almeno uno è sotto il proprio 10° percentile), `sovrapposizione_dd(a, b)` = quota di giorni sott'acqua insieme / (quota a × quota b), `cdar(giorn, alfa=0.95)` e `contributo_cdar(matrice, pesi, i)` (Chekhlov, Uryasev, Zabarankin 2005), `enb(matrice)` (Meucci 2009, versione con le componenti principali).
10. `scheda(giorn, date, trade, ...)`: dict compatto con i blocchi 1, 3, 4 (quelli calcolabili qui), 5 e 6 della scheda di `progetto-software.md`; i blocchi che richiedono altri dati (CPCV, varianti specchiate, portafoglio) entrano se passati come argomenti opzionali, altrimenti `None`.

## `motore/validazione.py`

1. `blocchi_cpcv(anni, k=2)`: tutte le combinazioni di k anni di test (13 anni → 78), come liste di (anni di training, anni di test).
2. `purga(trade_inizio, trade_fine, anni_test, embargo_giorni)`: maschera dei trade di training da tenere (via quelli che si sovrappongono a un blocco di test, allargato dell'embargo dopo il blocco).
3. `cpcv_selezione(matrice, date, k=2)`: per ogni combinazione sceglie la variante con lo Sharpe migliore sugli anni di training e registra il suo Sharpe sugli anni di test; uscita: mediana, 10° percentile, quota positiva degli Sharpe fuori campione e quante volte è stata scelta ciascuna variante.
4. `pbo(matrice, s=16)`: CSCV di Bailey et al. (2017), uscita PBO, mediana dei logit, perdita di rendimento fuori campione.
5. `spa(matrice, b=2000, lungh_blocco=None, seed=0)`: p-value del test SPA di Hansen (2005) contro rendimento zero, bootstrap stazionario; `romano_wolf(matrice, ...)`: p-value aggiustati stepdown per ogni variante.
6. `haircut(sr_annuo, anni, n_prove, metodo="bhy")`: Sharpe corretto di Harvey, Liu (2015) con Bonferroni, Holm e BHY.
7. `n_indipendenti(matrice)`: numero effettivo di prove dalle autocorrelazioni fra varianti (autovalori della matrice di correlazione, (Σλ)²/Σλ², più il raggruppamento gerarchico con soglia di correlazione 0,5 come seconda stima); restituisce entrambe.
8. Registro unico dei tentativi, `risultati/registro/`:
   - `registra(esperimento, famiglia, prodotto, parametri: dict, giorn, date)`: aggiunge una riga a `tentativi.jsonl` (id, data e ora, esperimento, famiglia, prodotto, parametri, Sharpe, giorni) e la serie giornaliera a `curve/<famiglia>.parquet`;
   - `conteggio(famiglia=None)`: numero di prove, numero effettivo (punto 7), varianza degli Sharpe; sono gli ingressi di DSR e MinBTL.
   - `risultati/` è già esclusa da git.

## Comandi in `motore/cli.py`

Aggiungere `minbtl --sr 0.7 --anni 13` (prove ammesse e anni necessari) e `registro stato [--famiglia X]` (conteggio). La scheda di un sistema arriverà dai motori (fasi 5-6), non serve un comando ora.

## Test (`motore/test_metriche.py`, `motore/test_validazione.py`, eseguibili con `python -m`)

Su dati finti dal risultato noto, mai sui dati veri:
- Sharpe di una serie costante più rumore noto; Lo ≈ Sharpe semplice su rumore indipendente, più basso con autocorrelazione positiva (AR(1) con φ = 0,3).
- PSR = 0,5 quando lo Sharpe stimato è uguale a quello di riferimento; DSR scende al crescere di `n_prove`.
- MinBTL: i due valori di controllo del punto 3.
- Drawdown, Ulcer, durata e quota sott'acqua su una curva costruita a mano.
- Wald-Wolfowitz: sequenza alternata → z positivo grande; vincenti tutti prima e perdenti tutti dopo → z negativo grande.
- Monte Carlo: su rumore indipendente `rapporto_dd` ≈ 1 (entro 0,15); su una serie con volatilità a grappoli (regimi alternati di 60 giorni calmi e 60 agitati) `rapporto_dd` > 1,1. Il secondo test è quello che risponde alla domanda di Andrea sulle perdite a grappolo.
- PBO: matrice di puro rumore (1000 giorni × 50 varianti) → PBO tra 0,35 e 0,65; matrice con una variante con media chiaramente positiva e le altre rumore → PBO < 0,1.
- SPA e Romano-Wolf: rumore → p > 0,1; una variante con Sharpe annuo 2 su 10 anni → p < 0,05.
- `blocchi_cpcv` su 13 anni → 78 combinazioni; `purga` toglie un trade che attraversa l'inizio del blocco di test.
- `n_indipendenti`: 20 copie quasi uguali della stessa serie → circa 1; 20 serie indipendenti → circa 20.
- `sovrapposizione_dd`: due sistemi indipendenti → circa 1; lo stesso sistema due volte → 1 / quota sott'acqua.

Ogni test va visto fallire almeno una volta (per esempio invertendo un segno) prima di essere considerato valido.
