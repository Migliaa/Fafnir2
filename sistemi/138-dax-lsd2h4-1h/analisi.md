# 138 DAX LSD2H4 – DAX, 1 ora

Sistema sul Germany 40 Cash da 1 € di IG (profitti e `StrategyProfit` in euro), grafico a 1 ora come dicono il nome e il commento sull'ATR, con un solo trade possibile a settimana: il martedì dalle 04:00 alle 21:00. Andrea usa solo lo short; il long, spento, gli sembra sovra-adattato e preferisce tenere il DAX direttamente. I nomi dei pattern (`uptn141`, `uptn008`, `bptns08`) vengono dalla stessa libreria numerata di [185 oro](../185-top-ua-342-gc-1h/analisi.md) e [097 BRK](../097-brk-in-gbpjpy-30m/analisi.md).

Ricerca sul prodotto: `fonti/prodotti/dax.md`, con la sezione aggiunta per questo sistema (ore notturne dei futures, giorni della settimana, inversione da un giorno all'altro).

**Da chiedere ad Andrea**: il report dello short dell'originale (trade, vincenti, guadagno medio, profit factor, drawdown), il periodo del backtest, lo spread impostato, quando è stato costruito il sistema (per sapere quale parte del backtest è fuori campione) e, se c'è, il report del long.

**Stato:** definitivo [C1](versioni/C1-M2-produzione.txt) = originale + M2 (ingresso alle 09:00), con la console a rischio per trade. Sette moduli provati, uno promosso; il long è scartato.

## Cosa fa

Orari in ora italiana. `Time` è l'ora di chiusura della barra e gli ordini partono all'apertura della barra successiva.

**Short.** Il martedì, alla chiusura della barra 03:00-04:00, vende se valgono tre condizioni:
- la barra 01:00-02:00 ha chiuso in salita e la 02:00-03:00 in discesa (`uptn141`);
- il minimo della barra 03:00-04:00 è sceso sotto l'apertura delle 02:00 meno il 30% dell'escursione della barra 02:00-03:00 (`bptns08`). Se la barra 02:00-03:00 ha un corpo di almeno il 30% della sua escursione, la condizione è vera già all'apertura della barra successiva: aggiunge poco a `uptn141`;
- il lunedì non è stato direzionale: corpo della candela giornaliera non oltre metà dell'escursione (`not uptn008`), in salita o in discesa.

Esce alle 21:00 del martedì. Stop al 3%, target al 3%; se il guadagno arriva al 2,5% lo stop va al prezzo d'ingresso, se la perdita arriva al 2,5% ci va il target. In 17 ore il DAX si muove del 3% solo nei giorni di crollo o di forte rialzo, quindi **lo short esce quasi sempre a orario**: è un trade di una giornata con stop di emergenza. Stima mia, da verificare sul report: circa 5 trade l'anno, una cinquantina in dieci anni.

**Long (spento).** Compra ogni martedì alle 04:00 senza altre condizioni ed esce alle 21:00; stop al 5%, target all'1,5%, stop all'ingresso dopo un guadagno dell'1,1%, target all'ingresso dopo una perdita del 2,5%. I valori 1,1 e 1,5 sono gli unici non tondi del codice.

**Taglia.** Con `Reinvest = 0`: contratti = 14% di 3.000 € / (prezzo × 3%) = 420 € di rischio allo stop, con minimo 1 e massimo 80. Il minimo scatta quando il DAX supera 14.000, cioè quasi sempre dal 2021: oggi, con il DAX a circa 26.700, lo short entra con 1 contratto (posizione da 26.700 €) e uno stop costa circa 800 €, il 27% di 3.000 invece del 14%.

## Che tipo di vantaggio hanno le gambe

Secondo i principi trasversali di `idee/idee-di-trading.md`.

- **Short: non documentato.** Sul DAX non ho trovato prove di un martedì negativo, e l'effetto lunedì è sparito dal 2000 (Miss et al. 2020). Il pattern notturno guarda un mercato quasi vuoto: nelle ore asiatiche l'FDAX scambia circa il 2,6% dei contratti della giornata (Eurex, 2024), con lo spread IG a 5 punti. Il filtro sul lunedì non ha una ragione dichiarata. Le letture possibili sono due: **calendario** (il martedì, selezionato dall'ottimizzazione) o **momento intraday** (il calo notturno prosegue durante la giornata). La tornata le distingue con i due test che costano poco: quanto rendono i tratti della posizione (M2) e quanto rendono i periodi agitati rispetto ai calmi (M3). Prima ancora va misurato se i pattern selezionano qualcosa (M1).
- **Long: esposizione al DAX** un giorno a settimana, con uscite da valori ottimizzati: Andrea ha ragione. Il modo per dargli una logica è condizionarlo a un motivo per cui quel martedì dovrebbe salire: dopo un lunedì di forti vendite (inversione da un giorno all'altro, rialzo all'apertura europea dopo le vendite; `fonti/prodotti/dax.md`, H14). Sul DAX la prova è debole, perché l'inversione media da un giorno all'altro è vicina a zero (Baltussen et al. 2019): se c'è, sta nei giorni di movimento grande (M4).

## Problemi trovati nel codice

1. **Rischio reale doppio di quello scritto**, per il minimo di 1 contratto (vedi Taglia). La console standard lo rende esplicito: con l'indice a questi livelli 1 contratto è la taglia minima, e il rischio va scelto sapendolo.
2. **Reinvestimento**: con `Reinvest = 1` ogni euro di profitto rischia il 28% (14% × 2), il doppio del capitale. È spento; la console lo sostituisce con la manopola `Aggressivita`.
3. **Esclusione di aprile e luglio 2022.** Toglie dal backtest otto martedì, probabilmente con perdite grandi. In reale non ha effetto, perché le date sono passate: serve solo ad abbellire il backtest. Le proposte la tengono (`Escludi2022 = 1`) per riprodurre l'originale, ma il riferimento va lanciato anche con `Escludi2022 = 0`, per sapere quanto nasconde.
4. **Il pattern notturno cambia significato con le stagioni e con gli anni.** I futures aprono all'01:10 d'inverno e alle 02:10 d'estate (orario di Singapore, senza ora legale): la barra 01:00-02:00 contiene l'apertura solo d'inverno. Prima del 10 dicembre 2018 di notte i futures erano chiusi e le barre di IG non avevano un mercato dietro.
5. **Costi non visti dal backtest.** Lo short entra alle 04:00 con lo spread IG a 5 punti ed esce alle 21:00 con 3,8: circa 4,4 punti a contratto tra andata e ritorno, contro 1,6 per un trade dentro l'orario di Xetra (09:00-17:30) e 2,7 per lo short di 165 DAX. Nessun finanziamento: chiude prima delle 23:00.
6. **Regole che non scattano.** L'uscita dopo 17 barre arriva alle 23:00, dopo quella delle 21:00; l'uscita "giorno diverso dal martedì" scatta solo se manca la barra delle 21:00. Inutilizzati il blocco di stop e target legati all'ATR, `BuyLot`, `TagliaPosizione`, i pattern del long (`bptnl08`, `uptn137`, `uptn003`).
7. **Candela giornaliera.** `uptn008` usa apertura e chiusura del lunedì secondo la candela giornaliera di ProRealTime per IG, che comprende anche le ore notturne (da controllare sul grafico da che ora parte).
8. **Sovrapposizione con 165 DAX.** Lo short di 165 DAX entra alle 12:30 da martedì a venerdì: alcuni martedì i due sistemi sono short insieme. Va tenuto presente quando si sceglie il rischio per il reale.
9. **Long e short sulla stessa barra.** Con entrambi accesi l'originale manda `BUY` e `SELLSHORT` alla stessa barra delle 04:00 quando lo short ha il segnale. Con M4 non può succedere: il long richiede un lunedì direzionale, lo short lo esclude.

## Prima tornata: M1–M4

**Riferimento dello short**: M1, M2 o M3 con `UsaMx = 0` (danno gli stessi trade dell'originale con la taglia del test). **Riferimento del long**: M4 con `UsaM4 = 0`, il long dell'originale. **Taglia dei test**: console standard con `Aggressivita = 0` e rischio fisso, 900 € allo stop sullo short (3%) e 1.500 € sul long (5%), cioè una posizione da 30.000 € in ogni trade: 3 contratti con il DAX a 10.000, 1,1 a 27.000. Ogni anno pesa allo stesso modo e il minimo di 1 contratto non scatta mai. Tutte le proposte hanno `DEFPARAM PreLoadBars = 3000` per la volatilità giornaliera di M3, quindi il backtest può partire qualche mese dopo quello dell'originale, ma è lo stesso in tutti i file.

[C0](versioni/C0-originale-con-console.txt) è l'originale con la console e la sua taglia (rischio 14% di 3.000 €, minimo 1 contratto): deve dare gli stessi numeri dell'originale ed è la base per le versioni combinate.

| Modulo | Idea | Lato | Da dove viene |
|---|---|---|---|
| [M1](proposte/M1-pattern-notturno-e-lunedi.txt) | short senza il pattern notturno; variante senza il filtro sul lunedì | short | ore asiatiche quasi vuote, spread notturno (H9, H10); lezione di 185 oro M12: un pattern va tolto e misurato prima di giudicarlo |
| [M2](proposte/M2-ingresso-alle-9.txt) | ingresso alle 09:00; variante uscita alle 17:00 | short | rialzo all'apertura europea (Boyarchenko et al. 2023; 165 DAX M11), spread IG per fascia oraria (H11, H12) |
| [M3](proposte/M3-regime-di-volatilita.txt) | solo periodi agitati | short | momento intraday (H13); `moduli/filtro-regime-volatilita.txt` (165 DAX M5) |
| [M4](proposte/M4-long-dopo-lunedi-in-calo.txt) | long solo dopo un lunedì in forte calo, uscite tonde; variante con le uscite originali | long | inversione dopo le vendite (Baltussen et al. 2019; Boyarchenko et al. 2023; H14) |

M1, M2 e M4 non vengono dalla libreria. M3 è un modulo validato su un altro sistema, qui proposto come misura.

## Come leggere i test

- Con circa 50 trade le differenze tra gruppi sono quasi sempre dentro il caso. Uno short tenuto 17 ore con una posizione da 30.000 € oscilla di circa 300 € (stima con un'escursione giornaliera dell'1-1,2%): su 50 trade l'incertezza del guadagno medio è circa 45 €, e tra due gruppi da 25 l'incertezza della differenza è circa 85 €, quindi solo differenze sopra i 150-170 € non sono probabilmente caso. Per questo M1 aggiunge trade, M2 confronta gli stessi trade e M3 serve più a capire il tipo di vantaggio che a filtrare.
- **M1 e M4 (trade aggiunti o scartati)**: guadagno medio dei trade aggiunti o scartati = differenza di profitto / differenza di trade, confrontato con quello del riferimento.
- **M2 (stessi trade)**: la differenza di profitto divisa per il numero di trade è quanto rende a trade il tratto tolto; a questo si aggiunge in reale il risparmio di spread (1,7 punti a contratto entrando alle 09:00, 1,1 uscendo alle 17:00).
- **M3**: guadagno medio degli scartati contro quello dei tenuti, e se il drawdown scende più del profitto.
- Ogni modulo va letto anche per anni: un miglioramento fatto da uno o due anni non è una prova.

## Prima tornata: esiti

Riferimento a posizione fissa da 30.000 €: 71 short dal 2016, 56,07 € a trade, profit factor 2,64, drawdown −580 €; nessuno stop e nessun target scattato. Numeri in `registro-test.md`.

| Modulo | Esito |
|---|---|
| M1 senza pattern notturno | i 215 short aggiunti perdono 4 € a trade: il pattern seleziona, senza il martedì non rende. Scartato |
| **M2 ingresso alle 09:00** | **stessi trade, +46,59 € a trade: il tratto 04:00-09:00 andava contro lo short. Profit factor 3,14, profitto / drawdown da 6,9 a 9,0. Promosso (C1)** |
| M3 solo periodi agitati | 133 € a trade contro 9 € dei calmi, ma drawdown quasi doppio con 27 trade: scartato come filtro. Contiene un'anomalia (trade che non sono nel riferimento) |
| M4 long dopo lunedì in calo | positivo fino al 2021, negativo dopo: scartato insieme al long |

**Cosa dice sul tipo di vantaggio.** Lo short vende una pressione in vendita vista nella notte, ma solo dopo il rialzo dell'apertura europea, che sul DAX c'è ancora (M2, come M11 di 165 DAX); nei periodi agitati rende di più, come una gamba di momento intraday (M3). Il martedì non ha una ragione documentata e il pattern è stato scelto sugli stessi dati: i 102 € a trade di C1 sono probabilmente più alti di quelli che il sistema darà in reale.

## Seconda tornata: M5–M7, sopra C1

Andrea ha chiesto tre tentativi per preparare il definitivo, anche per aumentare il numero di trade. Riferimento comune: C1 a posizione fissa, cioè M2 della prima tornata (71 trade, 7.288,37 €, drawdown −810,97 €); ogni file con `UsaMx = 0` deve riprodurlo.

| Modulo | Idea | Da dove viene |
|---|---|---|
| [M5](proposte/M5-tutti-i-giorni.txt) | lo stesso segnale da lunedì a venerdì; con un'ottimizzazione di `GiornoS` da 0 a 5 si vede ogni giorno | M1 (il vantaggio è nel pattern), nessuna prova di un martedì speciale sul DAX |
| [M6](proposte/M6-uscita-alle-17.txt) | uscita alle 17:00 con lo spread di Xetra; variante alle 15:00, prima dell'apertura americana | momento intraday fino alla chiusura, spread IG per fascia oraria |
| [M7](proposte/M7-stop-piu-vicino.txt) | stop all'1,5% invece del 3% con la stessa posizione; variante 2% | lo stop non è mai scattato ma decide il rischio scritto; Kaminski-Lo 2014 sul costo degli stop |

**Timeframe diverso: non proposto in questa tornata.** M1 ha mostrato che la selezione sta nel pattern delle barre orarie notturne: su barre da 30 minuti le stesse condizioni diventano un altro pattern, misurato su barre ancora più vuote, cioè un sistema nuovo da ottimizzare da capo. Aumentare i giorni (M5) aumenta i trade senza cambiare il segnale.

## Seconda tornata: esiti

| Modulo | Esito |
|---|---|
| M5 tutti i giorni | i 268 short degli altri giorni perdono 6,87 € a trade: il segnale vale solo il martedì. Scartato |
| M6 uscita alle 17:00 | la sera rende 30 € a trade allo short, gli anni recenti peggiorano. Scartato |
| M7 stop all'1,5% | ferma trade che poi tornano: profitto −46%, drawdown +84%. Scartato |

**Cosa resta.** Lo short guadagna dall'apertura di Xetra alle 21:00 e ha bisogno di uno stop lontano: il calo prosegue nella seduta americana dopo aver oscillato. Il limite è che martedì e pattern notturno sono stati scelti insieme sugli stessi dati e nessun test li ha confermati in modo indipendente (M1 e M5 dicono solo che fuori da quella combinazione non c'è niente): in reale conviene aspettarsi un guadagno per trade sotto i 103 € del backtest e controllare i primi 15-20 trade.

Risultati in `registro-test.md`.
