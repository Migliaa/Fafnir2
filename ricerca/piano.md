# Piano di ricerca: nuovi sistemi e diversificazione

**Aggiornamento del 2026-11-22**: con i dati a 1 minuto in `Dati/` la ricerca si fa fuori da ProRealTime, che resta per la verifica finale di Andrea. I cantieri sono diventati parti del software: `progetto-software.md`. Dove qui sotto c'è scritto "Andrea lancia", ora lancia il software.

Scritto il 2026-11-21. Parte da `cosa-distingue-i-sistemi.md` (che cosa hanno in comune i sistemi eccellenti) e da `librerie-pattern.md` (errori e ricostruzione delle librerie). Ogni direzione nuova segue comunque il ciclo di `metodo.md`: ricerca sul prodotto in `fonti/prodotti/`, ipotesi con direzione dichiarata, poi codice.

## Cantieri, in ordine

| # | Cantiere | Chi lavora | Costo in ProRealTime | Cosa produce |
|---|---|---|---|---|
| 1 | Correggere le librerie e scrivere la versione a famiglie | io | nessuno | libreria nuova, meno combinazioni con più significato |
| 2 | Setaccio dei sistemi già scritti: pattern spenti, prodotto gemello | Andrea lancia, io preparo i file | un lancio per sistema, senza ottimizzare | lista dei sistemi con un vantaggio nella finestra |
| 3 | Trapianto a parametri fermi dei due modelli che funzionano | io preparo, Andrea lancia | 1 ora, pochi lanci | prodotti nuovi per i due modelli |
| 4 | Analisi del portafoglio sulle liste dei trade | io | nessuno (servono le esportazioni) | calendario dell'esposizione, drawdown comuni, che cosa manca |
| 5 | Macchina di ricerca fuori da ProRealTime, primo pezzo | io | nessuno | mappa ora per ora con stabilità negli anni e costi |
| 6 | Direzioni nuove (sotto) | insieme | dipende | sistemi nuovi |

I cantieri 1-4 non richiedono ottimizzazioni lunghe e danno risultati in pochi giorni; il 5 serve soprattutto per i timeframe sotto l'ora e per provare molte idee senza consumare tempo macchina di ProRealTime.

### 2. Setaccio

Procedura in `cosa-distingue-i-sistemi.md`, ultima sezione. Serve sapere quali sistemi Andrea vuole passare al setaccio: quelli della cartella "2025 - PTF Stabile" sono un buon inizio, perché usano gli stessi modelli degli eccellenti su prodotti diversi.

### 3. Trapianti a parametri fermi

Stessi orari, soglie e uscite del sistema d'origine, nessun pattern, nessuna ottimizzazione; si tiene un prodotto solo se il profit factor resta sopra 1,3 in entrambe le metà del periodo.
- **Finestre dello yen** (128 AUDJPY) su NZD/JPY, CAD/JPY, EUR/JPY: allargano il numero di trade ma restano legate allo stesso rischio di AUDJPY, quindi aggiungono poco alla diversificazione.
- **Spostamento forte tenuto per giorni** (185 oro, 185 NQ) su DAX, S&P 500, argento, petrolio, Bund: il DAX darebbe un long con un meccanismo diverso da quello notturno di 165, il Bund e il petrolio sono i candidati scorrelati.

### 4. Analisi del portafoglio

Con le liste dei trade dei backtest dei sistemi in produzione (esportazione dal report di ProRealTime) si ricostruisce, ora per ora, quanta esposizione long e short c'è su ogni mercato e quali drawdown cadono negli stessi giorni. Serve a verificare l'ipotesi del calendario (inizio settimana tutto long, fine settimana tutto short) e a scegliere che cosa aggiungere in base a ciò che manca, non a ciò che è disponibile.

### 5. Macchina di ricerca

Un programma in Python che fa in pochi secondi quello che in ProRealTime costa ore, e che lascia a ProRealTime solo la verifica finale.

- **Dati.** Andrea ha già esportazioni nel formato di Bias Finder a 15 minuti (`Analisi\GBPUSD-TF15.txt`, `EURGBP-TF15.txt`, circa 2003-2025). Per indici, oro e cambi contro yen servono serie lunghe al minuto: Dukascopy le offre gratis dal 2003 circa; i prezzi dei CFD non coincidono con quelli IG, quindi la macchina sceglie le idee e il backtest di ProRealTime con gli spread IG decide.
- **Primo pezzo: mappa ora per ora.** Per ogni prodotto, il rendimento medio in escursioni medie per ogni coppia (ora d'ingresso, ora d'uscita) e per ogni giorno della settimana, anno per anno, al netto dello spread della fascia oraria. È il Bias Finder con due aggiunte: si vede se l'effetto c'è in ogni periodo o solo in alcuni anni, e si contano le finestre provate.
- **Prova di taratura.** Prima di cercare cose nuove, la macchina deve ritrovare da sola i vantaggi già noti: il ciclo settimanale di AUDJPY, lo short del DAX 15:00-16:35, la notte del DAX fino alle 09:00. Se non li ritrova, è sbagliata la macchina.
- **Secondo pezzo: studi d'evento** per il modello dello spostamento forte (quanto rende nei giorni dopo uno spostamento di k escursioni dall'apertura) su 20-30 prodotti, e per le famiglie della nuova libreria come condizioni.
- **Regole contro il sovra-adattamento**, decise prima: periodo di scoperta fino al 2018 e di verifica dal 2019; conferma su un prodotto gemello; registro del numero di prove fatte per ogni idea; si tengono solo zone stabili dei parametri.
- **Uscita**: codice ProRealCode con la console e gli interruttori standard, pronto da lanciare.

