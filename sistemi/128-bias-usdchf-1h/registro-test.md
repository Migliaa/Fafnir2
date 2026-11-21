# Registro test – 128 BIAS USDCHF 1H

Backtest ProRealTime su USD/CHF Mini (10.000 dollari, 1 franco per pip), 1 ora, orari italiani, dal 1° agosto 2014 al 20 novembre 2026, capitale del backtest 10.000 franchi. `StrategyProfit` e tutti i valori in franchi. Spread impostato: da chiedere.

Andrea ha concesso pochi tentativi e modifiche anche non modulari. Tentativi 1 e 2 (M1, M2) scritti il 2026-11-21; dopo i risultati ha concesso altri 2 tentativi (M3, M4).

## Prima tornata, screenshot di Andrea del 2026-11-21

L'originale è stato lanciato senza reinvestimento (`Reinvest = 0`): la taglia è 1 contratto finché il prezzo è sopra 0,90 e 0,9 / prezzo sotto, cioè circa 90 franchi a stop pieno in ogni trade, la stessa taglia di M1 e M2 (90 franchi di rischio). Il riferimento `UsaM1 = 0` non è stato lanciato: l'originale senza reinvestimento ne fa le veci, con una differenza minima (contratto minimo 1 nell'originale, 0,5 in M1).

| Versione | Trade | Vincenti | Guadagno medio | Vincente / perdente medio | Migliore | Peggiore | Profit factor | Profitto | DD max | Profitto / DD |
|---|---|---|---|---|---|---|---|---|---|---|
| originale, short senza reinvestimento | 159 | 96 (60%) | 26,72 | 78,39 / circa −51 | 359,30 | −101,00 | 2,3 | 4.247,84 | −438,20 | 9,7 (max runup / DD 10,44) |
| M1 valori del file (calendario nudo, stop 1,5 escursioni) | 637 | 318 (50%) | 5,47 | 62,81 / −51,69 | 386,87 | −90,00 | circa 1,2 | 3.485,64 | −1.026,99 | 3,4 |
| M2 franco rifugio, short | 375 | 185 (49%) | 2,63 | 55,96 / −49,29 | 223,48 | −89,77 | 1,11 | 987,93 | −891,03 | 1,1 |

Perdente medio dell'originale ricavato dal guadagno medio e dai vincenti. Durata media di M2: 40 barre; tempo in mercato 19,7%.

- Curva dell'originale: salita regolare per circa 135 trade, poi piatta negli ultimi 20-25 (gli ultimi due anni circa).
- Curva di M1: in perdita per i primi 50 trade, poi in salita con oscillazioni ampie.
- Curva di M2: tra −600 e +300 per 330 trade, poi una salita ripida negli ultimi 40 (2025-2026, franco forte).

**Interpretazione**
- **M1 ha cambiato tre cose insieme** (mesi, pattern e stop): non si può dire quale abbia tolto il guadagno. Andrea: «non è la tua versione pulita, cambia tutto». È stato un errore di disegno: la prima prova di un tentativo deve tenere intatta la logica dell'originale e cambiarne una parte sola.
- Quello che M1 dice comunque: ogni mercoledì senza filtri, 637 trade, il ciclo guadagna 5,47 franchi a trade, meno dei circa 6 di spread e finanziamento del reale. L'originale tiene 159 di quei mercoledì e guadagna 26,72 a trade: il vantaggio sta nella selezione (pattern e mesi), non nel giorno. Con una dispersione di circa 65 franchi a trade, la differenza è circa quattro volte la sua incertezza, ma pattern e mesi sono stati scelti sullo stesso storico, quindi la significatività è sopravvalutata (Sullivan-Timmermann-White 2001).
- **M2: H4 non confermata.** Profit factor 1,11 su 375 trade, con tutto il profitto negli ultimi due anni: un forte rialzo del franco in giornata non prosegue in modo stabile. Sul franco la BNS ha frenato gli apprezzamenti per gran parte del periodo (interventi fino al 2022); nel 2025-2026, con il franco lasciato salire, la regola guadagna. Non basta per un sistema.

## Decisioni

- 2026-11-21: M1 e M2 scartati («non ci siamo»). Andrea concede altri 2 tentativi. Scritti M3 (stessa logica dell'originale su altri giorni della settimana) e M4 (stessi trade dell'originale, ingresso dopo il finanziamento triplo, uscita del venerdì e taglia a volatilità), entrambi con `UsaMx = 0` identico all'originale senza reinvestimento.
