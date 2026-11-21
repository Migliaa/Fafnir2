# Idee di trading

Logiche di mercato ricavate dai sistemi di Andrea, con il grado di prova raggiunto. Servono per combinarle o provarle su altri prodotti. La gestione di taglia e capitale sta in `moduli/`; qui c'è solo la logica di ingresso e uscita.

**Gradi di prova**
- **Validata**: un sistema che la usa guadagna in reale o su più di 10 anni di backtest, e almeno un test ne ha confermato il ruolo.
- **Presente in un sistema valido**: fa parte di un sistema che funziona, ma il suo contributo da sola non è stato misurato.
- **Debole**: effetto visto su pochi trade.
- **Smentita**: un test l'ha contraddetta. Non riproporla senza un motivo nuovo.
- **Da misurare**: logica di un sistema di Andrea non ancora passata da un report, o ipotesi in prova con direzione dichiarata.

## Principi trasversali

Quello che vale oltre il singolo sistema, con il test che lo sostiene. Da usare come prima ipotesi su un prodotto nuovo, non come regola.

1. **Prima di tutto capire che tipo di vantaggio ha una gamba**, perché decide quali moduli servono:
   - **calendario** (V1): funziona con qualunque trend e qualunque volatilità; i filtri di trend non aiutano (S1);
   - **momento intraday** (V4): vive nei periodi agitati; si filtrano i periodi calmi (M5 di 165 DAX) e non si riduce la taglia quando la volatilità sale (M2 di 165 DAX);
   - **notte sugli indici** (V5): il guadagno è nella notte, e uscire prima la toglie (S4).
   Il test che distingue i tipi costa poco: guadagno medio per regime di volatilità e per tratto della posizione (pomeriggio, sera, notte).
2. **La forma delle uscite segue la finestra del vantaggio** (V2, V5): stop stretto se il vantaggio si vede presto, uscita a tempo alla fine della finestra; target lontani o nessuno. Allargare o togliere un target già lontano non ha aiutato (M7 di 165 DAX).
3. **Gli orari d'uscita vanno messi dove lo spread è stretto**: su IG lo spread del DAX passa da 3,8 a 1,6 punti alle 09:00 (V5).
4. **Le esclusioni fisse dell'originale (giorni, condizioni settimanali) vanno riverificate dopo un filtro di regime**: una volta tolti i trade deboli, il lunedì escluso è tornato utile (M9 di 165 DAX).

---

## V1 – Ciclo settimanale di AUDJPY: rialzo a inizio settimana, ribasso giovedì-venerdì

**Grado: validata** (128 BIAS HOUR, in reale su IG; backtest 2014-2026).

- Long da lunedì 03:00 a mercoledì 22:00 (ora italiana): 287 trade, 44% vincenti, profit factor 2,2, guadagno medio circa 10.000 ¥ a trade, cioè circa 0,65 volte la perdita a stop.
- Short da giovedì 12:00 a venerdì 17:00: 393 trade, 56% vincenti, profit factor 1,6, guadagno medio circa 3.500 ¥, con una gamba meno forte del long.
- **Il vantaggio è di calendario, non di trend.** Con un filtro sulla media dei 100 giorni, i long scartati guadagnavano in media quanto quelli tenuti (9.411 ¥ contro 9.962 ¥, M5): il ciclo funziona sia con il mercato in salita sia in discesa.
- **Spiegazione non dimostrata.** L'ipotesi "il long recupera la riduzione di rischio fatta prima del weekend" è stata smentita (S2). Le spiegazioni ancora aperte riguardano altri flussi ricorrenti: sessione asiatica del lunedì, posizioni dei piccoli operatori giapponesi, fixing di Londra delle 17:00 del venerdì, che coincide con l'uscita dello short.
- **Confermata su GBP/JPY** (097 BRK, M6, backtest 2016-2026 a 30 minuti, stessi orari, nessun pattern): long 529 trade, profit factor 1,50, 2.335 ¥ a trade su 2.000.000 ¥ di posizione; short 536 trade, profit factor 1,32. Più debole che su AUDJPY, ma sopra la soglia di 1,3 su entrambi i lati: il ciclo è almeno in parte dello yen, non solo del dollaro australiano.
- **Come riciclarla:**
  - provare le stesse finestre su altri cross di carry contro yen (NZDJPY, CADJPY, MXNJPY) e su AUDUSD, per capire se l'effetto è di AUD, di JPY o del carry in generale;
  - combinarla con l'orologio della giornata (V7): long e short entrano nelle ore favorevoli al loro lato (097 BRK, M7 e M8, da misurare);
  - provarle sugli indici azionari, che si muovono insieme ad AUDJPY quando il mercato cerca rischio o fugge dal rischio;
  - su un prodotto nuovo, tenere fissi gli orari e verificare se il profit factor resta sopra 1,3 prima di ottimizzare qualunque cosa.

