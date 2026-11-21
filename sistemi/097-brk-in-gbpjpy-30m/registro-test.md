# Registro test – 097 BRK IN GBPJPY 30m

Backtest ProRealTime, GBP/JPY Mini (10.000 sterline, 100 ¥ per pip), 30 minuti, orari italiani, dal 2 agosto 2019 al 20 novembre 2026 (circa 7 anni e 4 mesi: il limite dello storico a 30 minuti), capitale del backtest 800.000 ¥. Spread impostato: da confermare. `StrategyProfit` e tutti i valori sono in yen. Valori letti dagli screenshot di Andrea del 2026-11-21.

Taglia dei test della prima tornata: posizione di valore fisso, 2.000.000 ¥ (`Capitale = 1000000`, `Leva = 2`, `Reinvesti = 0`, `ContrattiFissi = 0`), cioè circa 15.000 ¥ a stop pieno in ogni trade. Con il prezzo tra 125 e 213 vale tra 1,6 e 0,94 contratti.

## Originale, a 1 contratto

L'originale lanciato da Andrea entra con 1 contratto (perdita peggiore pari a uno stop pieno su 1 contratto), cioè la formula di taglia resta sul minimo.

| Lato | N. trade | Vincenti | Guadagno medio | Vincente medio | Perdente medio | Migliore | Peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| long | 328 | 62% | 1.946,73 ¥ | – | – | 27.010 ¥ | −14.740 ¥ | 2,3 | 638.526,60 ¥ | −48.811 ¥ | 13,1 |
| short (con `EntraShort = 1`) | 163 | 98 (60%) | 1.577,98 ¥ | 5.033,37 ¥ | −3.631,69 ¥ | 22.190 ¥ | −20.840 ¥ | 2,09 | 257.210 ¥ | −43.750 ¥ | 5,9 |

- Long: curva quasi piatta per i primi 100 trade (agosto 2019-fine 2021, circa +40.000 ¥), poi in salita regolare fino alla fine.
- Short: durata 18 barre (01:00-10:30), 3,4% del tempo in mercato. Profitto per anno letto dal grafico a barre: 2019 circa 0, 2020 +48.000, 2021 +35.000, 2022 +28.000, 2023 +98.000, 2024 +42.000, 2025 +31.000, **2026 −26.280 ¥**. Media annua 25.256 ¥. La curva tocca il massimo verso il 145° trade e scende fino alla fine. Andrea lo giudica sovra-adattato. Sei anni positivi su sette, con il 2023 che vale più di un terzo del totale; il 2026 negativo arriva con lo yen debole nonostante i rialzi della BoJ.

## Prima tornata (M1–M4, sopra C0)

**Manca il riferimento.** Andrea ha confrontato i moduli con l'originale a 1 contratto, ma i moduli usano la posizione di valore fisso, più grande dell'originale finché il prezzo è sotto 200 (fino a 1,4 volte nel 2019-2021). C0 con i valori del file non è stato lanciato. Lo stimo pesando la curva dell'originale con il rapporto tra le due taglie anno per anno (1,35 nel 2019-2021, 1,15 nel 2022-2023, 1,0 dopo): **circa 690.000 ¥ di profitto, 2.100 ¥ a trade, 328 trade**, con un'incertezza di qualche decina di migliaia di yen. I confronti qui sotto usano questa stima e vanno rifatti con il report vero.

**Gli screenshot 2 e 3 sono lo stesso report**: stessi numeri, durata media 12 barre, 328 trade. È M3 con uscita alle 17:00 (12 barre = da 10:30-11:00 alle 17:00). Il report di M2 manca.

| Modulo | Variante | Trade | Vincenti | Guadagno medio | Vincente / perdente medio | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|
| C0 (stima) | valore fisso | 328 | – | circa 2.100 ¥ | – | – | circa 690.000 ¥ | – | – |
| M1 regime | soglia 1,0, solo periodi agitati | 121 | 75 (62%) | 2.080,24 ¥ | 7.131 / −6.155 ¥ | 1,89 | 251.708,80 ¥ | −62.021,51 ¥ | 4,1 |
| M3 uscita | 17:00 | 328 | 196 (60%) | 1.539,06 ¥ | 5.383 / −4.169 ¥ | 1,92 | 504.810,90 ¥ | −64.927,20 ¥ | 7,8 |
| M4 pattern | tolto | 350 | 212 (61%) | 1.994,92 ¥ | 6.332 / −4.702 ¥ | 2,08 | 698.221,50 ¥ | −72.916,40 ¥ | 9,6 |

