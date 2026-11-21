# 3251 ORAF FDAX 5m – short del pomeriggio sul DAX

Sistema solo short sul DAX, grafico a 5 minuti, ora italiana (uguale a quella di Francoforte). L'intestazione del generatore parla del CFD sui futures, ma i backtest di Andrea sono sul Germany 40 Cash (1 €), dal novembre 2012. Il codice è stato generato da AlphaMining (giro 8, 11 novembre 2026) e poi cambiato a mano da Andrea nei giorni (martedì, giovedì e venerdì, mentre il nome del generatore dice "TUTTI") e nella taglia (`RischioTrade = 2.5 + StrategyProfit/2000`). Ricerca sul prodotto: `fonti/prodotti/dax.md`, sezione "Pomeriggio e apertura americana".

**Stato:** pronto per il reale: [DEFINITIVO-produzione](versioni/DEFINITIVO-produzione.txt) = C1 (originale con la vendita alle 15:00, M2) con la console a rischio per trade, 9,5% di 10.000 € (918 € a stop) e manopola `Aggressivita` 1,5. Otto moduli provati, uno promosso.

## Cosa fa

Il codice ricostruisce la seduta di Xetra (09:00–17:30) dalle barre del CFD, che quota anche di notte, e a ogni chiusura di barra decide per l'apertura della barra successiva.

**Ingresso.** Martedì, giovedì e venerdì, con una sola decisione alla barra che chiude alle 14:00: vende allo scoperto se il prezzo è più dello 0,5% sotto il massimo della seduta e non è sotto il minimo della seduta di ieri, cioè in una giornata che ha perso terreno dal massimo senza rompere al ribasso. Se alle 14:00 le condizioni non ci sono, quel giorno non entra più.

**Uscita.** Alle 16:35, dopo 2 ore e 35 minuti (31 barre), un'ora dopo l'apertura di Wall Street; stop a 167 punti; dopo un guadagno dello 0,31% (circa 80 punti oggi) lo stop passa al prezzo d'ingresso; nessun target. Dentro la finestra cadono i dati americani delle 14:30, l'apertura di Wall Street alle 15:30, i dati delle 16:00 e, nei giovedì di riunione della BCE, la decisione delle 14:15 e la conferenza stampa delle 14:45 (dal luglio 2022; prima alle 13:45 e alle 14:30).

**Taglia.** Il rischio allo stop è il 2,5% del capitale attuale più lo 0,05% ogni 100 € di profitto; i contratti sono quel rischio diviso 167 punti, arrotondati per difetto a 0,5, tra 0,5 e 80. Un freno ferma il sistema per sempre quando il capitale scende del 30% dal massimo.

## Che tipo di vantaggio ha

Secondo i principi trasversali di `idee/idee-di-trading.md` le ipotesi sono due, e la prima tornata serve a distinguerle.

- **Calendario (orario).** Sui futures S&P 500 dal 1998 al 2020 i rendimenti sono negativi dalla mezz'ora prima dell'apertura di New York fino alle 12:00 di New York, cioè dalle 15:00 alle 18:00 italiane, e nell'ora dell'apertura valgono −1,2 punti base al giorno; per giorno della settimana sono significativi solo il giovedì (−2,1) e il venerdì (−3,0), mentre il martedì è zero (Boyarchenko, Larsen, Whelan 2023, appendice). La finestra e due dei tre giorni del sistema coincidono, e nel pomeriggio il DAX si muove insieme ai futures americani. Lo stesso studio però trova l'effetto forte dal 1998 al 2010 e nei periodi di crisi (2000-2003, 2007-2008, 2020), mentre dal 2011 al 2020 l'ora dell'apertura è leggermente positiva e non significativa: se il vantaggio fosse solo questo, nel backtest recente dovrebbe essere debole.
- **Momento intraday.** La condizione "0,5% sotto il massimo" sceglie le giornate che si indeboliscono, e su oltre 60 futures, DAX compreso, il movimento della giornata prosegue fino alla chiusura della borsa a contanti, di più con volatilità alta, per le coperture di chi ha esposizione gamma negativa (Baltussen et al. 2021; Gao et al. 2018). La seconda condizione però esclude le giornate già sotto il minimo di ieri, che sono i cali più forti, cioè quelli in cui il momento dovrebbe essere più forte: il motivo può essere lo stop in punti, troppo stretto nelle giornate agitate, oppure il rimbalzo che dopo le giornate di vendite è documentato sui futures americani (stesso studio di Boyarchenko e altri).

