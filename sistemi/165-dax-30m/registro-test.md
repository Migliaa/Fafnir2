# Registro test – 165 DAX 30m

Backtest ProRealTime, Germany 40 Cash (1 €), 30 minuti, dall'11/05/2015 al 20/11/2026, capitale del backtest 5.000 €. Valori letti dagli screenshot di Andrea del 2026-11-20; il numero di trade dei moduli è ricavato da profitto / guadagno medio. Spread impostato nel backtest: non indicato.

L'originale usato da Andrea come riferimento opera sempre 1 contratto (perdita peggiore del long 604 € = stop del 3% con il DAX a circa 20.100), quindi è la versione senza reinvestimento.

## Originale (1 contratto)

| Lato | N. trade | Vincenti | Guadagno medio | Vincente medio | Perdente medio | Perdita peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|---|
| tutti | 1.226 | 668 (54%) | 17,54 € | 93,04 € | −72,84 € | −604,20 € | 1,53 | 21.505,98 € | −1.453,80 € | 14,79 |
| long | 699 | 401 (57%) | 17,14 € | 90,19 € | −81,15 € | −604,20 € | 1,50 | 11.981,33 € | −1.305,32 € | 9,18 |
| short | 527 | 267 (51%) | 18,07 € | 97,33 € | −63,32 € | −256,60 € | 1,58 | 9.524,65 € | −1.377,60 € | 6,93 |

Durata media: long 18 h 17 min, short 6 h 1 min. Il vincente più grande dello short (369,80 €) è il target dell'1,4%, quello del long (693,30 €) il target del 3,5%.

Dispersione di un singolo trade ricostruita da vincente e perdente medio: circa 107 € sul long e 101 € sullo short. Serve a stimare l'incertezza dei confronti qui sotto (colonna "differenza / incertezza": sotto 2 la differenza può essere caso).

## Prima tornata (M1–M5)

### Filtri: trade tenuti contro trade scartati

Trade scartati = originale − modulo, sullo stesso lato (con 1 contratto la sottrazione è esatta, salvo le inversioni short → long delle 13:30).

| Modulo | Lato | Tenuti | Medio tenuti | Scartati | Medio scartati | Differenza / incertezza | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|
| M3 fine mese | short | 429 | 17,23 € | 98 | 21,78 € | −0,4 | 7.390,26 € | −1.191,40 € | 6,23 |
| M4 ampiezza 0,25 | long | 388 | 16,46 € | 311 | 17,99 € | −0,2 | 6.386,54 € | −1.334,32 € | 5,14 |
| M4 ampiezza 0,25 | short | 317 | 21,75 € | 210 | 12,53 € | 1,0 | 6.893,42 € | −1.016,20 € | 6,78 |
| M5 volatilità 1,0 | long | 281 | 23,05 € | 418 | 13,17 € | 1,2 | 6.477,61 € | −1.308,22 € | 4,96 |
| **M5 volatilità 1,0** | **short** | **238** | **31,38 €** | **289** | **7,12 €** | **2,7** | **7.467,45 €** | **−707,50 €** | **10,57** |

- **M3**: gli short a cavallo di fine mese guadagnano un po' più degli altri, non meno. Ipotesi smentita sul DAX; i long non cambiano.
- **M4**: sul long l'ampiezza del movimento della mattina non conta; sullo short va nella direzione prevista ma la differenza è nel margine del caso. Con M4 attivo sui long la perdita peggiore dello short sale da −256,60 a −343,20 €: alcuni short che nell'originale venivano chiusi alle 13:30 dall'inversione verso un long ora restano aperti fino a sera.
- **M5 short**: nei periodi calmi lo short guadagna 7,12 € a trade, meno di quanto costa davvero su IG (spread 1,6 in entrata e 3,8 in uscita alle 19:30). Il filtro dimezza il drawdown e porta il guadagno medio da 18,07 a 31,38 €. Anni in perdita: 2019 e, di poco, 2023.
- **M5 long**: i long nei periodi agitati guadagnano di più (23,05 contro 13,17 €), ma anche quelli calmi sono positivi e tengono regolare la curva; filtrarli lascia lo stesso drawdown con il 54% del profitto.

### Taglia: confronti non validi

| Modulo | Impostazioni | Profitto | Guadagno medio | Perdita peggiore | DD max | Profitto / DD |
|---|---|---|---|---|---|---|
| M1 frazione fissa 5 / 4 | Reinvest 1 | 61.554,81 € | 50,21 € | −2.229,50 € | −5.083,79 € | 12,11 |
| M2 volatilità | InitCapital 60.000, Reinvest 0 | 129.793,74 € | 105,87 € | −3.650,09 € | −10.905,59 € | 11,90 |

