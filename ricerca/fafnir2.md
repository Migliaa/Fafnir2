# Fafnir2: come si usa (guida per ogni sessione)

Fafnir2 è il software di ricerca di sistemi di questa cartella: motore in `motore/`, cruscotto per Andrea in `cruscotto/`. Il disegno e i risultati sono in `ricerca/protocollo-albero.md`; qui c'è come usarlo.

## Cosa fa

Cerca sistemi a orario fisso sui futures a 1 minuto di `Dati/` (in-sample 2014-2023, fuori campione 2024-maggio 2025, 2011-2013 e prima; mai niente dal 21 novembre 2025). Una **ricerca a cicli** alterna moltiplicazioni e filtri: forza bruta (ogni orario × 8 uscite × 50 pattern di struttura) → filtro 1 → combinazioni con altri pattern, indicatori e candele → filtro 2 → regime, calendario, altre uscite e orari → filtro 3 → ricalcolo esatto, gemello, segnale isolato, stop, verifica (DSR, ricerca rifatta anno per anno, prova sul rumore) → prova finale una volta sola. Una **campagna** lancia una ricerca per ogni prodotto, lato e timeframe, in parallelo.

## Comandi

```
python -m motore.campagna controlla esperimenti/<nome>.json
python -m motore.campagna lancia esperimenti/<nome>.json        # ore; riprende da dove era se interrotta
python -m motore.campagna riepilogo esperimenti/<nome>.json     # rifà solo la tabella finale
python -m motore.ricerca lancia esperimenti/<nome>.json         # una ricerca a cicli sola (minuti)
python -m cruscotto                                             # cruscotto su http://127.0.0.1:8765 (o cruscotto/avvia.bat)
```

Una campagna lunga va lanciata come processo separato, così sopravvive alla sessione (PowerShell): `Start-Process python -ArgumentList "-m","motore.campagna","lancia","esperimenti/<nome>.json" -WindowStyle Hidden -RedirectStandardOutput risultati/campagne/<nome>/campagna.log -RedirectStandardError risultati/campagne/<nome>/errori.log`. Il cruscotto si riavvia da solo quando cambia il codice e la pagina si ricarica: Andrea non deve riavviare niente. Non aprire un secondo server sulla 8765 (per le prove usare un'altra porta e chiuderlo).

## Dove sono i risultati (da leggere invece dei dati)

- `risultati/ricerche/<nome>/ricerca.json`: `imbuto` (quanti passano ogni passo), `cicli` (i migliori di ogni filtro con i motivi di scarto), `foglie` (i sistemi finali con misure, porte, curva, codice ProRealCode), `walkforward_ricerca`, `rumore`, `diario`. `stato.json` mentre gira.
- `risultati/campagne/<nome>/campagna.json`: tutti i finali della campagna in una tabella, con la conferma sugli altri prodotti; `spec.json`, un `.log` per ricerca.
- `risultati/registro/tentativi.jsonl`: ogni prova del ricalcolo esatto (il DSR delle ricerche future le conta).

Per rispondere ad Andrea basta leggere `campagna.json` o l'`imbuto` e le `foglie` di `ricerca.json`: pochi KB invece dei dati.

## File d'esperimento

- Ricerca: `esperimenti/dax-long-5m-cicli-8.json` (tipo `cicli`: prodotto, barre, lato, orari, uscite, cicli, rumore, uscite_finali).
- Campagna: `esperimenti/forex-cicli-1.json` (tipo `campagna`: prodotti, lati, barre, uscite per timeframe, rumore, lavoratori).
- Pattern: `motore/pattern.py` (83, dalle librerie di Andrea riscritte in escursioni, divise per strato). Grandezze in `motore/condizioni.py`, traduzione in `motore/uscita.py`.
- Un prodotto entra solo con costi IG e valore del punto in `motore/catalogo.py` (indici e oro 1 €/punto; cambi contratto mini IG da 10.000, confermato da Andrea).

## Regole che valgono sempre

- Soglie di Andrea: 20/30/50 € a trade netti per 1 CFD (fino a 36 ore, 72, oltre), con la volatilità del 2023 ("euro di oggi"); almeno 8 trade l'anno; R² 0,85; 70% di anni positivi.
- Un sistema da provare su ProRealTime deve passare tutto: anche la ricerca rifatta anno per anno (almeno metà del guadagno in-sample), il DSR, la prova sul rumore (al massimo 5%; 50 giri di default in ogni ricerca) e la prova finale.
- Una ricerca o campagna già lanciata non si rilancia con lo stesso nome (la prova finale si usa una volta).

## Risultati finora (2026-11-22)

| Ricerca | Prove | Risultato |
|---|---|---|
| DAX 5 min long a cicli (`dax-long-5m-cicli-8`) | 75.610 | 12 finali da 25-47 € a trade in-sample; rifatti anno per anno 3,7 € a trade; DSR vicino a zero; nessun sistema |
| campagna `forex-cicli-1` (6 cambi, long e short, 15 e 30 minuti) | circa 700.000 | in corso al 22/11 sera; i long finiti non hanno finali; alcuni short hanno finali e fanno la prova sul rumore. Leggere `risultati/campagne/forex-cicli-1/campagna.json` |

## Cosa manca: i tratti dei 5 sistemi eccellenti (`ricerca/cosa-distingue-i-sistemi.md`)

| Tratto | Nella ricerca? |
|---|---|
| soglie in unità di volatilità | sì, tutti i pattern sono in escursioni |
| controllo su un prodotto gemello | sì (gemello e conferma sulle altre valute) |
| uscita a fine finestra, stop dai trade | in parte: uscite a tempo e stop dall'escursione contraria; manca il target |
| una decisione al giorno, poche condizioni | in parte: al massimo 3 condizioni, ma tutte richieste; mancano le **esclusioni** (pattern negati) |
| modello 128: **finestra settimanale** (entra lunedì 03:00, esce mercoledì 22:00) | no: l'ingresso è ogni giorno e l'uscita al massimo dopo 2 giorni; il giorno della settimana è solo un filtro dello strato 3 |
| modello 185: **spostamento forte dall'apertura in escursioni orarie, tenuto 3-4 giorni** | no: le soglie dall'apertura arrivano a 0,3 escursioni giornaliere e le uscite a 2 giorni |
| meccanismo documentato per ogni gamba | no: la forza bruta non lo chiede; si scrive dopo |
| short con soglie più severe sui prodotti che salgono | in parte: i due lati si cercano separati |

Piano dettagliato della prossima sessione in `ricerca/prossima-sessione.md`. Prossimi passi proposti, in quest'ordine: (1) griglia **settimanale** (giorno e ora d'ingresso × giorno e ora d'uscita) nel motore a matrice, il modello del 128; (2) famiglia **185**: spostamento dall'apertura di 2-6 escursioni orarie con uscite di 2-5 giorni e stop in escursioni; (3) esclusioni (pattern negati) nella moltiplicazione; (4) i moduli promossi dei sistemi (`moduli/README.md`) come varianti d'uscita e di gestione nella verifica.