Il test che distingue i due tipi costa poco (principio 1): guadagno medio per regime di volatilità (M1) e per tratto della posizione, cioè quanto rende l'ora prima dell'apertura americana (M2) e quanto il tratto dopo l'uscita fino alla chiusura di Xetra (M3). Se il vantaggio è di calendario, i periodi calmi rendono quanto quelli agitati e l'ora 14:00–15:00 non aggiunge niente; se è momento intraday, i calmi rendono meno e i trade in giornate in calo guadagnano ancora dopo le 16:35.

## Problemi trovati nel codice

1. **Il reinvestimento accelera fino a mettere a rischio il conto, e il freno poi ferma il sistema per sempre.** La percentuale di rischio cresce con il profitto, quindi il rischio in euro cresce più del capitale:

   | Profitto | Capitale | Rischio scritto | Contratti | Perdita a stop | in % del capitale |
   |---|---|---|---|---|---|
   | 0 | 10.000 € | 2,5% | 1 | 167 € | 1,7% |
   | 5.000 € | 15.000 € | 5% | 4 | 668 € | 4,5% |
   | 10.000 € | 20.000 € | 7,5% | 8,5 | 1.420 € | 7,1% |
   | 20.000 € | 30.000 € | 12,5% | 22 | 3.674 € | 12,2% |
   | 40.000 € | 50.000 € | 22,5% | 67 | 11.189 € | 22,4% |

   Oltre i 40.000 € di profitto due stop di fila portano il capitale più del 30% sotto il massimo, e il freno blocca il sistema senza riavviarlo: nel backtest la curva si ferma, in reale il sistema smette di aprire. Inoltre il report dell'originale non è confrontabile con nessun modulo, perché la taglia cambia con la storia dei profitti. C0 sostituisce questa parte con la console standard (`moduli/console-rischio-per-trade.txt`), dove la manopola `Aggressivita` decide quanto i profitti fanno crescere il rischio e la percentuale resta quella scritta.