Perdita peggiore in tutti i moduli: circa −14.970/−14.990 ¥, uno stop pieno sulla posizione di valore fisso.

**Interpretazione** (con la stima di C0):
- **M1, regime di volatilità: H1 smentita.** I 207 long dei periodi calmi guadagnano circa (690.000 − 251.700) / 207 ≈ 2.100 ¥ a trade, come i 121 dei periodi agitati (2.080 ¥). Il long non è momento che vive nei periodi agitati. I trade agitati però hanno vincenti e perdenti più grandi (7.131 / −6.155 ¥ contro 6.332 / −4.702 ¥ dell'insieme) e da soli fanno un drawdown di −62.000 ¥ con un terzo dei trade: a parità di guadagno medio, i periodi agitati aggiungono solo oscillazione. È il caso in cui una taglia inversa alla volatilità dovrebbe aiutare (`moduli/taglia-volatilita-uscita-a-tempo.txt`; lezione M8 di 128 BIAS HOUR), il contrario di quanto previsto dalla tornata.
- **M3, uscita alle 17:00: H3 confermata nella direzione.** Stessi 328 trade, guadagno medio da circa 2.100 a 1.539 ¥: il tratto 17:00-22:00 rende circa 560 ¥ a trade, cioè 2,8 punti base su 2.000.000 ¥, vicino ai 3,2 previsti dai ritorni attorno al fixing di Londra (`fonti/prodotti/gbpjpy.md`, A1). Con una dispersione del tratto di circa 6.000 ¥ a trade, l'incertezza sulla differenza è circa 330 ¥: il risultato è al limite del caso, ma va nella direzione dichiarata. Il resto del guadagno, circa 1.540 ¥ a trade, viene dalla mattina e dal primo pomeriggio. Andrea nota il minor tempo in mercato; con un'uscita alle 22:00 il long non paga comunque finanziamento.
- **M4, pattern tolto:** 22 trade aggiunti, che guadagnano circa (698.200 − 690.000) / 22 ≈ 400 ¥ a trade contro 2.100: più deboli, come previsto, ma con 22 trade l'incertezza (circa 1.200 ¥) è più grande della differenza. Andrea lo scarta; il pattern resta.
- **M2: report mancante.**

## Seconda tornata: M5 e M6 (tentativi 1 e 2), backtest dal 2 agosto 2016

Da questa tornata lo storico a 30 minuti parte dal 2 agosto 2016 (10 anni e 4 mesi). Screenshot di Andrea del 2026-11-21. L'originale è a 1 contratto, M5 e M6 a 2.000.000 ¥ di posizione (più grande dell'originale fino al 2020, quando il prezzo era sotto 150). Il riferimento `UsaM5 = 0` non è stato mandato.

| Versione | Lato | Trade | Vincenti | Guadagno medio | Vincente / perdente medio | Migliore | Peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| originale, 1 contratto | long | 457 | 58% | 1.572,08 ¥ | – | 27.010 ¥ | −14.740 ¥ | 1,92 | 718.440,20 ¥ | −84.092,74 ¥ | 8,5 |
| originale, 1 contratto | short | 241 | 60% | 1.810,71 ¥ | – | 72.130 ¥ | −20.840 ¥ | 2,36 | 436.380 ¥ | −43.750 ¥ | 10,0 |
| M5 valori del file | long | 457 | 265 (58%) | 1.859,57 ¥ | 7.163 / −5.489 ¥ | 40.402,80 ¥ | −22.512,80 ¥ | 1,81 | 849.825,40 ¥ | −145.549,78 ¥ | 5,8 |
| M5 valori del file | short | 241 | 144 (60%) | 2.747,44 ¥ | 7.579 / −4.426 ¥ | 147.866,50 ¥ | −22.275 ¥ | 2,54 | 662.132,30 ¥ | −42.762,60 ¥ | 15,5 |
| M6 calendario | long | 529 | 212 (40%) | 2.335,49 ¥ | 17.407 / −7.743 ¥ | 40.000 ¥ | −12.922 ¥ | 1,50 | 1.235.475,90 ¥ | −144.623,95 ¥ | 8,5 |
| M6 calendario | short | 536 | 280 (52%) | 1.545,73 ¥ | 12.373 / −10.290 ¥ circa | 67.637,70 ¥ | −39.990 ¥ | 1,32 | 828.508,80 ¥ | −179.399,40 ¥ | 4,6 |

