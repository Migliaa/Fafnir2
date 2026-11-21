# Registro test – 138 DAX LSD2H4 1H

Backtest ProRealTime sul Germany 40 Cash (1 €) di IG, 1 ora, orari italiani, dall'8 agosto 2016 al 20 novembre 2026 (l'inizio dipende da `PreLoadBars = 3000`), capitale del backtest 10.000 €. Spread impostato: da chiedere. Valori letti dagli screenshot di Andrea del 2026-11-21.

Taglia dei test: console standard con `Aggressivita = 0`, `CapitaleVersato = 10000`, 900 € di rischio allo stop sullo short (3%) e 1.500 € sul long (5%): posizione da 30.000 € in ogni trade.

## Originale (taglia dell'originale)

Report non ricevuto. Non lanciati neanche il riferimento con `Escludi2022 = 0`, la variante di M1 senza filtro sul lunedì e la variante di M2 con uscita alle 17:00.

## Riferimento dello short (M1/M2/M3 con `UsaMx = 0`)

| N. trade | Vincenti | Guadagno medio | Migliore | Peggiore | Profit factor | Profitto | DD max | Profitto / DD | Durata media |
|---|---|---|---|---|---|---|---|---|---|
| 71 | 59% | 56,07 € | 479,10 € | −315,60 € | 2,64 | 3.980,75 € | −580,20 € | 6,9 | circa 17 ore |

Né lo stop (900 €) né il target (900 €) sono mai scattati: tutti gli short sono usciti alle 21:00. Circa 7 trade l'anno, un po' più della mia stima (5).

## Prima tornata (M1–M4), contro il riferimento

| Modulo | Variante | Trade | Vincenti | Guadagno medio | Vincente / perdente medio | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|
| M1 senza pattern notturno | `TogliNotte = 1` | 286 | 136 (48%) | 10,58 € | 211,37 / −171,48 € | 1,12 | 3.025,08 € | −2.162,21 € | 1,4 |
| **M2 ingresso alle 09:00** | uscita 21:00 | 71 | 43 (61%) | **102,65 €** | 248,86 / −121,88 € | **3,14** | **7.288,37 €** | −810,97 € | **9,0** |
| M3 solo periodi agitati | soglia 1,0 | 27 | 15 (56%) | 133,01 € | 390,17 / −188,45 € | 2,59 | 3.591,16 € | −1.062,20 € | 3,4 |
| M4 long dopo lunedì in forte calo | uscite tonde | 96 | 54 (56%) | 35,80 € | 226,28 / −209,10 € | 1,39 | 3.437,17 € | −2.732,74 € | 1,3 |

- **M1**: i 215 short aggiunti (martedì dopo un lunedì non direzionale, senza il pattern notturno) perdono in media 4,45 € ciascuno, contro 56 € dei tenuti: con una dispersione di circa 190 € a trade la differenza vale circa due volte l'incertezza. Il pattern notturno seleziona; senza, il martedì non ha vantaggio. H9 smentita. Va detto che i 56 € dei tenuti sono misurati sugli stessi dati su cui il pattern è stato scelto, quindi sono probabilmente gonfiati.
- **M2**: stessi 71 trade. Il tratto 04:00-09:00 costava allo short 46,59 € a trade (3.307,62 € in totale): il DAX sale in media nelle ore dell'apertura europea anche dopo un calo notturno. Profit factor da 2,64 a 3,14, profitto quasi raddoppiato, drawdown +40%, profitto / drawdown da 6,9 a 9,0. In reale si aggiunge il risparmio di spread (1,7 punti a contratto). Incertezza del tratto, stimata con una dispersione di circa 180 € in cinque ore: circa 21 € a trade, quindi 46 € sono circa due volte l'incertezza, nella direzione dichiarata prima del test. H11 confermata. **Promosso (C1).**
- **M3**: 27 short dei periodi agitati a 133 € contro circa 9 € dei 44 dei periodi calmi, ma il drawdown sale da 580 a 1.062 €: come su 185 NQ, il filtro toglie profitto senza togliere rischio. Scartato come filtro; dice che lo short è più forte nei periodi agitati, come il momento intraday. **Anomalia da chiarire**: il miglior trade di M3 (898,59 €, target pieno) e il peggiore (−413,44 €) non esistono nel riferimento (migliore 479,10, peggiore −315,60), quindi M3 non ha solo tolto trade. Lo stesso trade da 898,59 € compare in M1, che entra senza pattern notturno. Possibile che il blocco `TIMEFRAME(daily)` cambi il calcolo dei pattern; da verificare con la lista dei trade prima di usare di nuovo un modulo a più timeframe su questo sistema.
- **M4**: curva in salita fino al 50° trade circa (picco intorno a 5.000 €), poi in discesa; dalle barre annuali, circa +4.900 € dal 2016 al 2021 e circa −550 € dal 2022 al 2026. Il riferimento del long (`UsaM4 = 0`) non è stato lanciato. Andrea lo considera rotto e lo scarta. Il recupero del martedì dopo un lunedì di vendite c'era fino al 2021 ed è sparito, come il rialzo all'apertura europea sui futures USA (Boyarchenko et al., aggiornamento 2026). H14 smentita per gli anni recenti.