## V2 – Long con stop stretto e uscita a tempo: le perdite si chiudono presto, i guadagni corrono fino alla scadenza

**Grado: validata** (128 BIAS HOUR, gamba long).

- Lo stop allo 0,4% vale circa mezza escursione giornaliera di AUDJPY. Quasi tutti i perdenti escono a stop pieno dopo circa 20 ore; i vincenti restano aperti fino alla scadenza del mercoledì e guadagnano in media 2,75 volte lo stop. Il target (5 volte lo stop) viene raggiunto di rado.
- **Lo stop va tenuto fisso in percentuale.** Allargarlo e stringerlo con la volatilità ha funzionato solo dal 2022 ed è peggiorato sull'intero storico (M3).
- **Il guadagno sta nella scadenza.** Aggiungere a un trade già in guadagno aumenta il profitto quasi solo perché aumenta l'esposizione (M7, M9). Prolungare il trade oltre la finestra lo porta dentro la finestra opposta (V1).
- **Come riciclarla:** è la forma adatta a un vantaggio che si concentra in una finestra di tempo conosciuta. Su un prodotto nuovo con un vantaggio di calendario, provare uno stop pari a circa metà dell'escursione giornaliera, l'uscita alla fine della finestra e nessun target, o un target molto lontano.

## V3 – Operazione a tempo con stop di emergenza: taglia in base alla volatilità

**Grado: validata** (128 BIAS HOUR, gamba short, M8).

- Lo short esce sempre a tempo dopo 29 barre; lo stop al 2% non scatta quasi mai. La perdita reale dipende quindi da quanto si muove il prezzo in quelle ore, e dimensionare la taglia sulla volatilità recente ha ridotto il drawdown del 25% senza togliere profitto.
- Collegata alla lezione opposta: con uno stop stretto (V2) la stessa regola peggiora i risultati (M2).
- **Come riciclarla:** su una gamba con uscita solo a tempo, usare il modulo `moduli/taglia-volatilita-uscita-a-tempo.txt`, ma solo dopo aver controllato che il guadagno per trade non cresca con la volatilità: sugli short di momento del DAX (V4) avrebbe tolto i trade migliori.

## P1 – Niente long su AUDJPY dopo tre chiusure giornaliere in rialzo

**Grado: presente in un sistema valido** (128 BIAS HOUR, pattern `uptn049`).

- Al lunedì il long non si apre se martedì, mercoledì, giovedì e venerdì (o la domenica, a seconda di come il grafico raggruppa le ore del weekend) hanno chiuso ciascuno sopra il precedente: si evita di comprare dopo un rialzo già lungo.
- Contributo singolo non misurato. Va testato togliendolo (`PtnMRLN = 0`) prima di riusarlo altrove.

## P2 – Long solo se la barra oraria d'ingresso ha superato il massimo della precedente

