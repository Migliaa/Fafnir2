# Registro test – 185 TOP UA 342 NQ 1H

Backtest ProRealTime sul US Tech 100 Cash (1 €) di IG, 1 ora, dal 15/2/2016 al 6/2/2026, capitale del backtest 5.000 €. Valori letti dagli screenshot di Andrea del 2026-11-21. Spread impostato: da chiedere.

## Originale (taglia dell'originale, senza reinvestimento), tutte le posizioni

| N. trade | Vincenti | Guadagno medio | Vincente medio | Perdente medio | Miglior trade | Perdita peggiore | Profit factor | Profitto | DD max | Tempo in posizione | Durata media |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 422 | 286 (68%) | 41,05 € | 106,44 € | −96,46 € | 319,25 € | −436,60 € | 2,32 | 17.321,36 € | −772,36 € | 43,15% | 62 barre (vincenti 61, perdenti 64) |

- Profitto / drawdown 22,4. Tutti gli anni positivi: circa 250 € nel 2016, poi tra 800 e 2.200 € l'anno fino al 2024, circa 4.100 € nel 2025, 717 € nel 2026 fino al 6 febbraio. La crescita della posizione dal 2020 (minimo di 0,5 contratti, `analisi.md`) spiega parte del peso degli ultimi anni.
- Nel grafico per durata c'è un gruppo di trade a poco meno di 4 giorni: sono i long del lunedì che escono a tempo il venerdì.
- Il report è su tutte le posizioni: la divisione tra long e short non è nota.

## C0, prima versione (2026-11-20, sbagliata)

| N. trade | Vincenti | Guadagno medio | Vincente medio | Perdente medio | Profit factor | Profitto | DD max | Tempo in posizione |
|---|---|---|---|---|---|---|---|---|
| 421 | 282 (67%) | 40,00 € | 107,31 € | −96,56 € | 2,25 | 16.840,17 € | −772,36 € | 43,4% |

La prima C0 toglieva i limiti di 8 e 4 giorni in posizione, pensando che con barre da 15 minuti non scattassero mai. Sull'1 ora il limite di 4 giorni scatta sugli short aperti il lunedì e su quelli che invertono un long, perché il contatore non riparte quando un long diventa short: escono il venerdì all'01:00 invece che alle 21:00. Toglierlo è costato un trade e 481 €. C0 e le proposte ora tengono il contatore dell'originale e devono riprodurlo esattamente.

## Long su un solo giorno della settimana (ottimizzazione di Andrea, `s1` = giorno)

| Giorno | Trade | Vincenti | Guadagno medio | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|
| lunedì | 128 | 67,97% | 55,02 € | 7.042,89 € | −665,40 € | 10,6 |
| martedì | 134 | 56,72% | 24,34 € | 3.261,76 € | −924,80 € | 3,5 |
| mercoledì | 121 | 57,85% | 27,31 € | 3.304,81 € | −699,25 € | 4,7 |
| giovedì | 113 | 53,98% | 1,45 € | 164,26 € | −1.244,75 € | 0,1 |
| venerdì | 128 | 55,47% | 14,73 € | 1.886,07 € | −739,15 € | 2,6 |

- Da chiarire con Andrea: se l'ottimizzazione è solo long e su quale periodo (128 long del lunedì in dieci anni sono pochi rispetto ai 422 trade del report completo).
- Tutti i long chiudono entro il venerdì alle 21:00, quindi il long del lunedì resta aperto circa 4 giorni, quello del martedì 3,5, del mercoledì 2,5, del giovedì 1,5 e quello del venerdì poche ore.
- **Il lunedì si stacca davvero.** Con una dispersione per trade di circa 100 € (da vincente e perdente medio), l'incertezza sulla differenza tra lunedì e martedì è circa 12 €: 31 € di differenza sono 2,5 volte l'incertezza. Scegliendo il migliore di cinque giorni una parte della differenza è dovuta al caso, ma non tutta.
- **La differenza non dipende dalla durata.** Il long del martedì resta aperto quasi quanto quello del lunedì e guadagna meno della metà. Se i due trade condividono il tratto da martedì a venerdì, il lunedì vale circa 30 € a trade nelle sue prime 24 ore circa, più del resto della settimana: da qui la variante proposta di M1 (uscita il martedì sera).
- I giorni non sono indipendenti tra loro (Andrea): per sapere che cosa aggiungono gli altri giorni al lunedì serve una prova con tutti i giorni insieme (M5, `TuttiIGiorni = 1`), dove i trade in più sono solo quelli aperti quando il lunedì non era in posizione.

## Originale, lato per lato (taglia dell'originale)

| Lato | N. trade | Vincenti | Guadagno medio | Perdita peggiore | Profit factor | Profitto | DD max | Profitto / DD | Tempo in posizione |
|---|---|---|---|---|---|---|---|---|---|
| long | 333 | 68% | 37,42 € | −436,60 € | 2,12 | 12.461,52 € | −685,75 € | 18,2 | 40,04% |
| short | 89 | 67% | 54,60 € | −397,09 € | 3,44 | 4.859,84 € | −669,43 € | 7,3 | 3,11% |

