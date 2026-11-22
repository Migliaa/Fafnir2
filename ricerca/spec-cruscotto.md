# Specifica di costruzione del cruscotto

Scritta il 2026-11-22. Il progetto (cosa e perché) è `ricerca/progetto-cruscotto.md`: leggerlo per intero prima di iniziare. Qui il come, in due parti da fare in ordine: A (dati e giudizio) e B (applicazione).

## Vincoli comuni

- Python 3.14, numpy, polars, numba, scipy; **niente pacchetti nuovi** (FastAPI non c'è: server con la libreria standard). Frontend in HTML, CSS e JavaScript senza librerie esterne e senza CDN (deve funzionare offline): i grafici si disegnano in SVG o canvas con codice proprio.
- Testi dell'interfaccia in italiano, brevi, parole italiane vere (vedi le preferenze di scrittura in `CLAUDE.md` del progetto: niente frasi di raccordo, niente tono da vendita, ogni sigla spiegata con un `title` o tolta).
- Mai leggere dati dal 2025-11-21 in poi; i comandi di questa specifica usano solo gli anni della scoperta (2011-2023), come il resto del motore. Non lanciare esperimenti nuovi e non scrivere nel registro dei tentativi: le prove diagnostiche della parte A non sono tentativi di selezione e vanno salvate a parte.
- Test su dati finti per la parte A (come `motore/test_*.py`); i test vecchi devono continuare a passare.

## Parte A: dati per la scheda

### A1. `motore/robustezza.py`

Per un candidato già lanciato (regola, prodotto, barre), calcola e restituisce un dict JSON:
- `costi_doppi`: riassunto di `backtest.simula` con il costo raddoppiato (aggiungere a `simula`/`eventi.prova` un parametro `molt_costi=1.0`);
- `ingresso_spostato`: con barre ≤ 15 minuti, la regola con `da` e `a` spostati di −15 e +15 minuti (media, PF, Sharpe di ciascuna); altrimenti `None`;
- `specchio`: regola speculare (`condizioni.specchia`);
- `gemello`: stessa regola sul primo gemello del catalogo che ha costi (riassunto); `None` se non c'è;
- `regimi`: media per trade e numero di trade nei giorni con escursione media sopra e sotto la mediana della scoperta;
- `finestre_12_mesi`: per ogni finestra di 12 mesi con passo 3 mesi, profitto netto e numero di trade;
- `calendario`: profitto netto per anno e mese;
- `vicini`: dal registro, le combinazioni della stessa famiglia e prodotto che differiscono di un solo passo di griglia; mediana dello Sharpe dei vicini / Sharpe del candidato (zona stabile se ≥ 0,7);
- `euro`: profitto, drawdown e trade medio per 1 CFD IG in euro. Aggiungere al catalogo `euro_punto` (indici a 1 € per punto: 1,0; dove non è noto `None`) e alle tabelle dei trade la colonna `punti` (netto in punti di prezzo). Se `euro_punto` è `None`, i campi in euro sono `None`.

### A2. `motore/giudizio.py`

`giudica(scheda, robustezza) -> dict` deterministico, con i sei gruppi del progetto. Per ogni gruppo: `esito` ("verde", "giallo", "rosso", "grigio" se mancano i dati), e la lista delle voci `{nome, valore, soglia, esito, spiegazione}` (spiegazione: una riga in italiano di cosa misura). Soglie iniziali, scritte come costanti in cima al file:

| Gruppo | Verde | Giallo | Rosso |
|---|---|---|---|
| Caso o vantaggio (cancello) | DSR ≥ 0,95 e PBO < 0,2 e 10° percentile CPCV > 0 | DSR ≥ 0,8 e PBO < 0,5 | il resto |
| Costi e fattibilità (cancello) | lordo medio / costo medio ≥ 3 e Sharpe con costi doppi > 0 | rapporto ≥ 2 | il resto |
| Regolarità | R² ≥ 0,8, anni positivi ≥ 70%, Sharpe 12 mesi positivo in ≥ 70% delle finestre | due su tre | il resto |
| Robustezza | zona stabile ≥ 0,7, senza i 10 migliori > 0, ingresso spostato con media > 0 in entrambi i versi, gemello con media > 0, 2019-2023 > 0 | almeno metà delle voci disponibili verdi | il resto |
| Rischio | rapporto drawdown blocchi/rimescolato ≤ 1,3 e |z| < 1,96 | rapporto ≤ 1,6 | il resto |
| Portafoglio | grigio finché non ci sono le liste dei trade dei sistemi in produzione | | |

Esito complessivo: `candidato` se i due cancelli sono verdi o gialli e nessun altro gruppo è rosso; `da_rivedere` se i cancelli non sono rossi ma un altro gruppo lo è; `scartato` se un cancello è rosso.

### A3. `motore/uscita.py`: codice ProRealCode

`prorealcode(regola, prodotto, barre) -> str`. In testa la console di `moduli/console-rischio-per-trade.txt` (copiata così com'è); poi la traduzione letterale della regola con le convenzioni scritte in `motore/motori/eventi.py` (ora di chiusura della barra = `Time`, ingresso al mercato alla barra dopo, `barindex - tradeindex > N`, `dayofweek`, una posizione alla volta). Ogni famiglia di `condizioni.py` ha la sua traduzione in ProRealCode (escursione giornaliera media = media delle ultime 20 differenze `DHigh(i) - DLow(i)` a partire da i = 1; `AverageTrueRange`, `ExponentialAverage`, `RSI` come in ProRealTime). Stop e target in escursioni diventano `SET STOP LOSS` / `SET TARGET PROFIT` in punti calcolati all'ingresso. Le famiglie che non si sanno tradurre producono un commento `// DA TRADURRE: ...` e il campo `completo: false`. Niente righe `GRAPH`. Test: la regola del long di 165 DAX in `esperimenti/taratura/` produce codice con `time = 133000`, `ExponentialAverage[25]`, `RSI[2]`.

### A4. Comando `python -m motore.cli esperimento arricchisci <nome>`

Per ogni candidato di un esperimento già lanciato: `robustezza`, `giudizio`, `prorealcode`; li aggiunge a `candidati/<id>.json` (chiavi `robustezza`, `giudizio`, `prorealcode`) e scrive `candidati/<id>.prc`. Aggiunge a `riassunto.json` l'esito complessivo e il colore di ogni gruppo per ogni candidato. Non tocca il registro. Lanciarlo sull'esperimento `dax-long-5m-momento-chiusura`.

## Parte B: l'applicazione

### B1. Server `cruscotto/server.py`

`python -m cruscotto` (o `cruscotto/avvia.bat` per un doppio clic) avvia `ThreadingHTTPServer` su `127.0.0.1:8765` e apre il browser. Serve i file statici da `cruscotto/static/` e queste API JSON (lette da `risultati/` e `esperimenti/`, polars per i parquet):
- `GET /api/esperimenti`: elenco con intestazione, prove, budget, PBO, numero di candidati per esito;
- `GET /api/esperimenti/<nome>`: tutto `riassunto.json` + il resoconto `esperimenti/<nome>.md` in testo;
- `GET /api/sistemi`: una riga per candidato di tutti gli esperimenti (campi del riassunto + esito complessivo + colori dei gruppi + stato e nota di Andrea);
- `GET /api/sistemi/<nome>/<id>`: scheda completa, curva giornaliera (date e netto cumulato, drawdown), trade, codice PRT, commento dell'IA (`risultati/esperimenti/<nome>/commenti/<id>.md` se esiste, con data e modello in testa);
- `GET /api/registro`: tentativi con filtro per famiglia;
- `POST /api/sistemi/<nome>/<id>/decisione` con `{stato, nota, verifica}`: salva in `risultati/cruscotto/decisioni.json` (stato tra: da guardare, da approfondire, in verifica, live, scartato; `verifica` = `{data, esito, note}` della prova su ProRealTime). È l'unica scrittura dell'applicazione.
- Solo `127.0.0.1`, nessun accesso dalla rete.

### B2. Pagine (`cruscotto/static/`: `index.html`, `app.js`, `style.css`; navigazione con l'ancora `#/...`)

Tema scuro come AlphaMining con interruttore chiaro; menu a sinistra; larghezza fluida.
1. **Sistemi** (pagina iniziale): riquadri in alto (candidati, da rivedere, scartati, in verifica, live); filtri per esperimento, prodotto, lato, timeframe, esito, stato; ricerca per nome; tabella ordinabile con: nome, prodotto, lato, barre, esito complessivo, sei pallini colorati dei gruppi (con `title` che spiega), trade, media in escursioni, PF, Sharpe, DSR, anni positivi, 2019-2023, netto € 1 CFD, stato. Clic sulla riga → scheda.
2. **Scheda**: intestazione con nome, ipotesi e meccanismo dell'esperimento, esito complessivo grande e sei riquadri dei gruppi (colore + una riga di sintesi); schede:
   - *Riepilogo*: numeri chiave; il **giudizio dell'IA** in un riquadro a parte e distinto (bordo diverso, "Commento dell'IA, non deterministico" con data e modello), o "non ancora scritto";
   - *Curva*: equity netta con drawdown sotto, Monte Carlo a bande (5°-95° a blocchi) se i dati ci sono; risultato per anno in barre;
   - *Giudizio*: per ogni gruppo la tabella delle voci con valore, soglia, esito, spiegazione; prima i rossi;
   - *Robustezza*: finestre di 12 mesi come caselle colorate, vicini, costi doppi, ingresso spostato, specchio, gemello, regimi;
   - *Calendario*: tabella anno × mese colorata;
   - *Trade*: statistiche e lista paginata;
   - *Codice*: il ProRealCode con pulsante "copia" e "scarica .prc"; avviso se `completo: false`;
   - *Decisione*: stato, nota, esito della verifica su ProRealTime, salva.
3. **Esperimenti**: elenco; dettaglio con ipotesi, meccanismo, fonte, direzione, prove su budget, PBO per famiglia, resoconto, candidati.
4. **Registro**: tabella dei tentativi.
5. **Portafoglio**: pagina segnaposto che dice cosa servirà (liste dei trade dei sistemi in produzione).

### B3. Verifica

Avviare il server, aprire le pagine con un client HTTP (urllib) e controllare che ogni API risponda e che i numeri della scheda di `c01` coincidano con `candidati/c01.json`. Scrivere in `cruscotto/README.md` come si avvia (tre righe).
