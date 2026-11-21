# 097 BRK IN – GBP/JPY 30 minuti, long

Sistema su GBP/JPY che compra la rottura del massimo della notte asiatica durante la mattina di Londra, il lunedì e il mercoledì, ed esce la sera stessa. È solo long: lo short dell'originale è spento (`EntraShort = 0`). Il codice viene da una libreria di pattern numerati, come 185 TOP UA 342.

Ricerca sul prodotto (orari, costi IG, letteratura): `fonti/prodotti/gbpjpy.md`.

**Il grafico deve essere a 30 minuti.** L'intestazione dice sia "30min" sia "1H", ma il codice usa le barre delle 03:30 e delle 10:30, che su un grafico orario non esistono: a 1 ora il long non entrerebbe mai.

**Contratto e backtest**: GBP/JPY Mini, 30 minuti, dal 2 agosto 2019 (limite dello storico a 30 minuti), 800.000 ¥. Da confermare: lo spread impostato e quando il sistema è stato costruito (per sapere quale parte del backtest è fuori campione).

**Stato:** prima tornata (M1–M4) senza moduli adottati; M5 e M6 valutati (short di M5 migliore dell'originale, ciclo settimanale confermato su GBP/JPY). Terza tornata: [M7](proposte/M7-short-settimanale-a-orologio.txt) e [M8](proposte/M8-long-inizio-settimana.txt) da lanciare, un tentativo resta per il sistema finale.

## Cosa fa

Orari in ora italiana. `Time` è l'ora di chiusura della barra e gli ordini partono all'apertura della barra successiva.

**Livello.** Alla barra delle 03:30 il sistema memorizza il massimo della giornata fin lì: dall'inizio della giornata di ProRealTime (mezzanotte o le 23:00, da controllare sul grafico) alle 03:30, cioè le 10:30-11:30 di Tokyo. Comprende l'apertura di Tokyo e il fixing delle 09:55 giapponesi.

**Ingresso.** Il lunedì e il mercoledì, alla chiusura della barra delle 10:30 (le 09:30 di Londra, un'ora e mezza dopo l'apertura), piazza un ordine di acquisto stop a quel massimo, valido solo per la mezz'ora successiva. La giornata viene saltata se l'apertura di Londra è stata più calma della mezz'ora precedente: pattern `uptn133`, vero quando l'escursione della barra 09:00-09:30 è meno del 75% di quella 08:30-09:00 e la barra 09:30-10:00 non è più ampia del 10% rispetto alla 09:00-09:30. Il secondo pattern, `uptn027`, è commentato e vale sempre 1.

**Uscita.** Stop allo 0,75%, target al 2%, chiusura alle 22:00. La regola delle 22 barre scatta insieme o dopo quella delle 22:00, perché dall'ingresso alle 22:00 passano 22 o 23 barre. In 11 ore e mezza GBP/JPY si muove in media circa mezzo punto percentuale, quindi lo stop scatta in una minoranza dei trade (stima mia, intorno a uno su cinque, di più nei periodi agitati: da controllare sul report contando i perdenti a −0,75%) e il target quasi mai. È una posizione a tempo con uno stop di media distanza, a metà tra V2 e V3 di `idee/idee-di-trading.md`.

**Taglia** (`Reinvest = 1`, `BuyLotti = 1`): contratti = (6.000 × 0,018% + profitto / prezzo × 0,15%) / (prezzo × 0,75%), con minimo 1 e massimo 80.
- La parte sul capitale vale 1,08 / (prezzo × 0,0075): 0,68 contratti a 212, 1,15 a 125. Quasi sempre scatta il minimo di 1 contratto, che con il mini vale 2.120.000 ¥ di posizione e circa 16.000 ¥ allo stop, l'1,5% di 6.000 €.
- La parte sui profitti vale profitto × 0,2 / prezzo² contratti, cioè ogni yen di profitto aggiunge circa 9 yen di posizione a 212 e 14 a 140: una leva di 9-14 sui profitti contro circa 2 sul capitale. Con l'euro a circa 185 yen, dopo un guadagno pari al capitale iniziale la posizione è di circa 5,6 contratti, leva 5,4 sul capitale raddoppiato, e uno stop costa il 4% del capitale invece dell'1,5%.

## Che tipo di vantaggio ha la gamba

Secondo i principi trasversali di `idee/idee-di-trading.md` è una gamba di **momento intraday**: compra quando la mattina di Londra porta il prezzo sopra il massimo della notte e tiene fino a sera. Le fonti possibili del guadagno sono quattro, e la tornata ne misura tre.

- **Stop accumulati sopra il massimo della notte.** Chi è short dalla sessione asiatica ha lo stop sopra il suo massimo; superarlo fa partire acquisti a catena, con un effetto che dura ore e non giorni (Osler 2003 e 2005, `fonti/prodotti/gbpjpy.md`, A3). È la spiegazione dell'ingresso, non ha un test separato.
- **Momento più forte nei periodi agitati** (A2): M1.
- **Tratto dopo il fixing di Londra.** Tra le 17:00 e le 23:00 GBP/JPY è salito in media di 3,8 punti base al giorno dal 1999 al 2019, perché la sterlina si rafforza sul dollaro e lo yen si indebolisce (A1). Il long tiene quel tratto in ogni trade, indipendentemente dalla rottura: M3.
- **Ciclo settimanale dello yen.** Lunedì e mercoledì stanno dentro la finestra in cui AUDJPY sale (V1): M2.

**Giorni e pattern scelti per ottimizzazione.** Due giorni su cinque e un pattern numerato senza una ragione dichiarata fanno pensare a scelte fatte sul backtest; un backtest costruito così sovrastima il vantaggio (Bailey et al., `fonti/paper/schede.md`). Le regole tecniche intraday sul forex trovate cercando tra molte combinazioni non hanno reso fuori campione (Neely-Weller 2003, A3). Per questo M2 e M4 misurano cosa aggiungono giorni e pattern, invece di raffinarli.

**Rischio di notte nullo.** Il long è chiuso dalle 22:00 alle 10:30, cioè nelle ore dei crolli improvvisi della sterlina (7 ottobre 2016) e dello yen (3 gennaio 2019) (A5). Nessuna modifica di questa tornata allunga la posizione oltre la sera.

## Problemi trovati nel codice

1. **Timeframe**: vedi sopra, solo 30 minuti (o meno).
2. **Ordine stop già superato.** Alle 10:30 il prezzo è spesso già sopra il massimo della notte, perché l'apertura di Londra l'ha superato. L'ordine `BUY ... AT LivelloHigh STOP` è allora dal lato sbagliato del mercato. Il comportamento di ProBacktest in questo caso non è documentato (probabilmente lo esegue all'apertura delle 10:30); in reale, sul forum ProRealCode gli ordini troppo vicini o dal lato sbagliato vengono rifiutati da IG e il sistema si ferma (testimonianze sugli ordini limite, non sugli stop). Se succede, il reale prende meno trade del backtest. C0 ha un interruttore (`IngressoEsplicito`) che in quel caso compra al mercato: un lancio dice se il backtest cambia.
3. **Reinvestimento a leva 9-14 sui profitti**, vedi Taglia. Il capitale (6.000) è in euro, `StrategyProfit` in yen, e la formula divide per il prezzo due volte. L'intestazione standard, in yen, lo sostituisce con una leva unica sul capitale attuale.
4. **Short con il livello del giorno prima** (spento, ma da sapere se il codice short gira altrove): l'ordine parte all'01:00 al minimo `LivelloLow`, che si aggiorna alle 03:30, quindi usa il minimo delle 03:30 del giorno precedente.
5. **Uscita alle 22:00** all'inizio della fascia in cui IG allarga lo spread su GBP/JPY (00:00-21:00 GMT è la fascia normale; se è ora di Londra, le 22:00 italiane ne sono il limite tutto l'anno). Il backtest usa uno spread fisso. Su questo c'è la variante delle 21:00 di M3.
6. **Inizio della giornata.** `DHigh(0)` alle 03:30 dipende da quando ProRealTime fa iniziare la giornata del forex; il lunedì può comprendere o no le barre della domenica sera, e con loro il salto di apertura del weekend. Da controllare con la riga `GRAPH` del livello in C0.
7. **Righe senza effetto**: l'esclusione del 24 giugno 2016 (era un venerdì), la regola delle 22 barre, `StartTrade`/`EndTrade`, `varmax`, `varmin`, `range5d`, `body5d`.
8. **Costi.** Lo spread di IG è circa 3,5 pip nella fascia normale (dato del 2020), cioè 350 ¥ a contratto mini per andata e ritorno, circa il 2% dello stop. Nessun finanziamento: il long chiude prima delle 23:00.