Deviazione standard di un long: 124,27 €. La divisione del report completo (422 trade) è 333 long e 89 short: l'ottimizzazione per giorno con 128 lunedì era quindi su un periodo più corto o con altre impostazioni.

## Riferimento della prima tornata (valore fisso 30.000 €)

Andrea ha confrontato ogni modulo con l'originale, che ha un'altra taglia: in euro i moduli sembrano guadagnare di più nei primi anni e meno negli ultimi solo perché la posizione da 30.000 € pesa ogni anno allo stesso modo. Il riferimento giusto non è stato lanciato, ma si ricava esattamente dai moduli che non toccano un lato: i long di M2 (che cambia solo l'uscita degli short, dopo la finestra dei long) e gli short di M4 (che cambia solo la taglia dei long).

| Lato | N. trade | Vincenti | Guadagno medio | Vincente medio | Perdente medio | Perdita peggiore | Profit factor | Profitto | DD max | Profitto / DD | Durata media |
|---|---|---|---|---|---|---|---|---|---|---|---|
| long (da M2) | 333 | 226 (68%) | 165,16 € | 469,80 € | −478 € | −1.199,72 € | 2,07 | 54.996,89 € | −3.335,28 € | 16,5 | 73 barre |
| short (da M4) | 89 | 60 (67%) | 158,87 € | 334,78 € | −205 € | −1.197,36 € | 3,38 | 14.139,16 € | −2.021,45 € | 7,0 | 21 barre |

Il miglior long vale 750 € e il miglior short 480 €: sono i target (2,5% e 1,6% di 30.000), la perdita peggiore è lo stop al 4%. Dispersione di un trade, ricostruita da vincente e perdente medio più la dispersione dentro i gruppi: circa 500 € sul long, 290 € sullo short.

## Prima tornata (M1–M5), contro il riferimento

| Modulo | Lato | Trade | Guadagno medio | Scartati o aggiunti | Medio scartati o aggiunti | Differenza / incertezza | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|
| M1 uscita martedì 22:00 | long | 333 | 91,13 € | – | tratto da martedì sera a venerdì: 74 € a trade | – | 30.345,37 € | −3.772,11 € | 8,0 |
| M1 | short | 89 | 149,48 € | – | – | – | 13.303,91 € | −2.021,45 € | 6,6 |
| M2 short esce alle 22:00 | short | 89 | 59,79 € | – | dopo la chiusura del primo giorno: 99 € a trade | – | 5.321,61 € | −959,66 € | 5,5 |
| M3 solo periodi agitati | long | 127 | 226,02 € | 206 | 127,6 € | 1,7 | 28.704,62 € | −3.335,28 € | 8,6 |
| M3 | short | 37 | 241,83 € | 52 | 99,8 € | 2,3 | 8.947,79 € | −2.021,45 € | 4,4 |
| M4 taglia del long a volatilità | long | 333 | 160,25 € | – | – | – | 53.362,42 € | −3.111,07 € | 17,2 |
| M5 cambio di mese | long | 451 | 112,96 € | +118 | −34,3 € | – | 50.946,12 € | −4.147,35 € | 12,3 |
| M5 | short | 89 | 145,79 € | – | – | – | 12.975,44 € | −2.040,12 € | 6,4 |

- **M1**: chiudere il long il martedì sera toglie il 45% del profitto con un tratto che vale 74 € a trade, e il drawdown sale invece di scendere: le perdite del long arrivano nei primi giorni e il resto della settimana le recupera. L'idea che il lunedì valesse tutto nelle prime 24 ore, ricavata dai report per giorno, era sbagliata: trade aperti in giorni diversi non si possono scomporre per differenza. Profit factor 1,79 contro 2,07. Scartato. Gli short cambiano (−835 €) perché senza il long aperto non ereditano più i giorni del contatore.
- **M2**: lo short guadagna 60 € nelle ore fino alla chiusura americana e 99 € nei giorni dopo: è momento di più giorni, come lo short dell'oro, non momento intraday. Drawdown dimezzato, ma profitto / drawdown da 7,0 a 5,5. H2 smentita, scartato.
- **M3**: tutte e due le gambe guadagnano di più nei periodi agitati, lo short nella direzione prevista (242 contro 100 €, 2,3 volte l'incertezza), il long al contrario di quanto previsto (226 contro 128 €, 1,7 volte). I trade scartati però sono positivi e il drawdown resta tutto nei periodi agitati: come filtro toglie profitto senza togliere rischio (profitto / drawdown da 16,5 a 8,6 sul long, da 7,0 a 4,4 sullo short). Non adottato; serve per la seconda tornata.
- **M4**: profitto −3%, drawdown −7%, profitto / drawdown da 16,5 a 17,2; la perdita peggiore sale a −1.533 € (posizione più grande nei periodi calmi). Coerente con M3: ridurre la posizione nei periodi agitati toglie i long migliori insieme al rischio. Miglioramento piccolo, dentro il rumore: non adottato.
- **M5**: i 118 long aggiunti nei giorni del cambio di mese perdono in media 34 € e il drawdown sale del 24%. H5 smentita sul long del Nasdaq; il lunedì resta un giorno a parte.

## Seconda tornata (M6–M8), contro il riferimento

| Modulo | Lato | Trade | Guadagno medio | Aggiunti | Medio aggiunti | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|
| M6 short su ogni forte calo agitato | long | 333 | 165,16 € | – | – | 54.996,89 € | −3.335,28 € | 16,5 (identico) |
| M6 | short | 144 | 101,27 € | +55 | 8,1 € | 14.583,48 € | −3.064,37 € | 4,8 |
| M7 long tutti i lunedì (riserva alle 20:00) | long | 503 | 117,53 € | +170 | 24,2 € | 59.116,21 € | −4.471,42 € | 13,2 |
| M7 | short | 90 | 146,82 € | – | – | 13.214,03 € | −2.021,45 € | 6,5 |

- **M6**: i 55 short aggiunti valgono 8 € a trade e il drawdown dello short sale del 52%. Il pattern dell'originale (ieri chiusura nel 20% alto dell'escursione) seleziona davvero: senza, un forte calo agitato non prosegue. Scartato.
- **M7**: i 170 lunedì senza incrocio valgono 24 € a trade prima dei costi, e gli short perdono 925 €. Con quattro notti di finanziamento (circa 24 € a trade su 30.000 €) e lo spread il guadagno sparisce (Andrea). L'incrocio contiene un'informazione: i lunedì in cui il prezzo sale o scende senza pause per tutta la giornata non sono buoni. Scartato.

## M8: reinvestimento a leva 1,5, PesoShort 1,65, tutte le posizioni

| Trade | Vincenti | Guadagno medio | Vincente medio | Perdente medio | Perdita peggiore | Profit factor | Profitto | DD max | Max runup / DD |
|---|---|---|---|---|---|---|---|---|---|
| 422 | 286 (68%) | 493,00 € | 1.220 € | −1.036 € | −8.354,92 € | 2,48 | 208.045 € | −11.821,28 € | 17,61 |

- Da 5.000 a 213.045 € in dieci anni: circa il 46% l'anno composto. Il drawdown in percentuale del capitale non si legge dal report; la perdita peggiore cade alla fine, con il capitale intorno ai 200.000 €. M9 aggiunge la riga `GRAPH` del drawdown in percentuale.
- Andrea vuole di più, soprattutto sui profitti: partire con 1,5 contratti, 2,5 dopo un anno, 4 dopo due, 6 dopo tre, poi assestarsi, con drawdown fino al 20-25%.
- Con leva 1,5 il capitale cresce di circa il 46% l'anno e l'indice (storicamente) del 18%, quindi i contratti crescono di circa il 22% l'anno. Per moltiplicarli per 1,6 l'anno serve una leva di circa 2,6-2,7.

## Decisioni

- 2026-11-21: timeframe 1 ora e contratto US Tech 100 Cash da 1 € (Andrea). C0 corretta: tiene il contatore dei giorni dell'originale.
- 2026-11-21: prima tornata, nessun modulo promosso (Andrea e analisi concordano). Seconda tornata di tre tentativi sopra C0, più audaci su richiesta di Andrea: M6 (più short sui forti cali nei periodi agitati), M7 (long tutti i lunedì), M8 (reinvestimento a leva costante con pesi che pareggiano i drawdown).
- 2026-11-21: seconda tornata: M6 e M7 scartati; M8 funziona ma Andrea lo vuole più aggressivo sui profitti. Terza proposta M9: leva 1,5 sul capitale versato e 4 sui profitti, con un tetto che scende da 3 a 2 quando il capitale passa da 4 a 10 volte quello versato.
- 2026-11-21: M9 lanciato così com'era (con un errore: `Reinvesti = 0` nell'intestazione non spegneva il reinvestimento, perché l'interruttore era `UsaM9`). Drawdown massimo 18% del capitale, dentro il 20-25% accettato da Andrea: **M9 promosso**. Interruttore corretto (ora è `Reinvesti`), versione di produzione `versioni/DEFINITIVO-produzione.txt` = originale + M9.
- 2026-11-21: Andrea abbassa LevaProfitti a 3 nella versione di produzione (capitale 7.200 €).
- 2026-11-21: Andrea trova la gestione a leve (M9) troppo complicata. Produzione riscritta con una console a rischio per trade: % del capitale persa allo stop, 6% sul long e 10% sullo short (stessa esposizione di M8), reinvestimento sì/no, capitale versato 4.200 € e profitti precedenti 3.000 €. `versioni/PROVA-produzione-con-grafici.txt` è la stessa con le righe GRAPH per il backtest.
- 2026-11-21: Andrea vuole una manopola per l'intensità del reinvestimento. `Reinvesti` sostituito da `Aggressivita`: quota dei profitti che entra nel calcolo del rischio (0 nessun reinvestimento, 1 normale, 2 profitti contati doppio); le perdite contano sempre per intero.
