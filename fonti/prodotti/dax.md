# DAX (Germany 40 su IG) – ricerca sul prodotto

Ricerca del 2026-11-20, ampliata il 2026-11-21 per 138 DAX (sezione "Ore notturne, giorni della settimana e inversioni"). Orari in ora italiana (CET d'inverno, CEST d'estate). Il DAX era a circa 26.700 punti a metà novembre 2026 ([Trading Economics](https://tradingeconomics.com/germany/stock-market/news/601246), chiusura del 13 novembre).

**Gradi** (come in `README.md` di questa cartella)
- **A**: meccanismo chiaro, fonte solida, traducibile in ProRealCode.
- **B**: plausibile ma con fonte debole, oppure solo in parte traducibile.
- **C**: contesto, non diventa codice.

---

## Orari e calendario

| Evento | Ora italiana | Fonte |
|---|---|---|
| Futures FDAX su Eurex | 01:10–22:00; prima del 10 dicembre 2018 aprivano al mattino (circa 08:00) | dati ufficiali, [Eurex](https://www.eurex.com/dax/), [estensione 2018](https://eurex.com/ex-en/support/initiatives/archive/trading-hour-extension) |
| Borsa a contanti Xetra | 09:00–17:30, asta di chiusura subito dopo le 17:30 | dati ufficiali (Deutsche Börse), non riletti in questa ricerca |
| Dati macro USA (occupazione, inflazione) | 14:30 | calendario ufficiale USA |
| Apertura di Wall Street | 15:30 | idem |
| Decisione BCE / conferenza stampa | 14:15 / 14:45 dal 21 luglio 2022; prima 13:45 / 14:30 | dati ufficiali, [BCE](https://www.ecb.europa.eu/press/pr/date/2022/html/ecb.pr220627~73acedf868.en.html) |
| Decisione FOMC | 20:00, di solito il mercoledì | calendario Fed |
| Scadenza mensile di futures e opzioni sul DAX | terzo venerdì, asta intraday di Xetra delle 13:00 | dati ufficiali, [Eurex FDAX](https://www.eurex.com/ex-en/markets/idx/dax/DAX-Futures-34642) |

- **Settimane con ora legale sfasata.** Gli USA cambiano l'ora la seconda domenica di marzo e la prima di novembre, l'Europa l'ultima domenica di marzo e di ottobre. In quelle circa tre settimane l'anno i dati USA escono alle 13:30 e Wall Street apre alle 14:30 ora italiana, e la FOMC decide alle 19:00.
- **Il DAX è un indice di performance**: i dividendi sono reinvestiti nell'indice, quindi non cade alle date di stacco come l'Euro Stoxx 50 o lo S&P 500 (banca, [Sparkasse](https://www.sparkasse.at/investments-en/service-knowledge/services/securities-know-how/performance-index); [Wikipedia](https://en.wikipedia.com/wiki/DAX)). Da settembre 2021 ha 40 titoli invece di 30.

## Costi su IG

Fonti: [IG Svizzera, dettagli CFD indici](https://www.ig.com/en-ch/indices/indices-cfd-details) (orari in CET) e [IG UK, finanziamento overnight](https://www.ig.com/uk/help-and-support/spread-betting-and-cfds/fees-and-charges/why-is-overnight-funding-charged-and-how-is-it-calculated-); broker, pagine di altre sedi IG. La pagina italiana non era raggiungibile: verificare in piattaforma ("Info").

- **Contratto Germany 40 Cash**: 1 € per punto; la taglia minima "di solito parte da un contratto". Margine 0,5%, a scaglioni. Quotato 24 ore, da lunedì 00:02 a venerdì 23:00.
- **Spread per fascia oraria (punti)**:

| Fascia | Spread |
|---|---|
| 01:15–08:00 | 5 |
| 08:00–09:00 | 3,8 |
| 09:00–17:30 | 1,6 (variabile) |
| 17:30–22:00 | 3,8 |
| 22:00–01:15 | 7 |

- **Finanziamento overnight**: si paga sulle posizioni aperte alle 23:00, con la formula contratti × prezzo × (3% + tasso di riferimento in euro) / 360; il venerdì vale per tre giorni. Con il DAX a 26.700 e un tasso di riferimento attorno al 2% (da verificare), un contratto long paga circa 3,7 € a notte.
- **Il backtest di ProRealTime usa uno spread fisso** e non include il finanziamento.

## A – Utilizzabile

### A1. Il movimento della mattina tende a proseguire nel pomeriggio (momento intraday)
- **Fatto.** Sullo S&P 500 dal 1993 al 2013 il rendimento dalla chiusura precedente alla prima mezz'ora prevede quello dell'ultima mezz'ora; l'effetto cresce con la volatilità e i volumi, nelle recessioni e nei giorni di dati macro (Gao, Han, Li, Zhou, *Journal of Financial Economics* 2018, [scheda](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)). Lo stesso legame si trova in 12 di 16 borse sviluppate, più forte con volatilità alta, liquidità bassa e notizie concentrate (Li, Sakkas, Urquhart, *Journal of Financial Markets* 2022, [scheda](https://ideas.repec.org/a/eee/finmar/v57y2022ics138641812100001x.html)); i numeri per la Germania non li ho letti, il testo integrale non era raggiungibile.
- **Meccanismo.** Su oltre 60 futures dal 1974 al 2020 il momento intraday dipende da chi deve coprirsi comprando quando il prezzo sale e vendendo quando scende, soprattutto i market maker di opzioni con esposizione gamma negativa e gli ETF a leva; quando l'esposizione gamma dei market maker è positiva l'effetto sparisce, e nei giorni successivi il movimento si inverte in parte (Baltussen, Da, Lammers, Martens, *Journal of Financial Economics* 2021, [scheda](https://pure.eur.nl/en/publications/hedging-demand-and-market-intraday-momentum/)).
- **Perché conta.** È la spiegazione più plausibile di 165 DAX: il long compra alle 13:30 dopo una mattina in salita, lo short vende alle 12:30 dopo una mattina in discesa.
- **In ProRealCode.** Ampiezza del movimento dalla chiusura del giorno prima, `(close - DClose(1))`, divisa per l'escursione media giornaliera; regime di volatilità con `AverageTrueRange` su `TIMEFRAME(daily)`. Ipotesi H1 e H2.

### A2. Fine mese: le borse salgono nell'ultimo giorno e nei primi tre del mese
- **Fatto.** In 31 borse su 35 il rendimento dei quattro giorni attorno al cambio di mese è più alto degli altri giorni; negli USA 0,15% al giorno (indice ponderato per capitalizzazione), e l'effetto non si spiega con un rischio più alto (McConnell, Xu, *Financial Analysts Journal* 2008, [scheda](https://econpapers.repec.org/RePEc:taf:ufajxx:v:64:y:2008:i:2:p:49-64)).
- **Germania.** Sulle azioni tedesche la stagionalità è legata soprattutto alla liquidità e la finestra si è spostata a 4 giorni prima e 2 dopo la fine del mese (Weigerding, Hanke, *Business Research* 2018, [testo](https://link.springer.com/article/10.1007/s40685-017-0060-0)). Sul DAX l'effetto è stato trovato il primo giorno del mese (Nikkinen e altri, citato in [questo studio](https://virtusinterpress.org/IMG/pdf/cocv15i1art9.pdf)).
- **Perché conta.** Lo short di 165 DAX aperto in quei giorni va contro un flusso in acquisto documentato.
- **In ProRealCode.** Con `Day`, `Month`, `Year`, `DayOfWeek` si contano i giorni di borsa dall'inizio e alla fine del mese (sabati e domeniche esclusi, festività no). Ipotesi H3.

### A3. Gestire la taglia con la volatilità
- **Fatto.** Ridurre l'esposizione quando la volatilità recente è alta riduce code e drawdown su tutti gli strumenti, e sulle azioni migliora anche il rapporto rendimento/rischio (Harvey et al. 2018; Moreira-Muir 2017, entrambi in `fonti/paper/schede.md`). Su 103 strategie azionarie il miglioramento non è sistematico fuori campione (Cederburg et al., *Journal of Financial Economics* 2020, [scheda](https://econpapers.repec.org/RePEc:eee:jfinec:v:138:y:2020:i:1:p:95-117)).
- **Perché conta.** Le due gambe di 165 DAX escono a tempo con stop lontani, come lo short di 128 BIAS HOUR dove il modulo ha funzionato.

## B – Plausibile, da usare con cautela

### B1. Rialzo all'apertura europea ("overnight drift")
- Sui futures S&P 500 quasi tutto il premio azionario si è guadagnato tra le 08:00 e le 09:00 ora italiana, all'apertura dei mercati europei (3,7% l'anno); il rialzo è forte dopo le giornate di vendite a Wall Street e modesto dopo i rialzi (Boyarchenko, Larsen, Whelan, *Review of Financial Studies* 2023, [working paper](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)).
- **Dal 2021 al 2025 l'effetto è sparito**, secondo gli stessi autori: rendimento di quell'ora vicino a zero ([Liberty Street Economics, luglio 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)).
- **Coincidenza.** Il long di 165 DAX esce alle 08:00, proprio all'inizio di quell'ora. Lo studio riguarda futures americani; per il DAX è un'ipotesi.

### B2. Rialzo prima delle decisioni FOMC
- Nelle 24 ore prima delle decisioni FOMC le borse hanno reso molto più della media dal 1994 al 2011, anche il DAX (coefficiente 0,46% nella tabella internazionale) (Lucca, Moench, *Journal of Finance* 2015, [slide](https://www.bostonfed.org/economic/conf/Macro-Finance-2012/presentations/lucca.pdf)). Dopo il 2015 l'effetto negli USA è quasi scomparso (Kurov, Wolfe, Gilbert, *Finance Research Letters* 2021, [scheda](https://ideas.repec.org/a/eee/finlet/v40y2021ics1544612320315956.html)); per il DAX non ho trovato verifiche recenti.
- **Coincidenza.** Lo short del mercoledì (12:30–19:30) copre quasi tutta la finestra del rialzo, e chiude 30 minuti prima della decisione.
- **Limite.** Servono le date FOMC scritte nel codice, circa 8 l'anno.

### B3. Scadenze del terzo venerdì
- Lo short del venerdì entra alle 12:30, mezz'ora prima dell'asta che fissa il prezzo di liquidazione di futures e opzioni. Effetti di prezzo attorno alle scadenze sono documentati in letteratura, ma non ho trovato una direzione stabile per il DAX: non diventa proposta.

## C – Contesto

- **Rendimento notturno del DAX**: dal 1994 circa 0,04% al giorno in più rispetto alle ore di borsa, prima dei costi (analisi di [stock3](https://stock3.com/boersenwissen/overnight-effect-an-der-boerse-schlafend-geld-verdienen-11991899), blog). Su IG, il finanziamento di una notte su un contratto (circa 3,7 €) vale circa 0,014% del prezzo.
- **Effetto lunedì**: non trovato sul DAX tra il 2000 e il 2017 (replica del 2024, [record](https://katalog.lib.cas.cz/KNAV/EdsRecord/edo,ejs50450220)).
- **Effetto "Sell in May" / Halloween** (Bouman-Jacobsen 2002): differenza di rendimento tra i semestri dell'ordine di 0,03-0,05% al giorno, troppo piccola rispetto al risultato di un singolo trade per essere misurata su qualche centinaio di operazioni.
- **Episodi da usare come prova di resistenza**: agosto 2011, 24 agosto 2015, giugno 2016 (Brexit), marzo 2020, febbraio-marzo 2022, 5 agosto 2024, aprile 2025 (dazi USA).

---

## Ore notturne, giorni della settimana e inversioni (aggiunta del 2026-11-21, per 138 DAX)

### Sessione asiatica dei futures (dati ufficiali)
- **Dal 10 dicembre 2018** l'FDAX tratta anche nelle ore asiatiche. Pre-apertura 01:00–01:10 e negoziazione continua dalle 01:10 in inverno; d'estate le stesse fasi cadono un'ora dopo, 02:00–02:10 e dalle 02:10, perché l'apertura segue l'orario di Singapore, che non ha l'ora legale (Eurex, [documento del 2019](https://eurexrepo.com/resource/blob/1493194/bee8965900f0124d7ff7c7993d5f969b/data/2019_02_25_cs_4_history.pdf); [presentazione 2024](https://eurex.com/resource/blob/2845114/41f41c0f8fbb08da59926d07193e5877/data/presentation_trading-hours-extension.pdf), che indica le ore asiatiche 02:15–08:00 CEST). Prima del 2018 il prezzo notturno di IG non aveva dietro un futures aperto.
- **Volumi.** Nel 2024 l'FDAX ha scambiato in media 1.393 contratti al giorno nelle ore asiatiche su 53.605 dell'intera giornata, circa il 2,6% (calcolo mio sui numeri della presentazione Eurex di aprile 2024, stesso link).
- **Perché conta.** Un pattern costruito sulle barre orarie tra l'01:00 e le 04:00 misura movimenti di un mercato quasi vuoto, con lo spread IG a 5 punti, e d'estate e d'inverno guarda momenti diversi: la barra 01:00-02:00 contiene l'apertura dei futures solo d'inverno.

### Giorni della settimana (studi accademici)
- Sul DAX dal 2000 al 2017 non c'è un effetto lunedì stabile, prima, durante e dopo la crisi finanziaria (Miss, Charifzadeh, Herberger, *Management Review Quarterly* 2020, [scheda](https://ideas.repec.org/a/spr/manrev/v70y2020i2d10.1007_s11301-019-00167-4.html)). Sull'indice di Francoforte la dipendenza dal giorno della settimana c'era nel 1960-79 e si indebolisce molto dal 1980 (Herwartz 1999, [working paper](https://econpapers.repec.org/RePEc:zbw:sfb373:199947)).
- **Martedì.** Non ho trovato studi che documentino un martedì negativo sul DAX. Martedì negativi sono stati trovati in Giappone e Australia e attribuiti al fuso orario, perché lì il martedì riflette il lunedì americano (Jaffe, Westerfield 1985, citati in [Borges 2009](https://core.ac.uk/download/61453004.pdf)).
- Negli USA il rendimento del lunedì dipende da quello del venerdì: dopo un venerdì negativo il lunedì è negativo quasi l'80% delle volte, con vendite dei piccoli investitori il lunedì mattina (Abraham, Ikenberry, *Journal of Financial and Quantitative Analysis* 1994, [scheda](https://ideas.repec.org/a/cup/jfinqa/v29y1994i02p263-277_00.html)). È prosecuzione da un giorno al successivo, non inversione.

### Inversione da un giorno all'altro (studio accademico; testimonianze)
- Su 20 indici di 15 paesi l'autocorrelazione dei rendimenti giornalieri, positiva fino agli anni '90, è diventata negativa dal 1999, e la causa indicata è la diffusione di futures ed ETF, che con l'arbitraggio trasmettono all'indice pressioni di prezzo non legate a notizie (Baltussen, van Bekkum, Da, *Journal of Financial Economics* 2019, [testo](https://www3.nd.edu/~zda/Indexing.pdf), tabella 1). **Sul DAX però l'effetto giornaliero è piccolo**: autocorrelazione giornaliera 0,066 dal 1959 al marzo 1999, −0,016 dal 1999 al 2016, non significativa; quella settimanale passa da 0,008 a −0,102, significativa. Media dei 20 indici: da 0,094 a −0,026 al giorno.
- **"Turnaround Tuesday"** (testimonianze e analisi di broker, solo per generare ipotesi): sullo S&P 500 dal 2010, dopo un lunedì sotto −1,5% il martedì ha reso in media +0,9% contro +0,1% degli altri martedì ([Schaeffer's Research 2021](https://schaeffersresearch.com/content/analysis/2021/09/22/is-turnaround-thursday-a-real-thing)); risultati simili dopo tre sedute in calo ([Bloomberg 2024](https://www.bloomberg.com/news/articles/2024-08-06/turnaround-tuesday-can-prove-lucrative-but-not-always-durable)). Nessuno studio accademico trovato.
- **Collegamento con B1.** Sui futures USA il rialzo all'apertura europea era forte dopo le giornate di vendite (Boyarchenko, Larsen, Whelan 2023). Un long che tiene la mattina del martedì dopo un lunedì in forte calo raccoglie quel tratto; sul DAX 2015-2026 l'ora 08:00-09:00 è risultata positiva per i long di 165 DAX (M11).
- **Grado complessivo: B.** L'inversione dopo un forte calo ha un meccanismo (pressione di prezzo che rientra, rialzo all'apertura europea dopo le vendite), ma sul DAX l'autocorrelazione giornaliera media è vicina a zero: un effetto, se c'è, sta nei giorni di movimento grande, che lo studio non separa.

### Costi: taglia minima
- Le pagine IG di Svizzera e Singapore indicano per il Germany 40 da 1 € una taglia minima di 0,05, quelle di Regno Unito e Irlanda 0,10-0,20 sul contratto da 25 € ([IG Svizzera](https://www.ig.com/en-ch/indices/markets-indices/germany-40); broker). Le pagine sono etichettate in modo incoerente: la taglia minima del conto italiano va letta in piattaforma. I codici di Andrea usano un minimo di 1 contratto.

---

## Pomeriggio e apertura americana (aggiunta del 2026-11-21, per 3251 FDAX 5m)

Riguarda la finestra 14:00–17:30, con i dati americani delle 14:30, l'apertura di Wall Street alle 15:30 e la chiusura di Xetra alle 17:30.

### Calo dei futures americani attorno all'apertura di New York (studio accademico)
- Sui futures E-mini S&P 500 dal 1998 al 2020 i rendimenti sono negativi dalla mezz'ora prima dell'apertura delle 9:30 fino alle 12:00 di New York, cioè dalle 15:00 alle 18:00 italiane; l'ora 9:00–10:00 vale in media −1,2 punti base al giorno (t 2,6) (Boyarchenko, Larsen, Whelan, *Review of Financial Studies* 2023, [working paper rivisto nel 2022](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf), sezione II e appendice B).
- **Per giorno della settimana** (appendice, tabella A.5): nell'ora dell'apertura giovedì −2,10 punti base (t −2,02) e venerdì −3,03 (t −2,76), gli unici significativi; lunedì −1,21 non significativo, martedì e mercoledì vicini a zero. Nell'ora prima (8:00–9:00 di New York, 14:00–15:00 italiane) giovedì e venerdì sono positivi, +0,93 e +1,48, non significativi.
- **Nel tempo e per regime**: forte e significativo dal 1998 al 2010, leggermente positivo e non significativo dal 2011 al 2020; negativo in modo persistente nelle recessioni e nelle crisi (2000-2003, 2007-2008, 2020), piatto negli altri anni.
- **Spiegazione degli autori, solo come congettura**: il giovedì e il venerdì escono più dati americani alle 8:30, con rialzo prima dell'annuncio e breve rientro dopo; nell'ora dei dati il rendimento medio è +3,22 punti base (t 2,29). Le decisioni FOMC, precedute da rialzi che non rientrano, cadono quasi sempre di mercoledì. I risultati societari negativi si concentrano il giovedì e il venerdì.
- **Grado: B.** Studio solido, ma sui futures americani, con meccanismo non dimostrato e indebolito dopo il 2010. Il DAX nel pomeriggio si muove con i futures americani (legami contemporanei forti tra mercati americani, tedeschi e inglesi attorno ai dati delle 8:30 di New York: Andersen, Bollerslev, Diebold, Vega, *Journal of International Economics* 2007, [scheda](https://www.nber.org/papers/w11312)), ma l'effetto sul DAX non è stato misurato da nessuno studio che ho trovato.

### Di giorno gli indici non salgono (studi accademici; preprint)
- Sui futures E-mini S&P 500 dal 2004 al 2018 le quattro ore attorno all'apertura europea fanno tutto il rendimento medio; le altre 20 ore sono uno zero rumoroso (Bondarenko, Muravyev, *Journal of Financial and Quantitative Analysis* 2023, [scheda](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/market-return-around-the-clock-a-puzzle/089E33AC0B4D3B9A02CBA31EDF6505B3)).
- Su 21 indici in trent'anni i rendimenti notturni sono positivi e quelli di seduta negativi, salvo la Cina (Knuteson, [arXiv 2020](https://arxiv.org/pdf/2010.01727), preprint con un'interpretazione contestata); sul DAX i rendimenti notturni superano quelli di seduta (capitolo Springer 2020 su WIG20 e DAX, [scheda](https://ideas.repec.org/h/spr/prbchp/978-3-030-43078-8_1.html), letto solo il riassunto).
- **Grado: C.** Contesto: uno short di seduta non va contro una deriva al rialzo, ma da questo non nasce una direzione per le ore del pomeriggio.

### Momento fino alla chiusura della borsa a contanti (studio accademico)
- Nello studio di Baltussen, Da, Lammers, Martens (2021, A1) c'è il futures sul DAX, tra 8 futures europei, e le ore usate sono quelle della borsa a contanti, perché è lì che si chiudono le coperture: per il DAX conta l'ultima mezz'ora di Xetra (17:00–17:30), non la chiusura dei futures alle 22:00. Il risultato del gruppo europeo è significativo; quello del solo DAX non l'ho letto.
- **Perché conta.** Uno short del pomeriggio in una giornata in calo ha la spinta delle coperture fino alle 17:30; nei giorni successivi il movimento si inverte in parte.

### Dati americani e giornate di annuncio (studi accademici)
- Negli USA dal 1958 al 2009 i giorni con dati su inflazione, occupazione e decisioni FOMC rendono in media 11,4 punti base contro 1,1 degli altri giorni (Savor, Wilson, *Journal of Financial and Quantitative Analysis* 2013, [scheda](https://ideas.repec.org/a/cup/jfinqa/v48y2013i02p343-375_00.html)).
- Il premio delle riunioni FOMC c'è sulle borse di tutto il mondo; per BCE, Banca d'Inghilterra e Banca del Giappone non c'è un risultato simile, neanche sulle borse dei loro paesi (Brusa, Savor, Wilson, *Review of Finance* 2020, [scheda](https://ideas.repec.org/a/oup/revfin/v24y2020i2p263-304..html); BCE dal 1999 al 2016). I giovedì della BCE non danno una direzione allo short.
- La reazione delle borse ai dati americani cambia segno con il ciclo: nelle espansioni una buona notizia sull'economia fa scendere le azioni, nelle recessioni salire (Andersen et al. 2007, sopra).
- **Grado: B** per i venerdì dei dati sull'occupazione (di solito il primo venerdì del mese, alle 14:30 italiane), dove lo short va contro il premio delle giornate di annuncio; pochi trade, circa 5 l'anno.

### Regole scelte tra molte (studio accademico)
- Sulle regole di calendario delle borse americane in 100 anni di dati, risultati molto significativi presi uno per uno non lo sono più quando si tiene conto delle circa 9.500 regole da cui sono stati scelti (Sullivan, Timmermann, White, *Journal of Econometrics* 2001, [scheda](https://econpapers.repec.org/RePEc:eee:econom:v:105:y:2001:i:1:p:249-286)).
- **Perché conta.** 3251 viene da un generatore di regole (AlphaMining) e i giorni sono stati scelti dopo sul backtest: il backtest sovrastima, e i moduli servono a verificare i meccanismi più che a migliorare il numero.

### Costi del pomeriggio
- Le pagine IG di Regno Unito e Sudafrica indicano per il Germany 40 uno spread di 1,2 punti dalle 08:00 alle 16:30 di Londra (09:00–17:30 italiane), 2 punti fino alle 21:00 di Londra e 5 di notte ([IG UK](https://ig.com/uk/help-and-support/spread-betting-and-cfds/fees-and-charges/what-are-igs-indices-cfd-product-details); broker); la pagina svizzera usata sopra indica 1,6. Valori del contratto a contanti: per il CFD sui futures lo spread va letto in piattaforma.

---

## Ipotesi per i tentativi

Direzione dichiarata prima del test.

| Id | Ipotesi | Direzione attesa | Esito |
|---|---|---|---|
| H1 | I trade con un movimento della giornata ampio, nella stessa direzione del trade, proseguono di più (A1) | guadagno medio dei trade tenuti più alto di quello dei trade scartati | M4: no sul long; sullo short sì ma nel margine del caso |
| H2 | Il momento intraday è più forte nei periodi agitati (A1) | guadagno medio più alto nei periodi con volatilità sopra la media | **M5: confermata**, forte sullo short (31 contro 7 € a trade), più debole sul long |
| H3 | Gli short a cavallo di fine mese vanno contro un flusso in acquisto (A2) | guadagno medio degli short a fine mese più basso degli altri | M3: smentita (21,8 contro 17,2 €) |
| H4 | Taglia inversamente proporzionale alla volatilità (A3) | drawdown più basso, profitto simile | M2: test non confrontabile; contraddetta da H2 |
| H5 | Il long che esce alle 08:00 perde il rialzo dell'apertura europea (B1) | uscita alle 09:00 con guadagno medio più alto; poco probabile dopo il 2021 | **M11: confermata**, uscita alle 09:00 +11% sul long, anni dal 2021 ancora positivi |
| H6 | Niente short nei giorni FOMC (B2) | guadagno medio degli short più alto; circa 3 trade l'anno | non provata |
| H7 | Il long in guadagno alle 21:30 non ha più vantaggio nella notte | uscire la sera non toglie profitto e risparmia il finanziamento | M6: smentita, la notte dei long in guadagno ha reso 3.371 € |
| H8 | Nelle settimane con ora legale sfasata il long entra nel momento esatto dei dati USA | risultati più dispersi in quelle settimane; pochi trade, circa 5 l'anno | non provata |
| H9 | Il pattern notturno di 138 DAX (barre 01:00-04:00 del martedì) misura movimenti di un mercato quasi vuoto, grandi quanto lo spread | togliendolo, gli short aggiunti guadagnano quanto quelli tenuti | 138 M1: smentita, i 215 short aggiunti perdono 4 € a trade contro 56 € dei tenuti |
| H10 | Il filtro "lunedì non direzionale" di 138 DAX non ha una ragione economica | togliendolo, gli short aggiunti guadagnano quanto quelli tenuti | 138 M1 (variante): non lanciata |
| H11 | Lo short di 138 DAX tiene l'ora 08:00-09:00, che sul DAX è stata positiva (B1; 165 M11) | entrando alle 09:00 il guadagno medio sale più dei 3,4 punti di spread risparmiati | **138 M2: confermata**, il tratto 04:00-09:00 costava allo short 46,59 € a trade (posizione da 30.000 €), profitto / drawdown da 6,9 a 9,0: promosso |
| H12 | Lo short di 138 DAX esce alle 21:00 con lo spread a 3,8 punti | uscendo alle 17:00 si risparmiano 2,2 punti; direzione del tratto serale non prevista | 138 M2 (variante) non lanciata; riproposta come 138 M6 sopra C1 |
| H13 | Se lo short di 138 DAX è momento intraday, rende di più nei periodi agitati (A1) | guadagno medio degli short dei periodi agitati più alto; se non cambia, il vantaggio è di calendario | 138 M3: direzione giusta (133 contro 9 € a trade, 27 e 44 trade), ma drawdown quasi doppio: non adottato. Trade di M3 non tutti presenti nel riferimento, da verificare |
| H14 | Il martedì dopo un lunedì in forte calo il DAX recupera (inversione, rialzo all'apertura europea dopo le vendite; sezione sopra) | long del martedì dopo un forte calo con guadagno medio più alto degli altri martedì | 138 M4: positivo fino al 2021 (circa +4.900 €), negativo dal 2022 (circa −550 €); riferimento non lanciato. Smentita per gli anni recenti, come il rialzo all'apertura europea dopo le vendite sui futures USA |
| H15 | Lo short pomeridiano di 3251 vive del calo attorno all'apertura americana, più forte nelle crisi, o del momento intraday (A1; sezione "Pomeriggio") | short dei periodi agitati con guadagno medio più alto dei calmi; se uguale, il vantaggio è di calendario | 3251 M1: direzione giusta ma dentro l'incertezza (agitati 20,6 €, calmi 11,6 € a trade); i calmi sono positivi, quindi c'è anche una parte di calendario |
| H16 | L'ora 14:00–15:00, con i dati americani delle 14:30, in media sale | entrando alle 15:00 sugli stessi giorni il guadagno medio sale di pochi punti | 3251 M2: **smentita la direzione** (l'ora ha reso allo short 3,6 € a trade, non significativo), ma senza quell'ora il drawdown scende del 44% e profitto / drawdown sale da 7,2 a 10: promosso |
| H17 | Nelle giornate in calo il movimento prosegue fino alla chiusura di Xetra (A1) | tenendo fino alle 17:25 gli short delle giornate in calo il tratto aggiunto è positivo, per le giornate in salita è negativo | 3251 M3: smentita, tratto quasi nullo (179 € su 370 trade) e drawdown +21%; M8: il tratto 15:55–16:35 invece rende (2.186 €) |
| H18 | Il martedì non ha il calo dell'apertura americana, giovedì e venerdì sì | short del martedì con guadagno medio più basso di quelli di giovedì e venerdì | da leggere nel report per giorno di Andrea |
| H19 | Nei venerdì dei dati sull'occupazione USA lo short va contro il premio delle giornate di annuncio | guadagno medio più basso degli altri venerdì; circa 5 trade l'anno | non provata |