**Grado: presente in un sistema valido** (128 BIAS HOUR, pattern `uptn091`): conferma di spinta di brevissimo periodo al momento dell'ingresso. Contributo singolo non misurato.

## P3 – Niente short il giovedì se il mercoledì è stato un "inside day"

**Grado: presente in un sistema valido** (128 BIAS HOUR, pattern `uptn134`). Un inside day è una giornata con massimo e minimo interni a quelli del giorno prima. Contributo singolo non misurato.

## P4 – Nasdaq: short su una giornata che si gira con forza dopo una chiusura forte, tenuto per giorni

**Grado: presente in un sistema valido, ruolo dei due pezzi misurato** (185 NQ 1H, 2016-2026).

- Short tra le 16:00 e le 20:00 se ieri il Nasdaq ha chiuso nel 20% più alto della sua escursione e oggi è sceso sotto l'apertura di almeno 4 escursioni orarie medie; esce dopo 100 barre, al quarto giorno o il venerdì alle 21:00. 89 trade, profit factor 3,4.
- Guadagna 60 € a trade nelle ore fino alla chiusura americana e 99 € nei giorni dopo (M2): è prosecuzione per giorni, non momento intraday.
- Senza la chiusura forte di ieri lo stesso calo non rende (M6: 8 € a trade). Nei periodi agitati rende più del doppio, ma è positivo anche nei calmi (M3).
- **Come riciclarla**: provare la stessa coppia (chiusura forte ieri, rovescio forte oggi) sugli altri indici americani, con la stessa durata di più giorni.

## D1 – Niente long su un cross di carry durante uno shock di volatilità

**Grado: debole** (128 BIAS HOUR, M4). Saltare i long quando la volatilità dell'ultimo giorno è più del doppio di quella degli ultimi mesi ha tolto 3 trade su 287 e ridotto il drawdown dei long del 10%. Ha una base economica (Brunnermeier-Nagel-Pedersen: le coppie di carry crollano quando la volatilità sale), ma i trade sono troppo pochi per una prova.

## V4 – DAX: short a metà giornata nella direzione della mattina, nei periodi agitati o dopo un forte calo

**Grado: validata** (165 DAX 30m, backtest 2015-2026; ruolo della volatilità confermato da M5, del calo della mattina da M10).

- Short alle 12:30, da lunedì a venerdì, se il prezzo è sotto la media di 25 barre da 30 minuti e il minimo di ieri non supera quello di cinque giorni prima; uscita dopo 7 ore (19:30), stop 2,5%, target 1,4%.
- Si apre se il periodo è agitato (volatilità delle ultime 2 settimane sopra quella degli ultimi 5 mesi) oppure, nei periodi calmi, se il prezzo è sceso dalla chiusura di ieri di almeno mezza escursione media giornaliera. Con 1 contratto: 389 trade, 26,29 € a trade, drawdown −860 €. Gli short calmi senza forte calo guadagnavano circa 7 € a trade, meno dei costi reali.
- **Spiegazione**: momento intraday degli indici. Chi ha esposizione gamma negativa (market maker di opzioni, ETF a leva) deve vendere quando il prezzo scende, e vende di più quando la volatilità è alta o il movimento è ampio (Baltussen et al. 2021; Gao et al. 2018).
- Il target fisso dell'1,4% va bene: allargarlo non ha alzato il guadagno medio e ha alzato il drawdown (M7).
- **Come riciclarla**: su altri indici con la sessione americana sovrapposta (Euro Stoxx 50, FTSE 100, CAC 40) con stessi orari, stesso filtro (`moduli/filtro-regime-volatilita.txt`) e stessa soglia sul calo della mattina; poi la stessa logica sul lato long (comprare dopo una mattina in forte salita nei periodi agitati), che su 165 DAX non è stata provata.

## V5 – DAX: long alle 13:30 dopo un'ora in salita, tenuto di notte fino all'apertura di Xetra

