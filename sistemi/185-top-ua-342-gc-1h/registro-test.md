# Registro test – 185 TOP UA 342 GC 1H

Backtest ProRealTime, Spot Gold (E1) di IG, contratto da 1 € per punto (1 punto = 1 $ di prezzo dell'oro), 1 ora, dal 3/10/2016 al 20/11/2026, capitale del backtest 3.500 €, spread 0,3 punti, nessuna commissione. Valori letti dagli screenshot di Andrea del 2026-11-20; il numero di trade dei moduli è ricavato da profitto / guadagno medio quando non è scritto.

Il backtest parte dal 2016, quindi l'esclusione di giugno-novembre 2011 non ha alcun effetto (ipotesi H6 senza oggetto).

## Originale con la sua taglia (rischio 4% allo stop, reinvestimento)

| Lato | N. trade | Vincenti | Guadagno medio | Vincente medio | Perdente medio | Perdita peggiore | Profit factor | Profitto | DD max |
|---|---|---|---|---|---|---|---|---|---|
| long | 183 | 85 (46%) | 64,84 € | 315,58 € | −154 € circa | −315,65 € | 1,79 | 11.866,52 € | −1.035,03 € |
| short | 65 | 38 (58%) | 98,61 € | 267,22 € | −138 € circa | −174,42 € | 2,71 | 6.409,62 € | −779,26 € |

- Long: durata media 48 barre (vincenti 73, perdenti 26). Anni 2016, 2017 e 2019 in perdita (circa −400, −50, −200 €), tutti gli altri positivi, dal 2018 tra +400 e +2.600 € l'anno; 2026 +2.209,71 €.
- Short: durata media 42 barre (vincenti 54, perdenti 25). Tutti gli anni positivi; 2026 +710,28 €.
- La perdita peggiore vale circa il 4% del capitale del momento: è uno stop pieno, come previsto dalla formula.
- Andrea vede nella cronologia fino a 20 contratti nei primi anni; dice che oggi la posizione è di circa 0,8-1 contratti. Con 19.000-22.000 € di capitale e il 4% di rischio, 1 contratto vorrebbe dire uno stop di 800-900 punti: va controllato con la riga `GRAPH` dei contratti di C0.

### Short con `EntraLong = 0` (stessa taglia)

| N. trade | Vincenti | Guadagno medio | Vincente medio | Perdita peggiore | Profit factor | Profitto | DD max |
|---|---|---|---|---|---|---|---|
| 64 | 38 (59%) | 88,65 € | 250,51 € | −190,38 € | 2,48 | 5.673,84 € | −845,10 € |

Senza i long i vincenti dello short durano in media 61 barre invece di 54, e spariscono i grandi vincenti chiusi entro il primo giorno che si vedono nel grafico per durata del sistema completo: lo short usa il target dell'ultimo long (H7, molto probabile). Il confronto in euro non è pulito, perché senza i profitti dei long il capitale, e quindi la taglia degli short, è più piccolo; il profit factor (2,71 contro 2,48) non dipende dalla taglia.

## Originale a 1 contratto (riferimento di M1, M2, M3)

| Lato | N. trade | Vincenti | Guadagno medio | Vincente medio | Perdente medio | Perdita peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|---|
| long | 183 | 46% | 12,53 € | – | – | −115,20 € | 2,24 | 2.292,80 € | −421,30 € | 5,44 |
| short | 65 | 58% | 12,87 € | 44,59 € | −31,77 € | −191,30 € | 1,98 | 836,70 € | −507,60 € | 1,65 |

**A 1 contratto il backtest pesa quasi solo gli ultimi anni.** Il 2026 da solo fa 1.109,40 € dei 2.292,80 € del long (48%): l'oro è passato da circa 1.300 a 4.000-5.600 $ e l'escursione oraria in punti è cresciuta molto di più, quindi un trade del 2016 vale pochi euro e uno del 2026 decine. La curva a 1 contratto è esponenziale, quella dell'originale è diritta perché la taglia rende uguale il rischio di ogni trade. Le conclusioni qui sotto sono quindi distorte a favore dei trade dei periodi più cari e agitati; dalla seconda tornata i test si fanno a rischio fisso per trade (C0).

Dispersione di un trade a 1 contratto: circa 45 € su entrambi i lati (ricostruita da vincente e perdente medio, più la dispersione dentro i gruppi). Serve per la colonna "differenza / incertezza": sotto 2 la differenza può essere caso.

## Prima tornata (M1–M3 a 1 contratto; M4 non lanciato)

| Modulo | Lato | Tenuti | Medio tenuti | Scartati | Medio scartati | Differenza / incertezza | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|
| M1 uscita 09:00 | long | 183 | 12,10 € | – | – | stessi trade: −0,43 € a trade | 2.214,20 € | −401,30 € | 5,52 |
| M2 volatilità 1,0 | long | 78 | 18,88 € | 105 | 7,81 € | 1,7 | 1.472,30 € | −256,00 € | 5,75 |
| M2 volatilità 1,0 | short | 28 | 6,98 € | 37 | 17,33 € | −0,9 | 195,50 € | −404,70 € | 0,48 |
| M3 trend 12 mesi | long | 123 | 14,48 € | 60 | 8,53 € | 0,8 | 1.781,10 € | −421,30 € | 4,23 |
| M3 trend 12 mesi | short | 15 | 10,80 € | 50 | 13,49 € | −0,2 | 162,00 € | −138,60 € | 1,17 |

- **M1 long**: uscire alle 09:00 invece che all'01:00 non cambia il risultato (−3% di profitto, drawdown −5%, vincente più grande da 300,60 a 364,40 €). La salita asiatica non si vede nel tratto in più tenuto dal long; H1 non confermata. Il report degli short di M1 non è stato mandato.
- **M2 long**: i long dei periodi agitati guadagnano più del doppio di quelli calmi, nella direzione prevista, ma la differenza è al limite del caso e a 1 contratto i trade agitati valgono di più anche solo per la scala. Togliere 105 trade su 183 lascia una curva con pochi trade: da rimisurare a rischio fisso, come peso e non come filtro (M6).
- **M2 short**: direzione opposta a quella prevista. Gli short dei periodi calmi guadagnano di più (17,33 contro 6,98 €), e a 1 contratto la scala favorirebbe quelli agitati, quindi l'effetto vero potrebbe essere più forte; resta però nel margine del caso, con 65 trade.
- **M3**: gli screenshot indicati come M4 sono di M3, perché il numero di trade cambia (183 → 123 long, 65 → 15 short) e la taglia è di 1 contratto, mentre M4 cambia solo la taglia. Sul long i trade contro il trend guadagnano meno ma sono positivi e il drawdown resta uguale; sullo short il filtro toglie 50 trade su 65 che guadagnavano più dei tenuti. Ipotesi H3 smentita sullo short, non utile sul long.
- **M4** non lanciato: superato dalla scelta di Andrea di tenere la taglia normalizzata dell'originale (C0).

## Seconda tornata (M5–M7 sopra C0)

Andrea ha lanciato i moduli con la taglia del suo originale (rischio 4% allo stop, reinvestimento, 4.000 + 200 €): la perdita peggiore coincide con quella dell'originale. Riferimento: originale con la sua taglia (long 11.866,52 €, DD −1.035,03 €, profitto / DD 11,46; short 6.409,62 €, DD −779,26 €, profitto / DD 8,23). Con il reinvestimento il capitale è comune ai due lati, quindi un modulo su un lato sposta di poco anche l'altro.

| Modulo | Lato | N. trade | Vincenti | Guadagno medio | Vincente / perdente medio | Perdita peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 (short esce alle 21:00 del secondo giorno) | short | 64 | 38 | 91,86 € | 249,08 / −137 € | −174,42 € | – | 5.878,79 € | −853,12 € | 6,89 |
| M6, pesi 0,5 | long | 183 | 85 | 50,71 € | 231,45 / −107 € | −315,65 € | 1,89 | 9.280,81 € | −799,04 € | 11,62 |
| M6, pesi 0,5 | short | 65 | 38 | 76,19 € | 213,96 / −117 € | −160,97 € | 2,56 | 4.952,47 € | −642,83 € | 7,70 |
| M7, leva massima 5 | long | 183 | 85 | 60,46 € | 290,21 / −140 € | −315,65 € | 1,81 | 11.064,23 € | −959,97 € | 11,53 |

- **M1 short**: chiudere lo short prima della terza notte asiatica toglie l'8% del profitto e alza il drawdown del 9%. Insieme a M1 sul long, la salita dell'oro nelle ore asiatiche non si vede in questi trade: H1 e H2 smentite.
- **M6**: sul long profitto e drawdown scendono entrambi del 22-23%, il rapporto resta uguale (11,62 contro 11,46): ridurre i long calmi equivale a ridurre la taglia di tutto il long, e il drawdown più basso viene da pochi episodi. Sullo short il rapporto scende (7,70 contro 8,23): gli short dei periodi agitati rendono quanto gli altri per unità di rischio, quindi l'effetto opposto visto in M2 a 1 contratto era scala o caso. H9 smentita.
- **M7**: il tetto lavora solo nei mesi più calmi e cambia poco: profitto −7%, drawdown −7%, rapporto uguale.
- **M5** (target dello short esplicito): risultato non ricevuto.

## Terza tornata (M8–M12 sopra C0, taglia dell'originale)

Riferimento mostrato insieme ai moduli: long 183 trade, 12.459,21 €, 68,08 € a trade, DD −1.086,96 €, profitto / DD 11,46; short 65 trade, 6.729,92 €, 103,54 € a trade, DD −818,94 €, profitto / DD 8,22. È diverso da quello delle tornate precedenti (11.866,52 e 6.409,62 €) sullo stesso periodo, probabilmente per dati aggiornati: i confronti qui usano questo.

| Modulo | Lato | N. trade | Vincenti | Guadagno medio | Perdita peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|
| M8, 10 barre | long | 187 | 32% | 41,45 € | −331,78 € | 1,54 | 7.750,72 € | −1.880,52 € | 4,12 |
| M8, 10 barre | short | 67 | 45% | 73,62 € | −169,05 € | – | 4.932,66 € | −752,10 € | 6,56 |
| M9, trailing 6 | long | 163 | 37% | 91,26 € | −331,78 € | – | 14.874,95 € | −1.675,41 € | 8,88 |
| M9 (short con target esplicito) | short | 66 | 55% | 96,95 € | −184,31 € | – | 6.398,55 € | −724,98 € | 8,83 |
| M10, soglia 4 | short | 120 | 45% | 38,32 € | −188,58 € | – | 4.598,32 € | −1.721,39 € | 2,67 |
| M11, stop 1,5 giorni | long | 172 | 56% | 40,49 € | −171,74 € | 1,89 | 6.964,17 € | −829,87 € | 8,39 |
| M11, stop 1,5 giorni | short | 66 | 62% | 56,49 € | −169,23 € | – | 3.728,22 € | −539,43 € | 6,91 |
| M12, senza pattern | long | 202 | 43% | 50,38 € | −331,78 € | 1,55 | 10.176,65 € | −1.413,95 € | 7,20 |
| M12, senza pattern | short | 88 | 51% | 75,78 € | −200,47 € | 2,09 | 6.668,83 € | −893,67 € | 7,46 |

- **M8**: uscire alla barra 10 dai trade in perdita taglia soprattutto trade che poi diventano vincenti: i vincenti del long scendono dal 46% al 32% e il drawdown quasi raddoppia. Le rotture dell'oro non partono subito; H11 smentita.
- **M9**: il long a trailing fa più profitto (+19%) con vincenti molto più grandi (massimo 2.969 €), ma il drawdown sale del 54% e il rapporto scende da 11,46 a 8,88; le posizioni durano in media 82 barre. Lo short migliora un poco (8,83 contro 8,22) per il target scritto nel codice e per il capitale diverso: pochi trade cambiati. H12 non confermata.
- **M10**: i 55 short aggiunti perdono in media 38,76 € ciascuno. Il crollo di 5,5 escursioni orarie è una soglia vera: sotto quella i cali dell'oro non proseguono. H13 smentita.
- **M11**: con lo stop più largo i vincenti salgono dal 46% al 56% e il profit factor del long da 1,79 a 1,89, ma con il reinvestimento il profitto si dimezza e il rapporto scende (8,39 e 6,91); le posizioni del long durano 66 barre invece di 48, con più finanziamento. Non adottato.
- **M12**: i 19 long aggiunti senza `uptn104` perdono in media 120 € ciascuno, quindi il pattern contiene informazione (niente long quando la giornata è già tutta sopra il minimo di ieri di oltre l'1%); i 23 short aggiunti senza `uptn139` sono a zero (−2,66 € ciascuno). H15 smentita: i pattern restano.
- Nessuna modifica migliora il rapporto profitto / drawdown dell'originale: in tre tornate le uniche parti che hanno mostrato di contenere informazione sono quelle già presenti (soglia del crollo, pattern `uptn104`, target dello short).

## Decisioni

- 2026-11-20: scartati M1 sul long, M3 su entrambi i lati. M2 non adottato come filtro: si rimisura come peso a rischio fisso (M6). M4 superato da C0. Seconda tornata sopra C0 = originale con l'intestazione standard nella variante a rischio fisso allo stop; i test si fanno con `Reinvesti = 0`, cioè 160 € di rischio per trade.
- 2026-11-21: scartati M1 sullo short, M6 e M7 (rapporto profitto / drawdown uguale o peggiore). Andrea conferma C0 come base e chiede modifiche più forti (cinque), una manopola dell'aggressività e, più avanti, un reinvestimento un po' più aggressivo. Terza tornata M8–M12 sopra C0, lanciata con la taglia dell'originale.
- 2026-11-21: scartati M8–M12. Versione per il reale: `versioni/DEFINITIVO-produzione.txt` = originale con l'intestazione di C0 (rischio allo stop, manopola `Aggressivita`), target dello short scritto nel codice con lo stesso valore che l'originale eredita dal long, senza righe GRAPH.
