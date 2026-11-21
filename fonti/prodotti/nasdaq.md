# Nasdaq 100 (US Tech 100 su IG) – ricerca sul prodotto

Ricerca del 2026-11-20. Orari in ora italiana (CET d'inverno, CEST d'estate). Il Nasdaq 100 ha chiuso a 31.224 il 6 ottobre 2026, il suo massimo, ed è sceso di oltre il 10% nelle settimane successive; tra il 4 e l'11 novembre ha chiuso tra 27.900 e 28.440 (stampa finanziaria: [247wallst](https://247wallst.com/investing/2026/11/10/the-nasdaq-100-just-had-its-best-day-since-march-without-nvidias-help/), [archyde](https://www.archyde.com/nasdaq-100-gains-strength-in-new-york-trading-session/)). Livelli storici a memoria, da verificare sul grafico: circa 4.000-4.700 nel 2015, 10.000 superato a giugno 2020, 20.000 a metà 2024. Dal 2015 il prezzo è cresciuto di circa sei volte.

**Gradi** (come in `README.md` di questa cartella)
- **A**: meccanismo chiaro, fonte solida, traducibile in ProRealCode.
- **B**: plausibile ma con fonte debole, oppure solo in parte traducibile.
- **C**: contesto, non diventa codice.

---

## Orari