2. **Lo stop è in punti e il DAX è più che raddoppiato.** 167 punti erano circa l'1,7% del prezzo con il DAX a 10.000 (2016), l'1,1% a 15.000 (2021-2023) e sono lo 0,63% oggi, a 26.700, mentre il passaggio al pareggio è in percentuale (0,31%). Lo stop con cui il sistema lavora oggi è il più stretto di tutto il backtest, e nei primi anni lo stop non scattava quasi mai: i risultati vecchi descrivono un sistema che usciva quasi solo a tempo o a pareggio, quelli recenti uno con uno stop vicino. M4 misura il sistema con lo stop in percentuale su tutto lo storico.
3. **Sistema scelto da un generatore, poi con i giorni scelti sul backtest.** Quando si scelgono regole tra migliaia di candidate, la migliore è in parte migliore per caso: sulle regole di calendario delle borse americane, risultati con significatività altissima presi uno per uno non reggono più quando si tiene conto di quante regole erano state provate (Sullivan, Timmermann, White 2001; Bailey et al. 2017 in `fonti/paper/schede.md`). La scelta di martedì, giovedì e venerdì si aggiunge alla ricerca del generatore. Servono le date del periodo su cui AlphaMining ha scelto il sistema (in-sample) e i risultati sul periodo dopo, e i risultati per giorno dell'ottimizzazione di Andrea. La letteratura sostiene giovedì e venerdì, non il martedì.
4. **Parametri morti o incoerenti.** `Giorni = 2` non è usato (i giorni sono scritti nella riga `giornoOk`); l'intestazione parla di "RischioTrade = 0%" e di un freno al 50%, mentre il codice usa la formula di Andrea e il 30%; `EntraLong` e la taglia del long non servono, perché il codice non ha ingressi long.
5. **Dettagli dello stop.** Nella prima barra (14:00–14:05) la posizione non ha stop, perché l'ordine viene messo alla chiusura della barra in cui si è in posizione; il minimo di quella barra non conta per il pareggio. Con uno stop di 167 punti l'effetto è piccolo.
6. **Settimane con ora legale sfasata** (circa tre l'anno, a marzo e tra fine ottobre e inizio novembre): i dati americani escono alle 13:30 e Wall Street apre alle 14:30, quindi l'ingresso delle 14:00 cade mezz'ora prima dell'apertura americana invece di un'ora e mezza.
7. **Scadenze del terzo venerdì.** Lo short del venerdì entra un'ora dopo l'asta delle 13:00 che chiude futures e opzioni sul DAX; nessuna direzione documentata (B3 di `fonti/prodotti/dax.md`).
8. **Costi.** Entra ed esce durante la seduta di Xetra, con lo spread più stretto (1,2-1,6 punti sul Germany 40 secondo le pagine IG, da verificare per il CFD sui futures), e non paga finanziamento perché chiude in giornata. Il backtest usa uno spread fisso: va chiesto quale.
9. **`ValorePunto = 1`** presuppone il contratto da 1 € a punto: da confermare con lo strumento usato in reale.

## Prima tornata: M1–M4, sopra C0

[C0](versioni/C0-originale-con-console.txt) è l'originale con la console di gestione al posto delle sezioni 3 e 5 e senza il freno; ingressi, filtri, stop e uscite sono quelli dell'originale. Con `CapitaleVersato = 10000`, `RischioShort = 2.5` e `Aggressivita = 0` fa sempre 1 contratto (250 € / 167 punti = 1,5, arrotondato per difetto a 1), quindi deve dare gli stessi trade e gli stessi punti dell'originale lanciato con `Reinvest = 0` e `ContrattiFissi = 1`: è il controllo che C0 sia giusto.

**Riferimento comune**: qualunque file della tornata con `UsaMx = 0`, che riproduce C0. **Taglia dei test**: 1 contratto fisso, come C0. Con lo stop in punti il rischio fisso per trade coincide con un numero fisso di contratti; gli anni recenti pesano di più in euro perché i punti valgono di più in percentuale con il DAX alto, quindi oltre al totale vanno guardati gli anni.

| Modulo | Idea | Da dove viene |
|---|---|---|
| [M1](proposte/M1-regime-di-volatilita.txt) | short solo nei periodi agitati (escursione media della seduta delle ultime 2 settimane almeno pari a quella degli ultimi 5 mesi) | momento intraday (Baltussen 2021); rendimenti negativi all'apertura americana concentrati nelle crisi (Boyarchenko 2023); `moduli/filtro-regime-volatilita.txt`, rifatto con le candele della seduta |
| [M2](proposte/M2-ingresso-dopo-i-dati-usa.txt) | stessa decisione delle 14:00, ingresso alle 15:00; variante alle 14:35, subito dopo i dati delle 14:30 | sui futures americani l'ora dei dati è positiva e il calo comincia mezz'ora prima dell'apertura (Boyarchenko 2023; Savor-Wilson 2013) |
| [M3](proposte/M3-uscita-alla-chiusura-di-xetra.txt) | uscita alle 17:25 invece che alle 16:35 se la giornata è in calo rispetto a ieri; variante: tutti alle 17:25 | momento fino alla chiusura della borsa a contanti (Baltussen 2021, Gao 2018); calo dei futures americani fino alle 18:00 italiane (Boyarchenko 2023) |
| [M4](proposte/M4-stop-in-percentuale.txt) | stop allo 0,65% del prezzo (quello di oggi) su tutto lo storico; variante 1% (quello medio del backtest) | problema 2 del codice; Kaminski-Lo 2014 |

M2 e M3 non vengono dalla libreria. M4 viene dal codice.

**Direzioni dichiarate prima del test**
- M1: gli short dei periodi agitati guadagnano in media più di quelli calmi. Se il guadagno è uguale, il vantaggio è di calendario.
- M2: entrando alle 15:00 il guadagno medio sale, perché l'ora 14:00–15:00, con i dati americani, in media va contro lo short. Effetto atteso piccolo, pochi punti a trade.
- M3: i trade tenuti fino alle 17:25 nelle giornate in calo guadagnano ancora nel tratto aggiunto; tutti insieme (variante) guadagnano meno, perché nelle giornate in salita il momento va contro lo short.
- M4: con lo 0,65% gli anni fino al 2021 hanno un guadagno medio più basso e un drawdown più basso, perché lo stop stretto taglia trade che poi rientrano; gli ultimi due anni restano quasi uguali. Se invece i primi anni migliorano, nei trade che vanno male il movimento prosegue e uno stop stretto è giusto anche per il futuro.

## Come leggere i test

- **Ingressi e uscite sugli stessi trade (M2, M3)**: stessi giorni del riferimento, quindi la differenza di profitto è quanto rende il tratto tolto o aggiunto. Con M3 e la variante si ricavano tutti e due i gruppi: tratto delle giornate in calo = M3 − riferimento, tratto delle giornate in salita = variante − M3.
- **Filtro (M1)**: guadagno medio degli short scartati = (profitto riferimento − profitto M1) / (trade riferimento − trade M1), confrontato con quello dei tenuti. L'incertezza sulla differenza si ricava dalla dispersione di un trade, stimata da vincente e perdente medio (`moduli/lezioni.md`, Filtri e uscite).
- **Stop (M4)**: stessi ingressi e stessa taglia, cambia solo lo stop; vanno confrontati gli anni, perché negli ultimi due lo stop resta quasi uguale.
- I primi mesi del backtest di M1 non sono affidabili: le medie della volatilità hanno bisogno di circa 100 sedute per assestarsi.

## Prima tornata: esiti

C0 a 1 contratto, 2012-2026: 370 short, 16,67 € a trade, profit factor 2,08, profitto 6.166 €, drawdown −861 €. Numeri in `registro-test.md`.

| Modulo | Esito |
|---|---|
| M1 solo periodi agitati | agitati 20,62 € a trade, calmi 11,64 €: direzione prevista ma dentro l'incertezza, e i calmi sono positivi. Profitto / drawdown da 7,16 a 8,71, ma restano 207 trade: scartato da Andrea, ripreso come mezza posizione (M5) |
| **M2 ingresso alle 15:00** | **promosso (C1)**: l'ora 14:00–15:00 rendeva allo short 3,58 € a trade, ma portava quasi metà del drawdown (da −861 a −485 €); profitto / drawdown da 7,16 a 9,97, miglior trade da 713 a 376 € |
| M3 fino alle 17:25 nelle giornate in calo | il tratto aggiunto rende 179 € in tutto e il drawdown sale del 21% (profitto / drawdown 6,11): scartato |
| M4 stop allo 0,65% | profitto −9%, drawdown −12%, profitto / drawdown invariato (7,39): lo stop che si stringe con il DAX alto non indebolisce il sistema. Non adottato |

**Cosa dice sul tipo di vantaggio.** Lo short guadagna anche nei periodi calmi, quindi non è solo momento intraday: c'è una parte di calendario, la finestra pomeridiana. L'ora dei dati americani rende poco e porta molto rischio: il vantaggio sta dopo le 15:00, cioè nell'ora dell'apertura americana, dove sui futures S&P 500 il calo è documentato. Le prove successive cercano dove finisce la finestra buona (M8), se la decisione presa dopo i dati sceglie meglio i giorni (M6), se il momento è simmetrico (M7, lato long) e come pesare i periodi calmi senza toglierli (M5).

## Seconda tornata: M5–M8, sopra C1

Andrea ha chiesto quattro tentativi più audaci: entrata, uscita, lato long, posizione variabile. **Riferimento**: C1, già misurato (M2 della prima tornata: 370 short, 13,08 € a trade, 4.841 €, drawdown −485 €), oppure qualunque file della tornata con `UsaMx = 0`. Taglia dei test: 1 contratto.

| Modulo | Idea | Direzione attesa |
|---|---|---|
| [M5](proposte/M5-mezza-posizione-nei-periodi-calmi.txt) | short dei periodi calmi con mezza posizione; variante: niente short calmi | profitto / drawdown più alto di C1 con tutti i trade |
| [M6](proposte/M6-decisione-alle-15.txt) | filtri letti alle 15:00, dopo i dati; variante alle 15:30 | guadagno medio più alto di C1 |
| [M7](proposte/M7-lato-long.txt) | long speculare: alle 15:00 se la giornata è salita dello 0,5% dal minimo e non è sopra il massimo di ieri, nei giorni senza short; per giorno con l'ottimizzazione | long più debole dello short, negativo o nullo giovedì e venerdì |
| [M8](proposte/M8-uscita-prima-dei-dati-delle-16.txt) | uscita alle 15:55, prima dei dati delle 16:00; variante alle 17:25 | profitto più basso e drawdown che scende di più |

M6, M7 e M8 non vengono dalla libreria; M5 riprende il regime di M1.

## Seconda tornata: esiti

| Modulo | Esito |
|---|---|
| M5 calmi a mezza posizione | dopo lo spostamento alle 15:00 calmi e agitati rendono quasi uguale (2.307 e 2.535 €): profitto / drawdown da 9,97 a 7,98, scartato |
| M6 decisione alle 15:00 | 32 trade in più, drawdown da −485 a −665 €, ultimi anni più deboli: scartato |
| M7 lato long | 720 long a 0,60 € a trade, profit factor 1,03: nessun vantaggio, come previsto |
| M8 uscita alle 15:55 | il tratto 15:55–16:35 rende 2.186 €: l'uscita delle 16:35 resta |

**Conclusione sul vantaggio.** È di calendario: lo short del DAX nel pomeriggio, dall'apertura americana fino a un'ora dopo, nei giorni in cui la mattina ha perso terreno dal massimo. Non è momento simmetrico (il long speculare non guadagna) e non dipende dal regime di volatilità una volta tolta l'ora dei dati. L'ora dei dati delle 14:30 portava quasi metà del drawdown; il tratto 15:00–16:35 è quello che rende, coerente con il calo dei futures americani attorno all'apertura di New York (Boyarchenko, Larsen, Whelan 2023). Il backtest viene da un generatore con i giorni scelti dopo, quindi va letto come sovrastimato.