## Direzioni nuove

Ognuna con il meccanismo e il tipo di fonte; quelle senza un meccanismo preciso restano escluse anche se un backtest le premia.

**Long sul DAX** (bilancia i tre short)
- *Spostamento forte tenuto per giorni*, dal trapianto del cantiere 3.
- *Momento intraday sul lato long*: specchio dello short di 165 (12:30-19:30), comprando dopo una mattina in forte salita nei periodi agitati. Stesso meccanismo delle coperture gamma, che agisce nei due sensi (Baltussen et al. 2021, studio accademico); mai provato su 165. Attenzione: lo specchio long di 3251 nella finestra dell'apertura americana non ha reso (S10), ma era un'altra finestra.
- *Ultima mezz'ora di Xetra* (17:00-17:30) nella direzione della giornata, long o short: il resto della giornata prevede l'ultima mezz'ora, anche sui futures europei (Gao et al. 2018; Baltussen et al. 2021, studi accademici). Mezz'ora in mercato, grafico a 5 o 15 minuti; il punto debole è il costo, perché lo spread di 1,2-1,6 punti pesa su un movimento atteso di pochi punti, quindi va misurato prima con la macchina, distinguendo i periodi agitati.

**Scorrelati da Nasdaq, AUDJPY e oro**
- *Bund*: nelle vendite di panico sale mentre le borse scendono, quindi copre proprio il rischio di inizio settimana dei long. Il momento intraday vale anche sui futures obbligazionari (Baltussen et al. 2021). Prima serve `fonti/prodotti/bund.md`; Andrea aveva un 128 BIAS sul Bund nel portafoglio 2025.
- *EUR/USD e GBP/USD per ora del giorno*: una valuta tende a indebolirsi nelle ore di lavoro del suo paese (Breedon, Ranaldo 2013, studio accademico, A3 di `fonti/prodotti/audjpy.md`), e il dollaro sale prima dei fixing della BCE (14:15) e di Londra (17:00 italiane) e scende dopo (Krohn, Mueller, Whelan 2024, studio accademico). Direzione dichiarata: euro e sterlina più deboli nella mattina europea e fino al fixing, più forti dopo. Il limite è la grandezza: circa 2 punti base per fixing, scesi a 0,86 nel 2014-2019, vicini allo spread IG; va misurato con la macchina sui dati a 15 minuti che ci sono già, prima di scrivere codice.
- *Petrolio*: i tre sistemi attuali in reale 2024-2026 sono quasi in pari (long −586 €, short +605 €, una sola misura di due anni). Nessun meccanismo forte trovato finora: prima la ricerca sul prodotto (rapporto settimanale sulle scorte del mercoledì alle 16:30, sessioni), poi eventualmente il trapianto del cantiere 3.

**Poco tempo in mercato, timeframe bassi.** L'ultima mezz'ora di Xetra, la finestra dell'apertura americana di 3251 su Euro Stoxx 50 e US 500, i minuti attorno al fixing delle 17:00 sui cambi. Si cercano con la macchina, perché in ProRealTime i timeframe sotto l'ora sono lenti.

**Stop piccolo, target piccolo.** Non sono direzioni ma proprietà: uno stop stretto funziona solo dove il vantaggio si vede nelle prime barre (V2 di AUDJPY). La macchina può misurarlo per ogni finestra (quanto va contro una posizione vincente prima di guadagnare) e dire dove uno stop stretto è possibile.

**Correlazioni tra valute.** ProOrder non legge un secondo strumento, quindi non diventano segnali; servono per la costruzione del portafoglio (cantiere 4) e per scegliere il cross che contiene già la relazione (AUDJPY è AUDUSD per USDJPY).

**Escluse a priori.** Il rialzo prima della FOMC (quasi sparito dal 2015, Kurov et al. 2021); i flussi di fine mese sul Nasdaq (S6); i filtri di trend sui sistemi di calendario (S1).

## Da chiedere ad Andrea

1. 3251 FDAX ha in testa "Generato da AlphaMining... dal giro 8": è uno strumento suo? Se esiste già un generatore, la macchina del cantiere 5 va costruita sopra quello.
2. Quali dati può esportare (TradeStation o altro), per quali prodotti e da che anno; oppure se va bene scaricare Dukascopy.
3. Le liste dei trade dei backtest dei sistemi in produzione, per il cantiere 4.
4. Quali sistemi passare al setaccio, e in che ordine preferisce partire.