| Evento | Ora italiana | Fonte |
|---|---|---|
| US Tech 100 su IG | da lunedì 00:00 a venerdì 23:00, quotato anche di notte | broker, [IG Svizzera](https://www.ig.com/en-ch/indices/indices-cfd-details), pagina del 20/9/2026 |
| Pausa dei futures CME | 23:00-00:00 (17:00-18:00 a New York); IG quota lo stesso con spread 5 | dati ufficiali CME, non riletti; spread dalla pagina IG |
| Apertura europea (Xetra, Eurex) | 08:00 pre-apertura, 09:00 borsa a contanti | dati ufficiali, `fonti/prodotti/dax.md` |
| Dati macro USA (occupazione, inflazione) | 14:30 | calendario ufficiale USA |
| Borsa a contanti USA | 15:30-22:00 | dato ufficiale |
| Decisione FOMC | 20:00, di solito il mercoledì | calendario Fed |
| Scadenza mensile delle opzioni | terzo venerdì del mese | dato ufficiale, non riletto |

- **Settimane con ora legale sfasata.** Gli USA cambiano l'ora la seconda domenica di marzo e la prima di novembre, l'Europa l'ultima domenica di marzo e di ottobre. In quelle circa tre settimane l'anno la borsa USA apre alle 14:30 e chiude alle 21:00 ora italiana, la pausa dei futures cade alle 22:00 e la FOMC decide alle 19:00.
- **Candela giornaliera di ProRealTime sui CFD IG.** Sul forum di ProRealCode si legge sia che inizia a mezzanotte sia all'01:00 ora italiana, e che non si può spostare ([forum](https://www.prorealcode.com/topic/the-daily-candlestick-is-not-the-universal-daily-candlestick-on-prt-ig/), [forum](https://prorealcode.com/topic/changing-daily-candle-open-and-close-times)); testimonianze. `DOpen(0)` è quindi il prezzo di mezzanotte o dell'01:00, non quello dell'apertura di New York; `DayOfWeek` cambia quando si apre la candela giornaliera.

## Costi su IG

Fonte: [IG Svizzera, dettagli CFD indici](https://www.ig.com/en-ch/indices/indices-cfd-details), pagina datata 20 settembre 2026 (broker). La pagina italiana non era raggiungibile: verificare in piattaforma ("Info").

- **Contratti**: US Tech 100 Cash da 1 $ per punto; futures da 100 $ e mini da 20 $; un "Weekend US Tech 100" separato (spread 16). Sulla pagina inglese compare anche un "Weekend US Tech 100 E1", quindi esistono versioni in euro: Andrea usa il US Tech 100 Cash da 1 € (dato di Andrea), con profitti e `StrategyProfit` in euro. La pagina non indica la taglia minima ("di solito parte da un contratto"); il codice di Andrea usa un minimo di 0,5.
- **Spread del Cash (punti)**:

| Fascia | Spread |
|---|---|
| 15:30-22:00 | 1,3 (variabile) |
| 23:00-00:00 | 5 |
| altre ore | 2,5 |

  Con l'indice a 28.000, 2,5 punti sono lo 0,009% del prezzo: sul Nasdaq lo spread pesa molto meno che sul DAX (1,6-3,8 punti su 26.700, con movimenti giornalieri più piccoli).
- **Margine**: 0,5% sulla tabella della pagina svizzera (scaglioni a parte); per i clienti al dettaglio in Europa di solito il 5%.
- **Finanziamento overnight**: sulle posizioni aperte alle 23:00, contratti × prezzo alle 23:00 × tasso annuo / 360; il venerdì vale tre giorni; i long pagano, gli short ricevono o pagano. Il tasso è il riferimento in dollari più una commissione IG che la pagina non indica (sul DAX il 3%, `fonti/prodotti/dax.md`). Con il SOFR al 3,95% a inizio novembre 2026 ([sofrrate.com](https://www.sofrrate.com/sofr-rate/2026-11), sito di dati) e la commissione al 3%, un contratto long da 1 $ con l'indice a 28.000 paga circa 5,4 $ a notte, circa lo 0,02% del valore; uno short riceve circa 0,7 $. Sul contratto da 1 € il tasso di riferimento potrebbe essere quello in euro, più basso: da verificare in piattaforma. La Fed ha lasciato i tassi al 3,75-4% il 28 ottobre 2026 ([Advisor Perspectives](https://www.advisorperspectives.com/dshort/updates/2026/10/28/feds-interest-rate-decision-october-28-2026?topic=inflation)).
- **Dividendi**: i long ricevono e gli short pagano l'aggiustamento per i dividendi dell'indice.
- **Il backtest di ProRealTime usa uno spread fisso** e non include il finanziamento.

## A – Utilizzabile

### A1. Il rendimento degli indici USA si forma di notte, soprattutto all'apertura europea
- **Fatto.** Sui futures S&P 500, Nasdaq 100 e Dow dal 1998 al 2020 il rendimento più alto della giornata cade tra le 08:00 e le 09:00 ora italiana (02:00-03:00 a New York), all'apertura dei mercati europei, ed è più forte dopo le giornate di vendite a Wall Street (Boyarchenko, Larsen, Whelan, *Review of Financial Studies* 2023, [working paper](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)). **Dal 2021 al 2025 quell'ora ha reso circa zero**, secondo gli stessi autori, perché gli squilibri di fine giornata si sono ridotti ([Liberty Street Economics, luglio 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)).
- **Contesto più ampio.** Sulle azioni USA quasi tutto il rendimento storico è arrivato tra la chiusura e l'apertura (Cliff, Cooper, Gulen 2008, citato da [Alpha Architect](https://alphaarchitect.com/2015/02/overnight-momentum-vs-intraday-momentum/); non letto), e notte e giorno sono dominati da clientele diverse che spesso tirano in direzioni opposte (Lou, Polk, Skouras, *Journal of Financial Economics* 2019, [PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf); letto solo il riassunto).
- **Meccanismo.** I market maker assorbono a fine giornata gli ordini di vendita e si liberano del rischio quando arrivano gli operatori europei; il rialzo è quindi un compenso per il rischio di tenere le posizioni di notte.
- **Perché conta.** Il long del lunedì tiene quattro notti ed esce il venerdì a un'ora che dipende dall'ingresso. Lo short tiene la notte dopo una giornata di vendite, proprio la notte in cui il rialzo è stato più forte.
- **In ProRealCode.** Uscite a orario con `Time` e un contatore dei giorni dall'ingresso. Ipotesi H1 e H2.

### A2. Il movimento della giornata prosegue fino alla chiusura (momento intraday)
- **Fatto.** Sull'ETF dello S&P 500 il rendimento dalla chiusura di ieri alla prima mezz'ora prevede quello dell'ultima mezz'ora, di più con volatilità alta (Gao, Han, Li, Zhou 2018); su oltre 60 futures, indici azionari compresi, il rendimento del resto della giornata prevede l'ultima mezz'ora, e il movimento si inverte in parte nei giorni successivi (Baltussen, Da, Lammers, Martens 2021). Entrambi in `fonti/paper/schede.md`.
- **Meccanismo.** Chi ha esposizione gamma negativa (market maker di opzioni, ETF a leva) vende quando il prezzo scende e compra quando sale.
- **Dopo il 2022.** Con la crescita delle opzioni a scadenza giornaliera (0DTE) ci si chiedeva se i market maker amplificassero i movimenti; Dim, Eraker e Vilkov trovano che la loro esposizione gamma su queste opzioni non propaga la volatilità, e secondo Cboe è vicina a zero perché i flussi si compensano (riassunti di [Harbourfront Quant](https://harbourfrontquant.substack.com/p/impact-of-zero-dte-options-on-the) e [Cboe](https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options); paper non letto). Contesto, non diventa codice.
- **Perché conta.** Lo short vende durante la seduta americana dopo un calo dall'apertura della giornata: è la forma tipica del momento intraday, come gli short del DAX (V4 di `idee/idee-di-trading.md`), che rendevano 31 € a trade nei periodi agitati e 7 € in quelli calmi.
- **In ProRealCode.** Modulo `moduli/filtro-regime-volatilita.txt`; uscita alla chiusura americana con `Time`. Ipotesi H2 e H3.

### A3. Flussi di fine mese: vendite prima, acquisti a cavallo del cambio di mese
- **Fatto.** Fondi pensione e istituzioni vendono azioni nei giorni prima della fine del mese per avere liquidità per i pagamenti, e chi riceve i pagamenti reinveste nei giorni successivi: nei mercati liquidi di tutto il mondo i rendimenti sono bassi da 8 a 4 giorni di borsa prima dell'ultimo e alti nei sette giorni successivi, cambio di mese compreso (Etula, Rinne, Suominen, Vaittinen, *Review of Financial Studies* 2020, [testo](https://acris.aalto.fi/ws/portalfiles/portal/40965155/hhz054.pdf); letti riassunto e diapositive). Negli USA l'ultimo giorno del mese e i primi tre rendono circa lo 0,15% al giorno (McConnell, Xu 2008, in `fonti/paper/schede.md`); sui futures USA l'effetto c'era dal 1993 al 2009, con i giorni spostati in avanti (Dzhabarov, Ziemba 2010, [scheda](https://ideas.repec.org/h/wsi/wschap/9789814405461_0016.html)).
- **Contro.** Maberly e Waggoner non lo trovano più dopo il 1990 sull'S&P 500 a contanti e sui futures ([Fed di Atlanta, 2000](https://ideas.repec.org/p/fip/fedawp/2000-11.html)). Le prove sono in conflitto, quindi la direzione va dichiarata prima del test.
- **Collegamento con il lunedì.** Il rendimento negativo del lunedì negli USA (1962-1993) si concentra nelle ultime due settimane del mese; nelle prime tre il lunedì medio non è diverso da zero (Wang, Li, Erickson, *Journal of Finance* 1997, [scheda](https://ideas.repec.org/a/bla/jfinan/v52y1997i5p2171-86.html)). È la stessa finestra delle vendite di fine mese di Etula e coautori.
- **Perché conta.** Il long del lunedì cade una volta al mese circa nella finestra delle vendite (giorni da −8 a −4) e una volta su quattro o cinque vicino al cambio di mese. Andrea ha visto ingressi validi anche negli altri giorni: i giorni del cambio di mese sono quelli con la ragione più solida per aggiungerli.
- **In ProRealCode.** Conteggio dei giorni di borsa con `Day`, `Month`, `Year`, `DayOfWeek` e un ciclo `FOR`, come in 165 DAX M3 (festività escluse dal conteggio solo se cadono nel fine settimana). Ipotesi H5 e H6.

### A4. Esposizione ridotta quando la volatilità è alta
- **Fatto.** Sull'indice azionario USA scalare l'esposizione per l'inverso della volatilità recente alza il rapporto rendimento/rischio (Moreira, Muir 2017); su oltre 60 strumenti riduce sempre le code, e il miglioramento è netto proprio su azioni e credito (Harvey et al. 2018). Entrambi in `fonti/paper/schede.md`; su 103 strategie azionarie il vantaggio non è sistematico fuori campione (Cederburg et al. 2020).
- **Perché conta.** Il long resta aperto fino a quattro giorni con uno stop al 4%, circa una volta e mezza il movimento di quattro giorni: quanto perde, e quanto spesso arriva allo stop, dipende dalla volatilità di quei giorni. Sullo short di 128 BIAS HOUR, che esce a tempo, la taglia a volatilità ha ridotto il drawdown del 25% (V3); con uno stop stretto ha peggiorato (M2 dello stesso sistema).
- **In ProRealCode.** Modulo `moduli/taglia-volatilita-uscita-a-tempo.txt`, con la volatilità giornaliera invece di quella oraria. Ipotesi H4.

## B – Plausibile, da usare con cautela

### B1. Effetto lunedì
- Storicamente negli USA il lunedì rendeva meno degli altri giorni, soprattutto per il tratto tra la chiusura del venerdì e l'apertura del lunedì; dagli anni '90 l'effetto si è indebolito o è sparito sui titoli a grande capitalizzazione (Pace University, indici per decili NYSE-AMEX e NASDAQ 1973-2007, [working paper](https://activityinsight.pace.edu/mmorey/intellcont/7117-1.pdf); [Arizona State University 2017](https://news.wpcarey.asu.edu/20171204-research-debunks-myth-stock-market-weekend-effect), comunicato stampa). Uno studio specifico sul Nasdaq 100 non l'ho trovato.
- **Perché conta.** La scelta del lunedì viene dal backtest di Andrea, non da un meccanismo: il long potrebbe essere in buona parte il rialzo di fondo del Nasdaq (circa sei volte dal 2015) preso un giorno a settimana, con il lunedì scelto perché era il migliore dei cinque.

### B2. Filtro di trend sugli indici azionari
- Sul Dow Jones dal 1897 al 1986 i rendimenti dopo i segnali di vendita delle medie mobili sono stati negativi e più volatili di quelli dopo i segnali di acquisto (Brock, Lakonishok, LeBaron, *Journal of Finance* 1992, [scheda](https://ideas.repec.org/a/bla/jfinan/v47y1992i5p1731-64.html)).
- **Perché conta.** Se il long vive del rialzo di fondo, sotto la media dei 200 giorni (2022) dovrebbe guadagnare meno. Su AUDJPY il filtro di trend non ha aiutato un sistema di calendario (S1) e sull'oro non ha aiutato lo short (S5), ma lì il rialzo di fondo non era la fonte del guadagno. Da provare se M3 mostra che il long rende meno nei periodi agitati. Ipotesi H7.

### B3. Rialzo prima delle decisioni FOMC
- Scomparso negli USA dopo il 2015 (`fonti/paper/schede.md`). Il long del lunedì è aperto il mercoledì della FOMC, quindi la prende quasi sempre, ma l'effetto è sparito; lo short del mercoledì può entrare alle 20:00, nel minuto della decisione, ma succede meno di una volta l'anno. Non diventa proposta.

## C – Contesto

- **Regimi e crolli**: 2000-2002 (−80% circa), 2008, febbraio-marzo 2020, 2022 (anno di ribasso con volatilità alta), aprile 2025 (dazi USA), ottobre-novembre 2026 (correzione oltre il 10% dal massimo del 6 ottobre).
- **Lunedì di crollo recenti** (a memoria, da verificare): 9 e 16 marzo 2020, 5 agosto 2024 (chiusura dei carry trade sullo yen), 27 gennaio 2025 (DeepSeek), 7 aprile 2025. Sono la prova di resistenza del long del lunedì: lo stop al 4% è stato vicino o raggiunto.
- **Lunedì festivi USA** (Martin Luther King, Presidents' Day, Memorial Day, Labor Day): la borsa a contanti è chiusa, IG quota con i futures a orario ridotto. Circa 4 long l'anno partono in un mercato sottile.
- **Opzioni 0DTE**: dal 2022 una parte grande delle opzioni sugli indici USA scade in giornata; l'effetto sul momento intraday è discusso (A2).

---

## Ipotesi per i tentativi

Direzione dichiarata prima del test.

| Id | Ipotesi | Direzione attesa | Esito |
|---|---|---|---|
| H1 | Il guadagno del long del lunedì sta soprattutto nelle prime 24 ore (dai report per giorno di Andrea, non da una fonte indipendente); la notte fino all'apertura europea aggiunge (A1) | uscita il martedì sera con guadagno medio molto più alto di un quarto dell'originale e profitto / drawdown più alto | **M1: smentita**: il tratto da martedì sera a venerdì rende 74 € a trade su 165, e uscire prima alza il drawdown |
| H2 | La notte dello short, dopo una giornata di vendite, va contro il rialzo notturno (A1) e il movimento si inverte in parte il giorno dopo (A2) | uscire alla chiusura americana dello stesso giorno alza il guadagno medio e abbassa il drawdown | **M2: smentita**: 60 € a trade fino alla chiusura, 99 € nei giorni dopo |
| H3 | Lo short è momento intraday e rende di più nei periodi agitati (A2) | guadagno medio degli short tenuti più alto di quello degli scartati | **M3: confermata** (242 contro 100 €, 2,3 volte l'incertezza), ma gli scartati sono positivi; anche il long rende di più nei periodi agitati (226 contro 128 €) |
| H4 | Il long esce a tempo con stop lontano: la taglia inversa alla volatilità riduce il drawdown (A4) | drawdown più basso, profitto simile, profitto / drawdown più alto | M4: effetto piccolo (profitto −3%, drawdown −7%), dentro il rumore |
| H5 | I giorni del cambio di mese rendono più degli altri (A3) | long aggiunti in quei giorni con guadagno medio almeno pari a quello dei lunedì | **M5: smentita**: 118 long aggiunti, −34 € a trade |
| H6 | I lunedì della finestra delle vendite di fine mese (giorni −8 a −4) rendono meno (A3) | long scartati con guadagno medio più basso dei tenuti | non provata |
| H7 | Il long rende meno sotto la media dei 200 giorni (B2) | guadagno medio dei long scartati più basso | non ancora |
| H8 | Il finanziamento vale circa lo 0,02% del valore della posizione per notte sul long, che ne tiene quattro (costi) | va sottratto al guadagno medio del long letto nel backtest | da calcolare sul report |