**Grado: validata** (165 DAX 30m, 699 trade dal 2015; il ruolo della notte confermato da M6, l'uscita alle 09:00 da M11).

- Long da lunedì a giovedì alle 13:30 se il prezzo è sopra la media di 25 barre da 30 minuti e l'RSI a 2 periodi è sopra 65; uscita alle 09:00 del giorno dopo, stop 3%. Con 1 contratto: 19,08 € a trade, drawdown −1.298 €.
- **Il guadagno sta in buona parte nella notte**: chiudere alle 21:30 i long in guadagno ha tolto il 28% del profitto (M6). Uscire alle 09:00 invece che alle 08:00 ha aggiunto l'11% (M11), più il risparmio di spread.
- **Non è momento intraday**: non dipende dall'ampiezza del movimento della mattina (M4). Guadagna di più nei periodi agitati (23 contro 13 €), ma anche quelli calmi sono positivi e tengono regolare la curva: niente filtro di volatilità.
- **Spiegazione probabile**: premio notturno degli indici azionari, concentrato all'apertura dei mercati europei (Boyarchenko-Larsen-Whelan 2023, sui futures americani; lì sparito dal 2021, sul DAX le barre 2021-2026 sono ancora positive).
- **Come riciclarla**: su altri indici europei tenere la posizione di notte e uscire dopo l'apertura della borsa a contanti; su indici americani o asiatici l'ora equivalente è l'apertura europea (08:00-09:00 italiane).

## V6 – Oro: rotture forti della giornata, tenute 2-3 giorni, con stop e taglia sulla volatilità oraria

**Grado: presente in un sistema valido** (185 TOP UA 342, Spot Gold E1 1 ora, backtest 2016-2026; il ruolo di alcune parti confermato togliendole).

- Long tra le 11:00 e le 22:00 se il prezzo è salito dall'apertura di almeno 2,5 escursioni orarie medie (ATR 200 ore) e la barra oraria ha superato il massimo precedente dello 0,5%; short con un calo di almeno 5,5 escursioni e un nuovo minimo dello 0,5%. Stop a 3 escursioni medie delle ultime 20 ore, posizione = 4% del capitale / distanza dello stop, uscita dopo 3-4 giorni. Long 183 trade, profit factor 1,79; short 65 trade, 2,71.
- **Confermato dai test**: la soglia di 5,5 escursioni dello short (con 4 gli short aggiunti perdono, M10); il pattern che esclude i long quando il minimo del giorno è già più dell'1% sopra quello di ieri (senza, i long aggiunti perdono 120 € ciascuno, M12); il target che lo short eredita dal long (senza, profit factor da 2,71 a 2,48).
- **Non dipende** dal regime di volatilità (M2, M6), dalle ore asiatiche (M1), dal trend di 12 mesi (M3). Uscite più rapide (M8) o più lunghe (M9) peggiorano il rapporto profitto / drawdown.
- **Spiegazione probabile** (non dimostrata, ma coerente con tutti i test): il long compra quando una giornata rompe con forza al rialzo e tiene la posizione per i giorni in cui la rottura richiama altri compratori (chi segue il trend, chi usa l'oro come rifugio, che compra a ondate: sull'oro la volatilità sale con i rialzi, Baur 2012); lo stop stretto taglia subito le rotture che tornano indietro, e il vincente medio vale circa il doppio del perdente. Lo short vende solo i crolli più violenti, quelli in cui partono vendite forzate e stop a catena che proseguono per due o tre giorni; sotto la soglia di 5,5 escursioni i cali dell'oro vengono ricomprati (M10), coerente con gli acquisti fisici dopo i crolli (World Gold Council, aprile 2013). Il target ereditato chiude gli short a circa 13 escursioni orarie, prima del rimbalzo.
- **La taglia a rischio costante è parte del sistema**: su un prodotto il cui prezzo è triplicato, a 1 contratto il 2026 faceva metà del profitto del long, con la taglia dell'originale la curva è diritta.
- **Come riciclarla**: stessa struttura (soglia in escursioni dall'apertura, barra di conferma, stop in escursioni, uscita a tempo) su argento o indici, con la taglia a rischio costante; le soglie vanno riprovate, non copiate.

## V7 – GBP/JPY: giù dalla notte al primo pomeriggio, su nelle ore americane

**Grado: presente in un sistema valido** (097 BRK GBP/JPY 30m, backtest 2019-2026); il tratto dopo il fixing di Londra è confermato nella direzione da M3, al limite del caso.

- Il long di 097 BRK compra la rottura del massimo della notte asiatica alle 10:30 (lunedì e mercoledì) ed esce alle 22:00: 328 trade, profit factor 2,3, profitto / drawdown 13 a 1 contratto. Uscire alle 17:00 toglie circa 560 ¥ a trade su 2.000.000 ¥ di posizione (2,8 punti base), quanto previsto dai ritorni attorno al fixing di Londra.
- Lo short spento dello stesso sistema (01:00-10:30, sotto il minimo asiatico del giorno prima) ha guadagnato sei anni su sette, con il 2026 in perdita.
- **Spiegazione documentata**: i cross di carry scendono dalla chiusura di New York al primo pomeriggio europeo e salgono nelle ore americane (Krohn-Mueller-Whelan, due paper con dati 1999-2019 e 1999-2023; `fonti/prodotti/gbpjpy.md`, A1 e A6), per le coperture dei dealer prima dei fixing e per come si forma il premio del carry durante la giornata.
- **Non è momento che vive nella volatilità**: i long dei periodi calmi guadagnano quanto quelli agitati (M1), con oscillazioni più piccole.
- **Come riciclarla**: su altri cross contro yen con valuta a tasso alto (AUDJPY, NZDJPY, MXNJPY) tenere i long nelle ore americane e gli short nelle ore asiatiche ed europee, sempre senza posizioni tra le 22:00 e l'01:00; misurare l'ultimo tratto del long con un'uscita al fixing delle 17:00.

## V8 – DAX: le ore dell'apertura europea salgono anche dopo un calo notturno

**Grado: presente in un sistema valido** (138 DAX 1H, M2, 71 short del martedì dal 2016; conferma dal lato opposto di V5).

- Lo short di 138 DAX decide alle 04:00 su un calo notturno e prima entrava subito; entrando alle 09:00 sugli stessi trade il guadagno medio è passato da 56 a 103 € a trade (posizione da 30.000 €): il tratto 04:00-09:00 costava allo short 46,59 € a trade, circa due volte l'incertezza. Profit factor da 2,64 a 3,14.
- Il resto della giornata va tenuto: uscire alle 17:00 ha tolto 30 € a trade (M6), e uno stop all'1,5% invece del 3% ha quasi dimezzato il profitto (M7). Il segnale vale solo il martedì (M5: gli altri giorni −7 € a trade), quindi martedì e pattern sono probabilmente scelti insieme sul backtest.
- **Spiegazione**: la stessa di V5, il rialzo degli indici all'apertura dei mercati europei (Boyarchenko-Larsen-Whelan 2023). Sul DAX resta anche dopo il 2021 e anche quando la notte è stata in calo.
- **Come riciclarla**: nessuno short sugli indici europei va aperto prima delle 09:00 se la logica non riguarda proprio quell'ora; gli ingressi notturni vanno spostati all'apertura della borsa a contanti, dove lo spread IG è anche più stretto (1,6 punti contro 5).

## V7 – DAX: short nel pomeriggio, dall'apertura americana fino a un'ora dopo

**Grado: presente in un sistema valido** (3251 FDAX 5m, Germany 40 Cash, 2012-2026, 370 trade; ruolo degli orari misurato, sistema da generatore con i giorni scelti sul backtest).

- Martedì, giovedì e venerdì, decisione alle 14:00: short se il prezzo è più dello 0,5% sotto il massimo della seduta e non sotto il minimo di ieri; vendita alle 15:00, uscita alle 16:35, stop 167 punti, pareggio allo 0,31%. A 1 contratto 13,08 € a trade, drawdown −485 €.
- **L'ora dei dati americani va lasciata fuori**: entrando alle 14:00 lo short guadagnava 3,6 € a trade in più ma con il drawdown quasi doppio (M2). Il tratto 15:55–16:35, con i dati delle 16:00, invece rende (M8); quello dopo le 16:35 no (M3).
- **Non è momento simmetrico**: il long speculare guadagna 0,60 € a trade su 720 (M7). Dopo lo spostamento alle 15:00 periodi calmi e agitati rendono uguale (M5).
- **Spiegazione probabile**: sui futures S&P 500 i rendimenti sono negativi dalle 15:00 alle 18:00 italiane, significativi il giovedì e il venerdì e nelle crisi, deboli dopo il 2010 (Boyarchenko, Larsen, Whelan 2023, appendice).
- **Come riciclarla**: stessa finestra (15:00–16:35) su Euro Stoxx 50 e CAC 40, giovedì e venerdì; sui futures americani la stessa ora (9:00–10:35 di New York).

---

## Idee smentite

### S1 – Filtrare un sistema di calendario con il trend di fondo
128 BIAS HOUR, M5: il filtro sulla media dei 100 giorni ha dimezzato i trade e il profitto senza alzare il guadagno medio. Non riproporlo su sistemi di calendario.

### S2 – Ciclo di riduzione del rischio prima del weekend su AUDJPY
128 BIAS HOUR, M11: prendere il long del lunedì solo se il prezzo era sceso dal giovedì precedente ha portato il capitale finale dei long da 3,64 a 2,57 M ¥. Il long del lunedì non dipende dal movimento di fine settimana precedente.

### S3 – Niente short sul DAX a cavallo di fine mese
165 DAX, M3: gli short del pomeriggio nei quattro giorni attorno al cambio di mese (McConnell-Xu 2008) hanno guadagnato 21,78 € a trade contro 17,23 € degli altri (98 trade). L'effetto fine mese, se c'è, non si vede negli short pomeridiani del DAX.

### S4 – Chiudere la sera i long notturni del DAX già in guadagno
165 DAX, M6: l'idea era che dopo un pomeriggio in salita la notte rendesse poco (inversione del momento intraday, Baltussen et al. 2021; rialzo notturno debole dopo i rialzi, Boyarchenko et al. 2023). Chiudere alle 21:30 i long in guadagno ha portato il guadagno medio da 17,14 a 12,32 € e il profitto del long da 11.981 a 8.610 €.

### S5 – Filtrare con il trend di 12 mesi lo short che vende i crolli dell'oro
185 oro, M3 (a 1 contratto, 2016-2026): tenere lo short solo con l'oro più basso di un anno prima ha tolto 50 short su 65, che guadagnavano in media 13,49 € contro 10,80 € dei tenuti. I crolli dell'oro proseguono anche dentro un trend di fondo in salita; il momento di 12 mesi (Moskowitz, Ooi, Pedersen 2012) non serve come filtro di una gamba di pochi giorni.

### S6 – Uscite attorno alla salita dell'oro nelle ore asiatiche
185 oro, M1 (2016-2026): tenere il long fino alle 09:00 invece che all'01:00 non ha cambiato il risultato (−0,43 € a trade a 1 contratto), chiudere lo short alle 21:00 prima della terza notte asiatica ha tolto l'8% del profitto dello short con il drawdown +9%. La salita notturna documentata sul 2001-2018 (Blose et al. 2018) in questi anni e su questi trade non c'è.

### S7 – Pesare i trade per regime di volatilità sull'oro
185 oro, M6: metà posizione ai long dei periodi calmi ha ridotto profitto e drawdown nella stessa proporzione (rapporto 11,62 contro 11,46); metà posizione agli short dei periodi agitati ha peggiorato il rapporto (7,70 contro 8,23). Il vantaggio delle due gambe, misurato a rischio costante, non dipende dal regime; la differenza vista a 1 contratto (M2) era dovuta alla scala dei trade.

### S6 – Long sul Nasdaq anche nei giorni del cambio di mese
185 NQ, M5 (2016-2026, valore fisso 30.000 €): aggiungere al long del lunedì i long dell'ultimo giorno di borsa del mese e dei primi tre (McConnell-Xu 2008; Etula et al. 2020) ha aggiunto 118 trade che perdono 34 € in media, e il drawdown è salito del 24%. Sul Nasdaq 100 dal 2016 il flusso di fine mese non si vede in trade di quattro giorni.

### S7 – Chiudere alla chiusura americana lo short che vende un forte calo del Nasdaq
185 NQ, M2: l'idea era che lo short fosse momento intraday e che la notte dopo le vendite gli andasse contro (Baltussen et al. 2021; Boyarchenko et al. 2023). Lo short guadagna 60 € a trade fino alla chiusura e 99 € nei giorni successivi: un forte calo della seduta americana prosegue per giorni, come sull'oro.

### S8 – Uscire presto dalle rotture dell'oro che non partono
185 oro, M8: chiudere alla barra 10 i trade ancora in perdita ha portato i vincenti del long dal 46 al 32% e il drawdown quasi al doppio. Le rotture dell'oro spesso tornano sotto il prezzo d'ingresso prima di proseguire.

### S9 – Abbassare la soglia del crollo dello short sull'oro
185 oro, M10: con un calo di 4 escursioni orarie invece di 5,5 gli short sono passati da 65 a 120 e quelli aggiunti hanno perso in media 38,76 € ciascuno.

### S10 – Filtrare con il regime di volatilità il long di rottura di GBP/JPY
097 BRK GBP/JPY, M1 (a valore fisso, con il riferimento stimato): tenere solo i long dei periodi agitati ha lasciato 121 trade su 328 con lo stesso guadagno medio (2.080 ¥ contro circa 2.100 dei 207 scartati) e un drawdown più alto. La rottura del massimo asiatico non dipende dal regime; la volatilità decide solo quanto oscillano i trade (V7).

### S11 – Long del DAX il martedì dopo un lunedì in forte calo
138 DAX, M4 (posizione da 30.000 €, 96 trade dal 2016): l'idea era l'inversione dopo un giorno di vendite, con il rialzo all'apertura europea più forte dopo le vendite (Boyarchenko et al. 2023; Baltussen, van Bekkum, Da 2019). Circa +4.900 € fino al 2021 e −550 € dal 2022: l'effetto c'era ed è sparito, come sui futures USA. Attenzione: V8 dice che sul DAX l'ora 08:00-09:00 sale ancora in media; quello che è sparito è il recupero di tutto il martedì dopo un forte calo.

### S10 – Long speculare dello short pomeridiano del DAX
3251 FDAX, M7: comprare alle 15:00 una giornata salita dello 0,5% dal minimo, fino alle 16:35, ha dato 0,60 € a trade su 720 (profit factor 1,03). Nella finestra dell'apertura americana il DAX non ha un momento simmetrico.

### S12 – Short USD/CHF dopo un forte apprezzamento del franco in giornata
128 BIAS USDCHF, M2 (90 franchi di rischio, dal 2014): vendere quando USD/CHF scende dall'apertura di 3,5 escursioni orarie e fa un nuovo minimo delle 24 ore, tenuto due giorni, ha dato 2,63 franchi a trade su 375 (profit factor 1,11), tutto nel 2025-2026. Il franco è una valuta rifugio (Ranaldo-Söderlind 2010), ma i suoi rialzi forti non proseguono come quelli dell'oro e del Nasdaq: fino al 2022 la BNS li frenava con gli interventi.