Entrambi sono stati confrontati con l'originale a 1 contratto, che ha un'altra taglia: i numeri in euro non si possono mettere a confronto. Quello che se ne ricava:
- **M1**: rischiare il 5% del capitale con uno stop al 3% vuol dire una posizione da 1,7 volte il capitale, meno di quella imposta all'inizio dal contratto minimo (2,3 volte con 5.000 € e il DAX a 11.500). Per questo Andrea lo ha visto reinvestire troppo poco. Si riprova con la taglia espressa direttamente come leva (M8).
- **M2**: non giudicabile da solo, ma M5 mostra che il guadagno per trade cresce con la volatilità molto più del rischio, soprattutto sullo short. Ridurre la taglia nei periodi agitati toglierebbe proprio i trade migliori: scartato.

## Seconda tornata (M6–M9, sopra C1)

Riferimento: C1 a 1 contratto. Il long di C1 è quello dell'originale; per lo short di C1 uso il report short di M5 (stessi trade, salvo le rare inversioni short → long delle 13:30). Andrea ha confrontato con l'originale: i miglioramenti che ha visto su M7 e M9 contengono quello di M5.

| Modulo | Lato | N. trade | Vincenti | Guadagno medio | Perdita peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|
| C1 | long | 699 | 57% | 17,14 € | −604,20 € | 1,50 | 11.981,33 € | −1.305,32 € | 9,18 |
| M6, modo 2 | long | 699 | 63% | 12,32 € | −604,20 € | 1,38 | 8.610,27 € | −1.260,52 € | 6,83 |
| C1 | short | 238 | 57% | 31,38 € | −256,60 € | 2,07 | 7.467,45 € | −707,50 € | 10,57 |
| M7, MoltTP 1 | short | 238 | 56% | 32,05 € | −491,40 € | 1,99 | 7.627,57 € | −907,27 € | 8,42 |
| M9, lunedì | short | 275 | 56% | 30,27 € | −256,60 € | 1,99 | 8.323,92 € | −737,10 € | 11,31 |

- **M6**: chiudere alle 21:30 i long in guadagno toglie 3.371 €: la notte rende anche dopo un pomeriggio in salita, molto più del finanziamento. Ipotesi smentita; il vantaggio del long sta in buona parte nella notte.
- **M7**: rispetto a C1 il profitto sale di 160 € (+2%) e il guadagno medio di 0,67 €, mentre il drawdown sale del 28% e la perdita peggiore passa da −257 a −491 € (un trade che con il target sarebbe uscito in guadagno è tornato indietro). Il vincente più grande sale da 369,80 a 655,90 €. Dopo un calo dell'1,4% in poche ore il DAX in media non prosegue: il target fisso va bene così.
- **M9**: 37 short in più il lunedì, 23,1 € a trade (incertezza circa ±17 €), profitto dello short +11,5%, drawdown +4%, rapporto profitto / drawdown da 10,57 a 11,31. La variante senza la settimana debole non è stata provata.
- **M8**: promosso da Andrea (screenshot non inviato), con le impostazioni del file: leva 3 sul long, 4 sullo short, senza freno.

## Terza tornata (M10–M11, sopra C2 = originale + M5 + M8 + M9)

Riferimento: C2 a 1 contratto. Andrea ha messo accanto l'originale; il long di C2 è uguale all'originale, lo short di C2 è quello di M9.

| Modulo | Lato | N. trade | Vincenti | Guadagno medio | Perdita peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|
| C2 | long | 699 | 57% | 17,14 € | −604,20 € | 1,50 | 11.981,33 € | −1.305,32 € | 9,18 |
| **M11, uscita 09:00** | long | 699 | 58% | 19,08 € | −604,20 € | 1,52 | 13.336,60 € | −1.297,70 € | 10,30 |
| C2 | short | 275 | 56% | 30,27 € | −256,60 € | 1,99 | 8.323,92 € | −737,10 € | 11,31 |
| **M10, soglia 0,5, peso 1** | short | 389 | 55% | 26,29 € | −256,60 € | 1,83 | 10.228,30 € | −860,30 € | 11,90 |

- **M11**: +1.355 € sul long (+11%), +1,94 € a trade, drawdown uguale; le barre annuali sono positive anche dal 2021. Nel reale si aggiunge il risparmio di spread (1,6 punti alle 09:00 contro 3,8 alle 08:00).
- **M10**: 114 short in più nei periodi calmi, 16,7 € a trade (incertezza circa ±9 €), contro 7,12 € di tutti gli short calmi; profitto dello short +23%, drawdown +17%, rapporto profitto / drawdown da 11,31 a 11,90. Il 2023 diventa un anno in perdita di circa 700 € sullo short.

## Decisioni

- 2026-11-20: **M5 promosso sullo short** (versione C1 = originale + M5 sugli short). Scartati M2 e M3. M4 non adottato (effetto sullo short dentro il margine del caso, e in parte coperto da M5). M1 da rifare come M8. M5 sul long non adottato.
- 2026-11-20: promossi M8 e M9. Scartato M6. M7 approvato da Andrea confrontandolo con l'originale; rispetto a C1 non migliora e alza il drawdown, quindi nella versione di produzione resta spento con un interruttore. Versione C2 = originale + M5 + M8 + M9.
- 2026-11-20: promossi M10 e M11. Versione di produzione: `versioni/DEFINITIVO-produzione.txt` = originale + M5 + M8 + M9 + M10 + M11.