## Prima tornata: C0 e M1–M4

**C0** ([versioni/C0-originale-con-intestazione.txt](versioni/C0-originale-con-intestazione.txt)) è l'originale con l'intestazione standard in yen. **Taglia dei test**: posizione di valore fisso, 2.000.000 ¥ (`Capitale = 1000000`, `Leva = 2`, `Reinvesti = 0`, `ContrattiFissi = 0`), cioè circa 1 contratto mini oggi e 1,6 con il prezzo a 125: ogni stop costa 15.000 ¥ in qualunque anno, mentre a 1 contratto fisso i trade del 2024-2026 peserebbero 1,7 volte quelli del 2016 e del 2020 (lezione dell'oro in `moduli/lezioni.md`).

**Controlli da fare una volta su C0**:
1. `ContrattiFissi = 1`: deve dare gli stessi trade e lo stesso profitto dell'originale con `BuyLotti = 0`.
2. `IngressoEsplicito = 1` (sempre con `ContrattiFissi = 1`): se il risultato è identico, il backtest esegue all'apertura delle 10:30 gli ordini già superati e l'interruttore fa la stessa cosa con un ordine al mercato, che in reale non viene rifiutato; se cambia, il backtest li scarta, e il reale fa lo stesso solo se IG li rifiuta senza fermare il sistema.

**Riferimento comune** dei moduli: lo stesso file con `UsaMx = 0`, che dà i trade di C0. Report long.

| Modulo | Idea | Da dove viene | Direzione dichiarata |
|---|---|---|---|
| [M1](proposte/M1-regime-di-volatilita.txt) | salta i long dei periodi calmi (volatilità di 2 settimane sotto quella di 5 mesi); varianti soglia 0,8 e metà posizione | momento intraday (A2), `moduli/filtro-regime-volatilita.txt` | i long dei periodi calmi guadagnano meno di quelli agitati |
| [M2](proposte/M2-giorni-della-settimana.txt) | aggiunge il martedì; variante solo giovedì e venerdì, per misurarli | ciclo settimanale dello yen (A4, V1) | martedì come lunedì e mercoledì, giovedì e venerdì più deboli; se tutti i giorni rendono uguale, il vantaggio è la rottura |
| [M3](proposte/M3-uscita-e-fixing-di-londra.txt) | uscita alle 17:00, al fixing di Londra; variante alle 21:00 | ritorni attorno ai fixing (A1); spread a fine giornata | uscire alle 17:00 toglie guadagno; alle 21:00 toglie poco |
| [M4](proposte/M4-pattern-apertura-di-londra.txt) | toglie il pattern `uptn133` | principio 4 di `idee/idee-di-trading.md`; partecipazione di Londra | i trade che il pattern scarta guadagnano meno dei tenuti |

M3 non viene dalla libreria: nasce dalla ricerca su sterlina e yen attorno ai fixing. M2 riprende un'idea validata su un altro prodotto (V1) e la usa per capire il tipo di vantaggio.

**Considerate e non proposte.** Taglia legata alla volatilità: prima va visto con M1 se il guadagno per trade cresce con la volatilità, nel qual caso ridurre la taglia nei periodi agitati toglierebbe i trade migliori (lezione M5 di 165 DAX). Prolungare il long nella notte: GBP/JPY scende in media dopo le 23:00 ed entra nelle ore dei crolli improvvisi. Giornate FOMC e BoJ: effetto documentato fino al 2010, servono elenchi di date, pochi trade (H5, H6 di `fonti/prodotti/gbpjpy.md`). Target diverso: il 2% non viene quasi mai raggiunto, e allargare un target già lontano non ha aiutato su 165 DAX (M7).

## Prima tornata: esiti

Numeri e calcoli in `registro-test.md`. C0 non è stato lanciato e Andrea ha confrontato i moduli con l'originale a 1 contratto, che ha una posizione più piccola della taglia dei test fino a che il prezzo è sotto 200; il riferimento è quindi una stima (circa 690.000 ¥, 2.100 ¥ a trade). Il report di M2 manca: gli screenshot 2 e 3 sono lo stesso report di M3.

| Modulo | Esito | Cosa dice sul sistema |
|---|---|---|
| M1 regime | i long dei periodi calmi guadagnano quanto quelli agitati (circa 2.100 ¥), con oscillazioni più piccole; filtro scartato | il long non è momento che vive nella volatilità; la volatilità aggiunge solo dispersione, quindi serve una taglia inversa alla volatilità (H9) |
| M3 uscita 17:00 | −560 ¥ a trade, 2,8 punti base, vicino ai 3,2 previsti; non adottato | il tratto dopo il fixing di Londra rende come documentato; il resto del guadagno (circa 1.540 ¥) è della mattina e del primo pomeriggio |
| M4 pattern | 22 trade aggiunti da circa 400 ¥, troppo pochi per dire; scartato | il pattern resta |
| M2 giorni | report mancante | si misura dentro M5 e M6 |

**Lo short dell'originale** (screenshot 5, lanciato da Andrea): 163 trade, 1.578 ¥ a trade, profit factor 2,09, sei anni positivi su sette e il 2026 a −26.280 ¥. Andrea lo considera sovra-adattato. Le ore in cui lavora (01:00-10:30) sono quelle in cui i cross di carry scendono secondo due studi indipendenti dal sistema (A1, A6 di `fonti/prodotti/gbpjpy.md`), e il suo livello, per un errore del codice, è il minimo asiatico del giorno prima: vende dopo 24 ore di calo. Il 2026 negativo arriva in un anno in cui lo yen si è indebolito nonostante i rialzi della BoJ.

## Seconda tornata: 4 tentativi, M5 e M6 subito

Andrea chiede modifiche più forti o un sistema nuovo, con variabili decimali da ottimizzare in al massimo 1.000-1.500 combinazioni, e 4 tentativi in tutto. Ne uso due subito e tengo gli altri due per quello che diranno i risultati, insieme ai report mancanti (riferimento e M2).

| Tentativo | Cosa è | Da dove viene | Direzione dichiarata |
|---|---|---|---|
| [M5](proposte/M5-giro-dell-orologio.txt) giro dell'orologio | il sistema di Andrea a due lati: short 01:00-10:30 sotto il minimo asiatico di ieri, long 10:30-22:00 sopra il massimo della notte; taglia inversa alla volatilità; giorni dell'originale o tutti; orari e stop da ottimizzare (168 + 150 combinazioni, un lato alla volta) | A1, A6, B5 di `fonti/prodotti/gbpjpy.md`; esito di M1 | taglia a volatilità: drawdown del long più basso a parità di profitto; short positivo e poco legato al long; i giorni aggiunti rendono meno se il ciclo settimanale conta |
| [M6](proposte/M6-ciclo-settimanale-yen.txt) ciclo settimanale dello yen | sistema nuovo: gli orari di 128 BIAS HOUR su GBP/JPY (long lunedì 03:00-mercoledì 22:00, short giovedì 12:00-venerdì 17:00), prima solo calendario, poi con i pattern di 128 | V1 di `idee/idee-di-trading.md` | profit factor sopra 1,3 su entrambi i lati, se il ciclo è dello yen e non del dollaro australiano |

**Perché lo short dentro M5, anche se Andrea non lo sistemerebbe.** Non è una correzione dello short: è la metà della giornata che i due studi sul carry danno come sfavorevole a GBP/JPY, e l'originale aveva già una regola che la sfrutta. Si giudica da solo nel report short; se il 2026 negativo è l'inizio di un cambiamento, lo si vede anche nell'ottimizzazione fino al 2024 con verifica sul 2025-2026.

**Tentativi 3 e 4, da decidere sui risultati.** Se M6 regge, il passo successivo è metterlo accanto al long di 097 BRK con pesi che pareggino i drawdown; se lo short di M5 cede anche fuori campione, M5 diventa solo long con taglia a volatilità e orari ottimizzati; se i giorni aggiunti di M5 rendono come quelli dell'originale, il long passa a tutti i giorni.

## Seconda tornata: esiti (backtest dal 2016)

Numeri in `registro-test.md`. Lo storico a 30 minuti ora parte dal 2 agosto 2016.

| Tentativo | Esito | Cosa dice |
|---|---|---|
| M5 long | stessi 457 trade dell'originale; drawdown −145.500 ¥ contro −84.000 a 1 contratto | la taglia a volatilità non aiuta il long: con uno stop che limita la perdita non serve (H9 non confermata, riferimento mai lanciato) |
| M5 short | profitto / drawdown 15,5 contro 10,0 dell'originale; migliore trade 147.866 ¥ (crollo della sterlina del 7 ottobre 2016), 22% del profitto | la taglia a volatilità aiuta lo short, a tempo e con stop lontano; Andrea lo giudica migliore del suo |
| M6 long | profit factor 1,50, 2.335 ¥ a trade, drawdown −144.600 ¥ | il ciclo settimanale vale per GBP/JPY (H11); troppo drawdown per Andrea |
| M6 short | profit factor 1,32, 1.546 ¥ a trade, drawdown −179.400 ¥, curva diritta | stesso ciclo; Andrea lo trova interessante ma con un guadagno troppo piccolo |
| ingresso esplicito | stessi trade dell'originale | ProBacktest esegue all'apertura gli ordini stop già superati |

## Terza tornata: altri 3 tentativi, M7 e M8 subito

| Tentativo | Cosa è | Direzione dichiarata |
|---|---|---|
| [M7](proposte/M7-short-settimanale-a-orologio.txt) short del fine settimana | short di M6 che entra il giovedì alle 22:00 invece che alle 12:00, con taglia a volatilità; uscita venerdì 17:00 | togliere il pomeriggio e la sera americana del giovedì, in cui GBP/JPY sale in media, alza il guadagno medio di circa 500 ¥ e abbassa il drawdown |
| [M8](proposte/M8-long-inizio-settimana.txt) lato long | modo 1: long di M6 che entra il lunedì alle 13:00 invece che alle 03:00; modo 2: long di rottura di 097 BRK con il martedì aggiunto | modo 1: meno stop presi nella mattina del lunedì, guadagno medio / drawdown più alto di M6; modo 2: il martedì rende come lunedì e mercoledì |

**Il terzo tentativo** è il sistema finale che mette insieme il long migliore tra M8 e 097 BRK, lo short delle 01:00 di M5 e quello del fine settimana di M7, con pesi che pareggino i drawdown dei lati. La settimana ha un posto per ciascuno: long da lunedì a mercoledì, short del giovedì mattina (01:00-10:30) e short dal giovedì sera al venerdì pomeriggio.

## Come leggere i test

- Ogni modulo contro lo stesso file con `UsaMx = 0`, report long. Se la taglia del file è diversa da quella con cui si lancia l'originale, il riferimento va lanciato insieme ai moduli (lezione di questa tornata).
- **Filtri (M1, M4, e M2 per i giorni aggiunti)**: guadagno medio dei trade scartati o aggiunti = differenza di profitto / differenza di numero di trade, confrontato con il guadagno medio di quelli tenuti; l'incertezza si ricava da vincente e perdente medio del report (lezione in `moduli/lezioni.md`).
- **Uscite (M3)**: stessi trade, quindi conta la differenza di guadagno medio; con circa 400 trade una differenza sotto i 500-600 ¥ a trade può essere caso.
- Servono anche, dal report di C0: numero di trade, quanti perdenti escono a −0,75% (stop) e quanti alle 22:00, e se nella lista dei trade gli ingressi delle 10:30 avvengono sopra il livello.

Risultati in `registro-test.md`.
