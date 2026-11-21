# Registro test – 3251 ORAF FDAX 5m (short)

Backtest ProRealTime su **Germany 40 Cash (1 €)** di IG, 5 minuti, dal 21 novembre 2012 al 20 novembre 2026, capitale 10.000 €, report "Posizioni short". Valori letti dagli screenshot di Andrea del 2026-11-21. Spread impostato: da chiedere.

## C0, riferimento della prima tornata (1 contratto)

| Trade | Vincenti | Guadagno medio | Miglior trade | Perdita peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|
| 370 | circa 43% | 16,67 € | 712,70 € | −167,00 € | 2,08 | 6.166,10 € | −861,00 € | 7,16 |

- Circa 26 trade l'anno, cioè uno ogni sei giornate di martedì, giovedì e venerdì.
- Dispersione di un trade, ricostruita da vincente e perdente medio dei moduli (circa +60/+95 € e −45/−55 €, con un terzo dei trade chiusi a pareggio): circa 90 €.

## Prima tornata (M1–M4), contro C0

| Modulo | Trade | Vincenti / perdenti / pareggio | Guadagno medio | Vincente medio | Perdente medio | Miglior trade | Perdita peggiore | Profit factor | Profitto | DD max | Profitto / DD | Durata media |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 solo periodi agitati | 207 | 77 / 54 / 76 | 20,62 € | 93,96 € | −54,92 € | 712,70 € | −167,00 € | circa 2,4 | 4.269,00 € | −490,10 € | 8,71 | 24 barre |
| M2 ingresso alle 15:00 | 370 | 175 / 131 / 64 | 13,08 € | 61,79 € | −45,59 € | 376,20 € | −167,00 € | 1,81 | 4.841,30 € | −485,40 € | 9,97 | 17 barre |
| M3 fino alle 17:25 nelle giornate in calo | 370 | 136 / 115 / 119 | 17,15 € | 92,06 € | −53,70 € | 676,00 € | −167,00 € | 2,03 | 6.345,30 € | −1.038,90 € | 6,11 | 30 barre |
| M4 stop allo 0,65% | 370 | 154 / 119 / 97 | 15,16 € | 75,21 € | −50,19 € | 712,70 € | −124,00 € | 1,94 | 5.609,70 € | −759,50 € | 7,39 | 24 barre |

**Attribuzione degli screenshot.** La terza e la quarta foto sono lo stesso report. È M4 e non M3: la perdita peggiore di −124 € è possibile solo con lo stop in percentuale (0,65% di circa 19.000 punti), mentre M3 tiene gli stessi trade più a lungo con lo stesso stop e non può perdere meno di C0; inoltre i vincenti durano 30 barre come in C0, mentre con M3 quelli delle giornate in calo durerebbero fino a 41. Lo screenshot di M3 è arrivato dopo (riga M3).

- **M1**: i 163 short scartati (periodi calmi) hanno guadagnato 1.897,10 €, cioè 11,64 € a trade, contro i 20,62 € dei tenuti. La differenza va nella direzione prevista (H15) ma vale circa una volta l'incertezza (9 € su circa 9 €): gli short calmi sono positivi. Il drawdown scende del 43% e il profitto del 31%, quindi profitto / drawdown passa da 7,16 a 8,71: parte del drawdown stava nei periodi calmi. Andrea lo scarta perché lascia 207 trade in 14 anni.
- **M2**: l'ora 14:00–15:00 ha reso allo short 1.324,80 €, 3,58 € a trade: il contrario della direzione dichiarata (H16), ma piccolo. Ha portato però quasi metà del rischio: senza quell'ora il drawdown scende da −861 a −485 € (−44%) con il profitto −21%, e profitto / drawdown sale da 7,16 a 9,97. Anche il miglior trade scende da 712,70 a 376,20 €: i movimenti più grandi della finestra arrivano con i dati americani delle 14:30, in tutte e due le direzioni. Promosso da Andrea, che vuole compensare con più contratti: diventa C1.
- **M3**: il tratto 16:35–17:25 nelle giornate in calo ha reso 179 € in tutto, meno di 1 € a trade sui 370, e il drawdown è salito del 21%: profitto / drawdown da 7,16 a 6,11. H17 non confermata. Scartato.
- **M4**: profitto −9%, drawdown −12%, profitto / drawdown 7,39 contro 7,16. Con lo stop di oggi su tutto lo storico il sistema rende meno ma nella stessa proporzione del rischio, cioè lo stop che si stringe con il DAX alto non lo indebolisce. Non adottato: la curva peggiora (Andrea) e non c'è miglioramento da prendere.

## Seconda tornata (M5–M8), contro C1

Riferimento: C1 = C0 + M2, già misurato (riga M2 della tabella sopra), oppure qualunque file della tornata con `UsaMx = 0`.

| Modulo | Lato | Trade | Guadagno medio | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|
| M5 calmi a mezza posizione | short | 370 | 9,97 € (misto 1 e 0,5 contratti) | 3.688,00 € | −462,20 € | 7,98 |
| M6 decisione alle 15:00 | short | 402 | 12,28 € | 4.936,10 € | −665,30 € | 7,42 |
| M7 lato long | long | 720 | 0,60 € | 434,70 € | −1.432,50 € | 0,30 |
| M8 uscita alle 15:55 | short | 370 | 7,18 € | 2.655,00 € | −518,30 € | 5,12 |

- **M5**: dimezzare i calmi ha tolto 1.153 €, quindi in C1 gli short calmi fanno 2.307 € e gli agitati 2.535 €, quasi alla pari. Dopo lo spostamento dell'ingresso alle 15:00 il regime non distingue più: profitto / drawdown da 9,97 a 7,98. Scartato.
- **M6**: decidere alle 15:00 aggiunge 32 trade e porta il drawdown da −485 a −665 €, con gli ultimi anni più deboli (Andrea): profitto / drawdown 7,42. La decisione presa prima dei dati sceglie meglio. Scartato.
- **M7**: il long speculare non ha vantaggio (0,60 € a trade su 720, profit factor 1,03, anni alterni). Direzione dichiarata confermata: il vantaggio dello short non è momento simmetrico ma il calo della finestra pomeridiana.
- **M8**: uscire alle 15:55 toglie 2.186 € (5,9 € a trade) con il drawdown quasi uguale: il tratto 15:55–16:35, con i dati delle 16:00, rende. L'uscita delle 16:35 resta. Scartato.

**Fine del sistema**: versione definitiva = C1 con la console a rischio per trade (`versioni/DEFINITIVO-produzione.txt`).
