# Registro test – 128 BIAS HOUR AUDJPY 1H

Backtest ProRealTime, AUD/JPY Mini 1 ora, dal 19/01/2014 al 20/11/2026, capitale iniziale 800.000 ¥. Valori letti dagli screenshot di Andrea del 2026-11-20. Lo storico non è stato diviso in periodo di scelta e periodo di verifica.

## Prima tornata (M1–M5)

### Solo posizioni long

| Versione | N. trade | Vincenti / perdenti | Guadagno medio | Vincente medio | Perdente medio | Profit factor | Profitto totale | DD max |
|---|---|---|---|---|---|---|---|---|
| originale | 287 | 125 / 162 (44%) | 9.698,74 ¥ | 41.297,96 ¥ | −14.683,37 ¥ | 2,17 | 2.783.538,60 ¥ | −144.791,56 ¥ |
| M4 (soglia 2) | 284 | 124 / 160 (44%) | 9.741,85 ¥ | 41.253,17 ¥ | −14.679,43 ¥ | 2,18 | 2.766.685,50 ¥ | −129.773,96 ¥ |
| M5 (100 giorni) | 150 | 67 / 83 (45%) | 9.961,60 ¥ | 40.272,40 ¥ | −14.506,15 ¥ | 2,24 | 1.494.240,60 ¥ | −132.859,20 ¥ |

Differenza M4 − originale: 3 trade in meno su 287, quindi il miglioramento del drawdown dipende da due sole perdite evitate.

### Sistema completo (long + short), capitale finale

| Versione | Periodo | Capitale finale | Esito |
|---|---|---|---|
| originale | intero storico | circa 4,97 M ¥ | riferimento |
| M3 | intero storico | circa 4,41 M ¥ | peggiore |
| originale / M3 | periodo recente (dal 2022 circa) | circa 1,72 / 1,77 M ¥ | M3 leggermente migliore |
| M1 | intero storico | curva a denti di sega | errore di valuta, test nullo |
| M2 | intero storico | guadagno simile, DD peggiore | scartato |

## Seconda tornata (M6–M8)

Backtest dal 22/01/2015 al 20/11/2026, capitale iniziale 800.000 ¥.

### M6 – sistema completo

| Versione | Periodo | Capitale finale | Esito |
|---|---|---|---|
| originale | recente (dal 2023 circa) | 1,735 M ¥ | riferimento |
| M6 (QuotaReinvestita 1) | recente (dal 2023 circa) | 2,834 M ¥ | promosso; secondo Andrea regolare anche sull'intero storico (screenshot non inviato) |

### M7 – solo posizioni long

| Versione | N. trade | Vincenti / perdenti | Guadagno medio | Profit factor | Profitto totale | Perdita peggiore | DD max | Max runup / DD |
|---|---|---|---|---|---|---|---|---|
| originale | circa 270 (dal grafico) | 44% | circa 10.300 ¥ | 2,25 | 2.770.724,60 ¥ | −15.040,00 ¥ | −144.791,56 ¥ | 19,49 |
| M7 (SogliaR 1, Quota 1) | 412 ordini | 167 / 245 (41%) | 8.665,02 ¥ per ordine | 2,33 | 3.569.987,38 ¥ | −27.498,81 ¥ | −243.188,21 ¥ | 15,05 |

Le circa 140 aggiunte contano come trade separati: per posizione il guadagno medio di M7 è circa 13.200 ¥ (stima con 270 posizioni). Scartato per il drawdown: l'originale ingrandito del 29% darebbe lo stesso profitto con circa 187.000 ¥ di drawdown. Gli short non cambiano, come previsto.

### M8 – solo posizioni short

| Versione | N. trade | Vincenti / perdenti | Guadagno medio | Profit factor | Profitto totale | Perdita peggiore | DD max | Max runup / DD |
|---|---|---|---|---|---|---|---|---|
| originale | 393 | 56% | 3.483,57 ¥ | 1,63 | 1.369.041,60 ¥ | −44.983,40 ¥ | −159.049,90 ¥ | 8,79 |
| M8 | 393 | 219 / 174 (56%) | 3.722,15 ¥ | 1,67 | 1.462.806,10 ¥ | −43.911,60 ¥ | −119.791,30 ¥ | 12,34 |

Promosso. Vincenti e perdenti durano entrambi 29 barre: lo short esce sempre a tempo.

## Terza tornata (M9–M11)

### M9 – solo posizioni long (dal 22/01/2015)

| Versione | N. trade | Guadagno medio | Profit factor | Profitto totale | Perdita peggiore | DD max | Max runup / DD |
|---|---|---|---|---|---|---|---|
| originale | 268 | 10.338,52 ¥ | 2,25 | 2.770.724,60 ¥ | −15.040,00 ¥ | −144.791,56 ¥ | 19,49 |
| M9 (SogliaR 1, 8 barre, Quota 0.5) | 328 ordini (60 aggiunte) | 8.846,42 ¥ per ordine | 2,25 | 2.901.624,86 ¥ | −23.320,93 ¥ | −148.786,76 ¥ | 19,83 |

Per posizione il guadagno medio sale da 10.339 a circa 10.827 ¥ (+4,7%); le 60 aggiunte portano circa 2.200 ¥ ciascuna prima dei costi. Supera di poco il confronto con l'originale ingrandito del 4,7% (DD 151.600 ¥), ma il vantaggio è piccolo e i costi lo riducono ancora. Non adottato; logica da riprovare su altri sistemi.

### M10 – freno sul drawdown sopra C1

Promosso da Andrea (screenshot non inviato). Entra nella versione di produzione.

### M11 sperimentale – solo posizioni long

| Versione | Capitale finale |
|---|---|
| originale | 3,635 M ¥ |
| M11 (ApplicaLong) | 2,568 M ¥ |

Il filtro toglie molto profitto: l'ipotesi del ciclo settimanale non regge sul long. Scartato.

## Decisioni

- 2026-11-20: scartati M2, M3, M5. M1 da rifare (M6). M4 tenuto in sospeso: effetto su 3 trade.
- 2026-11-20: promossi M6 e M8 (in `moduli/`). Scartato M7. Versione combinata C1 = originale + M4 + M6 + M8.
- 2026-11-20: promosso M10. Scartati M9 (vantaggio troppo piccolo rispetto ai costi) e M11. In produzione: `versioni/DEFINITIVO-produzione.txt` = originale + M4 + M6 + M8 + M10.