Profit factor di M5 e M6 ricavati da vincenti e perdenti medi. Durate medie: M5 long 22 barre, M5 short 18, M6 long 77 (38 ore e mezza), M6 short 57 (28 ore e mezza).

- **L'ordine stop già superato viene eseguito dal backtest.** M5 entra al mercato quando il livello è già superato e ha esattamente gli stessi trade dell'originale su entrambi i lati (457 e 241): ProBacktest esegue all'apertura della barra gli ordini stop dal lato sbagliato. `IngressoEsplicito = 1` dà lo stesso backtest ed evita il rifiuto in reale.
- **Long di M5: la taglia a volatilità non aiuta.** Stessi trade, drawdown da −84.000 (1 contratto) a −145.500 ¥; la sola differenza di posizione nel 2016-2020 (circa 1,35 volte) lo porterebbe a circa −115.000. La curva scende nel 2016-2017, anni calmi in cui il fattore arriva a 1,5 e il long perdeva: H9 non confermata, con la riserva che il riferimento non è stato lanciato. È la lezione M2 di 128 BIAS HOUR: con uno stop che limita la perdita, la taglia a volatilità non serve.
- **Short di M5: migliore dell'originale** (giudizio di Andrea): profitto / drawdown 15,5 contro 10,0, drawdown uguale con una posizione più grande. **Il migliore trade vale 147.866 ¥, il 22% del profitto**: è con ogni probabilità il venerdì 7 ottobre 2016, quando la sterlina è crollata alle 01:07 italiane, subito dopo l'ingresso delle 01:00. Senza quel trade lo short fa circa 514.000 ¥ su 240 trade, 2.140 ¥ a trade.
- **M6, ciclo settimanale: H11 confermata, più debole che su AUDJPY.** Con gli orari fissi di 128 BIAS HOUR entrambi i lati superano 1,3 di profit factor (long 1,50, short 1,32; su AUDJPY 2,2 e 1,6). Il long ha la forma di V2: 40% di vincenti, vincente medio più del doppio del perdente, perdenti quasi tutti allo stop. Andrea: short interessante per la curva diritta ma con un guadagno troppo piccolo rispetto al drawdown; long interessante ma 2.300 ¥ a trade con 145.000 ¥ di drawdown sono troppo.

## Decisioni

- 2026-11-21: M1, M3 e M4 non adottati (Andrea: "nulla di interessante"). Andrea chiede ricerche più approfondite e concede 4 tentativi: modifiche forti al suo sistema o un sistema nuovo, con variabili decimali da ottimizzare in al massimo 1.000-1.500 combinazioni. Scritti M5 (giro dell'orologio, sopra il sistema di Andrea) e M6 (ciclo settimanale dello yen, sistema nuovo); M7 e M8 restano da giocare sui risultati.
- 2026-11-21: Andrea giudica M5 long "regge", M5 short migliore del suo, M6 short interessante (curva diritta, ma guadagno troppo piccolo per il drawdown), M6 long interessante ma con troppo drawdown. Concede altri 3 tentativi. Scritti M7 (short di M6 con ingresso giovedì alle 22:00 e taglia a volatilità) e M8 (long lunedì-mercoledì: settimanale con ingresso alle 13:00, oppure rottura ogni giorno con il martedì); il terzo resta per il sistema finale che mette insieme i lati migliori.