## Seconda tornata (M5–M7), contro C1 a posizione fissa (71 trade, 102,65 € a trade, 7.288,37 €, DD −810,97 €)

| Modulo | Variante | Trade | Vincenti | Guadagno medio | Vincente / perdente medio | Peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|---|
| M5 tutti i giorni | `GiornoS = 0` | 339 | 163 (48%) | 16,07 € | 209,65 / −163,22 € | −898,87 € | 1,19 | 5.446,65 € | −3.309,75 € | 1,6 |
| M6 uscita alle 17:00 | 170000 | 71 | 42 (59%) | 72,35 € | 215,99 / −135,69 € | −322,88 € | 2,31 | 5.136,51 € | – | – |
| M7 stop all'1,5% | 1.5 | 71 | 40 (56%) | 55,80 € | 223,74 / −160,90 € | −450,08 € | 1,79 | 3.961,90 € | −1.493,72 € | 2,7 |

- **M5**: i 268 short aggiunti negli altri giorni perdono in media 6,87 € ciascuno. Il segnale funziona solo il martedì; martedì e pattern sono stati scelti insieme sugli stessi dati, quindi C1 non ha una conferma indipendente e il suo guadagno medio in reale sarà probabilmente più basso. Scartato.
- **M6**: stessi trade; il tratto 17:00-21:00 rende allo short 30,31 € a trade, molto più del risparmio di spread (1,1 punti a contratto). Anni recenti in perdita secondo Andrea. Il calo prosegue fino alla chiusura americana. Scartato. Variante delle 15:00 non lanciata.
- **M7**: lo stop all'1,5% scatta (peggior trade −450 €, cioè stop pieno) e ferma trade che poi sarebbero tornati: profitto −46%, drawdown +84%, profitto / drawdown da 9,0 a 2,7. Lo stop al 3% resta. Scartato.
- **C1 di produzione** (finestra in alto nello screenshot di M5, se l'ho letta bene: `CapitaleVersato = 3000`, rischio 25%, `Aggressivita = 1`, senza esclusione del 2022): +10.256,84 € dal 2016, 140,50 € a trade (circa 73 trade), drawdown −2.828,40 €, peggior trade −2.563,70 € a posizione cresciuta; tutti gli anni dal 2017 al 2025 positivi, 2026 leggermente negativo.

## Decisioni

- 2026-11-21: sistema ricevuto; prima tornata M1–M4 sopra l'originale (`analisi.md`).
- 2026-11-21: promosso M2 (C1 = originale + ingresso alle 09:00). Scartati M1, M3 e il long (M4). Seconda tornata di tre tentativi sopra C1: M5 (altri giorni della settimana), M6 (uscita alle 17:00), M7 (stop più vicino a parità di posizione).
- 2026-11-21: M5, M6, M7 scartati (Andrea e analisi concordano). **Definitivo: C1** (`versioni/C1-M2-produzione.txt`).
