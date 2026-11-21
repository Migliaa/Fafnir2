# Cosa distingue i sistemi eccellenti

Confronto del 2026-11-21 tra i cinque sistemi che Andrea considera eccellenti (128 AUDJPY, 165 DAX, 185 NQ, 185 oro, 3251 FDAX) e i sistemi della cartella `G:\My Drive\Andrea\ProRealTime\2025 - PTF Stabile`, che usano gli stessi modelli su altri prodotti (128 BIAS HOUR su dieci cambi e sull'oro, 185 TOP UA su Dow Jones e GBP/JPY, 097 BRK su oro e USD/JPY, tre sistemi sul petrolio, 178 MINSTOP DAX).

**Attendibilità.** Per i cinque eccellenti ci sono i backtest e i test dei moduli (`sistemi/*/registro-test.md`). Dei sistemi mediocri ho solo il codice e il giudizio di Andrea: le differenze qui sotto sono lette nel codice e vanno confermate con i report. Il registro dei trade reali (2024-2026) è una sola misura di due anni, con taglie e valute diverse.

## I cinque sistemi in una tabella

| Sistema | Lato | Quando entra | Condizione | Uscita | Stop | Vantaggio |
|---|---|---|---|---|---|---|
| 128 AUDJPY 1H | long | lunedì 03:00 | nessuna, due esclusioni | mercoledì 22:00 | 0,4%, circa mezza escursione giornaliera | ciclo settimanale dello yen (V1, V2) |
| | short | giovedì 12:00 | nessuna, due esclusioni | venerdì 18:00 | 2%, d'emergenza | stesso ciclo (V3) |
| 165 DAX 30m | short | 12:30, martedì-venerdì | sotto la media esponenziale di 25 barre e minimo di ieri non sopra quello di 5 giorni prima | dopo 7 ore, target 1,4% | 2,5% | momento intraday (V4) |
| | long | 13:30, lunedì-giovedì | sopra la media e RSI a 2 periodi sopra 65 | 09:00 del giorno dopo | 3% | premio notturno (V5) |
| 185 NQ 1H | long | lunedì 08:00-20:00 | media di 5 barre incrocia sopra quella di 10 | 90 barre o venerdì 21:00, target 2,5% | 4% | non misurato |
| | short | 16:00-20:00 | sotto l'apertura di 4 escursioni orarie medie, dopo una chiusura forte ieri | 100 barre o 4 giorni, target 1,6% | 4% | prosecuzione per giorni (P4) |
| 185 oro 1H | long | 11:00-22:00 | sopra l'apertura di 2,5 escursioni orarie medie e nuovo massimo; una esclusione | 3-4 giorni | 3 escursioni medie | prosecuzione per giorni (V6) |
| | short | 11:00-22:00 | sotto l'apertura di 5,5 escursioni e nuovo minimo; una esclusione | 60 barre | 3 escursioni medie | stesso |
| 3251 FDAX 5m | short | decide alle 14:00, entra alle 15:00, martedì, giovedì, venerdì | 0,5% sotto il massimo della seduta, non sotto il minimo di ieri | 16:35 | 167 punti, poi pareggio | apertura americana (V7 DAX) |

## Sei tratti comuni

**1. Ogni gamba ha un orario o un evento con un meccanismo documentato**, tranne il long del Nasdaq, il cui ruolo del lunedì non è mai stato misurato: il ciclo settimanale dello yen confermato su GBP/JPY con gli stessi orari e senza pattern, le coperture gamma che fanno proseguire il movimento della giornata, il premio notturno all'apertura europea, il calo dei futures americani all'apertura di New York. Le finestre dei 128 BIAS mediocri invece non hanno un meccanismo conosciuto (CAD/CHF dal venerdì 19:00 al mercoledì 13:00, USD/CZK mercoledì 07:00-14:00, EUR/SGD), e quella di EUR/JPY tiene il long dal lunedì al giovedì e lo short dal giovedì al lunedì, cioè è sempre in mercato e scommette sulla forma dell'intera settimana.

**2. I vantaggi sono di due sole famiglie**, e sono i due modelli da riciclare:
- *finestra di calendario o d'orario*: 128 AUDJPY, le due gambe di 165 DAX, 3251 FDAX;
- *spostamento forte dall'apertura della giornata, misurato in escursioni medie, tenuto per giorni*: lo short di 185 NQ e le due gambe di 185 oro. I test hanno mostrato che non è momento intraday: lo short del Nasdaq guadagna più nei giorni dopo che nella seduta (M2), e l'oro peggiora con uscite più rapide (M8).

**3. Una decisione al giorno, poche condizioni, filtri che escludono invece di richiedere.** 128 AUDJPY ha quattro pattern e sono tutte esclusioni (`PtnMRLY = 1`, `PtnUNMRLY = 1`), che tolgono pochi trade a un vantaggio che c'è già senza di loro; 165 DAX ha una condizione per lato. Nei mediocri le condizioni si accumulano: 159 CRUDE combina due pattern, due indicatori su tre timeframe e sei regole d'uscita (ore precise con la posizione in perdita, venerdì, espansione della volatilità giornaliera); 178 MINSTOP DAX usa volatilità settimanale, bande PRT, volatilità e movimento direzionale giornalieri; 128 AUDUSD apre lo short solo se l'escursione di oggi è sotto lo 0,2%. Ogni condizione scelta sul backtest è un grado di libertà che il sistema spende per adattarsi al passato.

**4. L'uscita sta alla fine della finestra, e lo stop è o stretto o d'emergenza.** Il long di AUDJPY perde lo stop pieno presto e i vincenti, tenuti fino al mercoledì, guadagnano 2,75 volte lo stop (V2). Nei 128 mediocri lo stop sui cambi è del 3,5-8% (CAD/CHF 3,5%, EUR/JPY 4,5%, CHF/JPY 8% sul long), cioè non c'è, e alcuni target sono più vicini dello stop (AUD/USD 1,1% contro 1,3%; USD/CAD 1% contro 1,6%): il risultato dipende allora solo dalla percentuale di vincenti, senza l'asimmetria che rende robusto AUDJPY.

**5. Le soglie sono in unità di volatilità.** 185 misura il movimento in escursioni orarie medie e lo stop dell'oro in escursioni delle ultime 20 ore, quindi la stessa regola vale nel 2016 e nel 2026 e su prodotti diversi. Le librerie di pattern usano invece soglie percentuali fisse (0,5%, 1%, 2%), che su EUR/USD e sul Nasdaq, o sull'oro a 1.300 e a 4.000 dollari, descrivono giornate diverse; 3251 ha lo stop in punti, che oggi vale un terzo di quello del 2016 (problema 2 della sua analisi).

**6. Sui prodotti che salgono nel lungo periodo lo short aspetta un evento raro.** Sull'oro il long entra con 2,5 escursioni e lo short con 5,5, e abbassare la soglia dello short a 4 ha aggiunto trade in perdita (S9); sul Nasdaq lo short chiede 4 escursioni più una chiusura forte il giorno prima, e senza la chiusura forte lo stesso calo non rende (M6). Lo stesso modello su Dow Jones e GBP/JPY ha soglie asimmetriche anche lì, ma stop al 9% e al 5% e un pattern del long sul Dow (`uptn092`, massimo di oggi minore di zero) che è sempre falso.

## Cosa dice il registro dei trade reali

Il file `Analisi\TradeBreakDown-(31-12-2023_2300)-(26-01-2026_2259).csv` contiene circa 1.100 trade chiusi su IG tra gennaio 2024 e gennaio 2026. La correlazione dei profitti giornalieri tra strumenti è vicina a zero per tutte le coppie (la più alta +0,25 tra Nasdaq e GBP/JPY, la più bassa −0,17 tra EUR/USD e GBP/JPY), perché i sistemi sono raramente in posizione negli stessi giorni.

Il rischio comune del portafoglio quindi non si vede nei profitti giornalieri ma nel calendario: dal lunedì al mercoledì sono aperti insieme il long di AUDJPY, il long del Nasdaq e i long notturni del DAX, tutti posizioni che guadagnano quando i mercati cercano rischio, mentre gli short (tre sul DAX, uno sul Nasdaq, uno su AUDJPY) si concentrano tra martedì e venerdì. Una vendita forte di inizio settimana colpisce tutti i long insieme. È un'ipotesi da misurare con le liste dei trade dei backtest, giorno per giorno, prima di scegliere che cosa aggiungere (`piano.md`, cantiere 4).

## Una prova economica per le centinaia di sistemi già scritti

Il vantaggio di AUDJPY si è riconosciuto lanciando le stesse finestre su un prodotto vicino senza pattern (097 BRK, M6): profit factor 1,50 sul long e 1,32 sullo short. La stessa prova si può fare su ogni sistema di Andrea, senza ottimizzare niente:
1. pattern spenti (tutti i `Y` a 1 e gli `N` a 0), stessi orari, stop e uscite;
2. stesso codice su un prodotto con lo stesso meccanismo (un altro cross contro yen, un altro indice europeo);
3. resta in lista solo quello che tiene un profit factor sopra 1,3 in entrambi i casi e in entrambe le metà del periodo.

Un sistema che passa ha un vantaggio nella finestra e i pattern sono un ritocco; uno che non passa vive dei pattern, cioè probabilmente del passato.
