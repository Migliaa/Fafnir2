# Schede dei paper

Ogni scheda: riferimento, dove leggerlo, l'idea in breve, come la usiamo, i limiti. Riassunti scritti da noi, non estratti.

## Dimensionamento e reinvestimento

### Kelly frazionario – MacLean, Thorp, Ziemba (2010)
"Long-term capital growth: the good and bad properties of the Kelly and fractional Kelly capital growth criteria", *Quantitative Finance*. PDF: https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf
- Investire una frazione fissa del capitale che massimizza la crescita logaritmica dà la crescita più alta nel lungo periodo, ma con oscillazioni nel breve periodo molto ampie; usare una frazione del Kelly pieno riduce le oscillazioni in cambio di meno crescita.
- **Uso:** M1, l'esponente di crescita sotto 1 si comporta come un Kelly frazionario.
- **Limiti:** richiede di conoscere il vantaggio vero del sistema, che dal backtest si sovrastima.

### Controllo del drawdown – Grossman, Zhou (1993)
"Optimal Investment Strategies for Controlling Drawdowns", *Mathematical Finance* 3(3), 241–276. https://ideas.repec.org/a/bla/mathfi/v3y1993i3p241-276.html
- Per non scendere mai sotto una frazione del massimo storico del capitale, l'esposizione va tenuta proporzionale alla distanza tra capitale attuale e quel pavimento.
- **Uso:** M1, freno sul drawdown.
- **Limiti:** in tempo discreto e con costi di transazione la proprietà di crescita ottimale non regge (Klass-Nowicki 2005), e il freno rallenta il recupero dopo un drawdown; per questo M1 ha una taglia minima.

## Volatilità

### Portafogli gestiti sulla volatilità – Moreira, Muir (2017)
"Volatility-Managed Portfolios", *Journal of Finance* 72(4), 1611–1644. https://www.nber.org/papers/w22208
- Ridurre l'esposizione quando la volatilità recente è alta e aumentarla quando è bassa migliora il rapporto rendimento/rischio su molti fattori azionari.
- **Uso:** M2. 185 NQ, M4 (taglia del long legata alla volatilità).
- **Limiti:** su 103 strategie azionarie il vantaggio non è sistematico fuori campione (Cederburg, O'Doherty, Wang, Yan, *Journal of Financial Economics* 2020, https://econpapers.repec.org/RePEc:eee:jfinec:v:138:y:2020:i:1:p:95-117).

### Impatto del volatility targeting – Harvey et al. (2018)
"The Impact of Volatility Targeting", *Journal of Portfolio Management* 45(1), 14–33. https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf
- Su oltre 60 strumenti, scalare per la volatilità riduce sempre le code e i drawdown; il miglioramento del rapporto rendimento/rischio c'è su azioni e credito, mentre **su valute è trascurabile**.
- **Uso:** M2 e M3. Su AUDJPY ci si aspetta una curva più regolare, non per forza più profitto.

## Valute e carry

### Carry trade e crolli valutari – Brunnermeier, Nagel, Pedersen (2008)
"Carry Trades and Currency Crashes", *NBER Macroeconomics Annual*. https://www.nber.org/papers/w14473
- Le coppie tra valuta ad alto tasso e valuta a basso tasso (AUDJPY è l'esempio tipico) hanno rendimenti con crolli improvvisi: quando volatilità e costo del finanziamento salgono, le posizioni vengono chiuse tutte insieme.
- **Uso:** M4, niente long su AUDJPY durante gli shock di volatilità.

### Momentum di serie storica – Moskowitz, Ooi, Pedersen (2012)
"Time Series Momentum", *Journal of Financial Economics* 104(2), 228–250. https://papers.ssrn.com/abstract=2089463
- Il rendimento passato di uno strumento (fino a 12 mesi) predice il segno del rendimento futuro, anche su valute.
- **Uso:** M5, filtro di direzione.
- **Limiti:** sulle valute il momentum tra coppie diverse ha funzionato meglio di quello sulla singola coppia (Menkhoff et al. 2012).

## Stop

### Quando gli stop riducono le perdite – Kaminski, Lo (2014)
"When Do Stop-Loss Rules Stop Losses?", *Journal of Financial Markets* 18, 234–254. https://dspace.mit.edu/handle/1721.1/114876
- Se i prezzi seguono un cammino casuale, uno stop riduce sempre il rendimento atteso; aggiunge valore solo se i rendimenti hanno inerzia dopo le perdite.
- **Uso:** M3. Uno stop stretto in percentuale fissa (0,4% sul long) in fasi agitate esce per rumore; legarlo alla volatilità riduce queste uscite.

### Stop con regimi e costi – Lo, Remorov (2017)
"Stop-loss strategies with serial correlation, regime switching, and transaction costs", *Journal of Financial Markets* 34, 1–15. https://dspace.mit.edu/handle/1721.1/107017
- Sulle azioni USA gli stop stretti perdono contro il buy-and-hold per i costi; possono vincere quando i rendimenti hanno correlazione seriale alta o quando il mercato alterna regimi persistenti.
- **Uso:** M7. Se il long funziona con uno stop stretto, è indizio che le settimane si dividono in buone e cattive e che la differenza si vede presto: è il presupposto per aggiungere ai long in guadagno.

## Teoria dei giochi e flussi prevedibili

### Trading predatorio – Brunnermeier, Pedersen (2005)
"Predatory Trading", *Journal of Finance* 60(4), 1825–1863. https://www.princeton.edu/~markus/research/papers/predatory_trading.htm
- Quando un operatore deve vendere e gli altri lo sanno, conviene loro vendere prima e ricomprare dopo: la liquidazione costa di più, il prezzo va oltre il valore giusto e poi rientra.
- **Uso:** M11. Se una parte del mercato riduce le posizioni su AUDJPY prima di ogni weekend, lo short del giovedì vende prima di loro e il long del lunedì compra il rientro.
- **Limiti:** la riduzione delle posizioni prima del weekend è descritta da fonti di settore, non misurata da studi accademici su AUDJPY.

## Effetti di calendario sulle valute

### Inversione dopo il weekend – Dao, McGroarty, Urquhart (2016)
"A calendar effect: Weekend overreaction (and subsequent reversal) in spot FX markets", *Journal of Multinational Financial Management*. https://eprints.soton.ac.uk/402301
- Su 8 valute principali e 9 emergenti, i salti ampi tra chiusura del venerdì e apertura del lunedì tendono a invertirsi nella settimana successiva.
- **Uso:** non ancora usato. Possibile filtro per il long del lunedì (gap del weekend), da tenere come idea.

## Valute: ore del giorno, fixing, ordini

### Ritorni attorno ai fixing – Krohn, Mueller, Whelan (2024)
"Foreign Exchange Fixings and Returns Around the Clock", *Journal of Finance* 79(1), 541–578. Working paper: https://www.wu.ac.at/fileadmin/wu/d/ri/isk/VSFX_2022/Paper/Session_III_1a_Krohn__foreign_Exchange_Fixings_Returns_Around_The_Clock_0712.pdf
- Dal 1999 al 2019, sulle nove valute più scambiate, il dollaro sale prima dei fixing di Tokyo (09:55 locali), della BCE (14:15) e di Londra (16:00 locali) e scende dopo, di circa 2 punti base ogni volta; sull'intera giornata nessuna valuta si muove in modo significativo. La causa indicata sono i dealer che si coprono prima di una domanda di dollari che arriva sempre al fixing.
- Dopo il fixing di Londra tutte le valute salgono sul dollaro tranne lo yen, che scende; lo yen sale invece nelle ore asiatiche, contro la regola di Breedon-Ranaldo.
- **Uso:** 097 BRK GBP/JPY, M3. Ricavando il cross dalla tabella I, GBP/JPY sale di circa 3,8 punti base tra le 17:00 e le 23:00 italiane (`fonti/prodotti/gbpjpy.md`, A1).
- **Limiti:** l'effetto si riduce nel tempo (dollaro dopo il fixing di Londra: 2,80 punti base nel 1999-2003, 0,86 nel 2014-2019); dopo il 2019 non misurato.

### Carry di giorno e di notte – Krohn, Mueller, Whelan (2024)
"Uncovered Interest Parity in High Frequency", working paper, novembre 2024. https://jbs.cam.ac.uk/wp-content/uploads/2024/11/uncovered-interest-parity-in-high-frequency.pdf
- Dal 1999 al 2023, sulle nove valute principali, il carry trade perde sul cambio di notte, dalle 17:00 alle 07:00 di New York (23:00-13:00 italiane), quasi esattamente l'interesse che incassa (−3,45% l'anno), e guadagna di giorno, dalle 07:00 alle 17:00 di New York (+3,44% l'anno); il risultato regge spostando l'inizio del giorno alle 08:00 di New York. Oltre il 60% del rendimento del carry cade nei giorni della FOMC e dei dati macro americani, che sono il 17% dei giorni.
- **Uso:** 097 BRK GBP/JPY, M5 (long nelle ore americane, short nelle ore asiatiche ed europee).
- **Limiti:** working paper; portafogli di valute contro dollaro, non GBP/JPY.

### Operatori al dettaglio giapponesi – Mukoyama, Kikuta, Washimi (2018)
"Investment Patterns of Japanese Retail Investors in Foreign Exchange Margin Trading", Bank of Japan Review 2018-E-3. https://www.boj.or.jp/en/research/wps_rev/rev_2018/rev18e03.htm
- Su dati di transazione ad alta frequenza: controcorrente sulle posizioni tenute per la notte o più, a favore del movimento dentro la giornata quando il cambio comincia a muoversi.
- **Uso:** 097 BRK GBP/JPY, M5 (meccanismo possibile per lo short delle ore asiatiche dopo un giorno di calo).
- **Limiti:** letto il riassunto; dati sul dollaro-yen.

### Giornate delle banche centrali – Mueller, Tahbaz-Salehi, Vedolin (2017)
"Exchange Rates and Monetary Policy Uncertainty", *Journal of Finance* 72(3), 1213–1252. Working paper: https://www.fmg.ac.uk/sites/default/files/publications/dp-54.pdf
- Dal 1994 al 2010 un portafoglio short dollaro guadagna molto di più nei giorni delle decisioni FOMC, e di più per le valute con tassi alti (16,83 punti base contro 1,67 negli altri giorni); per lo yen la differenza non è significativa. Nei giorni delle decisioni BoJ, tutte le valute contro yen guadagnano 18,16 punti base contro 1,41 (1998-2010).
- **Uso:** non ancora; ipotesi H5 e H6 di `fonti/prodotti/gbpjpy.md`.
- **Limiti:** il campione finisce nel 2010; servono gli elenchi delle date.

### Momento intraday sul forex – Elaut, Frömmel, Lampaert (2018)
"Intraday momentum in FX markets: Disentangling informed trading from liquidity provision", *Journal of Financial Markets* 37, 35–51. https://econpapers.repec.org/RePEc:eee:finmar:v:37:y:2018:i:c:p:35-51
- Sul rublo-dollaro alla borsa di Mosca (2005-2014) il rendimento della prima mezz'ora predice quello dell'ultima, più nelle crisi; la causa indicata è che chi fornisce liquidità non vuole tenere posizioni fuori orario.
- **Uso:** 097 BRK GBP/JPY, M1.
- **Limiti:** letto solo il riassunto; un mercato con orari di borsa, mentre GBP/JPY si scambia tutto il giorno.

### Stop accumulati e accelerazioni – Osler (2003, 2005)
"Currency Orders and Exchange Rate Dynamics: An Explanation for the Predictive Success of Technical Analysis", *Journal of Finance* 58(5), 1791–1819, https://ideas.repec.org/a/bla/jfinan/v58y2003i5p1791-1819.html – "Stop-loss orders and price cascades in currency markets", *Journal of International Money and Finance* 24(2), 219–241, https://www.newyorkfed.org/research/staff_reports/sr150.html
- Con gli ordini di una grande banca (1999-2002): le prese di profitto si concentrano sui numeri tondi, gli stop appena oltre; quando il prezzo raggiunge un livello con molti stop il movimento accelera, più a lungo che per le prese di profitto, con effetti significativi nell'arco di ore e non di giorni.
- **Uso:** 097 BRK GBP/JPY, spiegazione dell'ingresso sulla rottura del massimo della notte.
- **Limiti:** letti i riassunti; studia i numeri tondi, non i massimi di sessione.

### Regole tecniche intraday sul forex – Neely, Weller (2003)
"Intraday technical trading in the foreign exchange market", *Journal of International Money and Finance* 22(2), 223–237. https://gpbib.cs.ucl.ac.uk/gp-html/neely_2003_JIMF.html
- Regole intraday scelte con un algoritmo genetico e con un modello lineare ottimizzato non danno rendimenti in eccesso fuori campione una volta considerati costi e orari realistici.
- **Uso:** 097 BRK GBP/JPY, motivo per misurare giorni e pattern (M2, M4) invece di raffinarli.

### Attività per ora del giorno – Ito, Hashimoto (2006)
"Intraday seasonality in activities of the foreign exchange markets: Evidence from the electronic broking system", *Journal of the Japanese and International Economies*. https://www.nber.org/papers/w12413
- Sul circuito EBS (dollaro-yen, euro-dollaro) numero di scambi e volatilità hanno un andamento a U nelle ore di Tokyo e di Londra, con picchi alle aperture; volatilità e attività vanno insieme, e con spread più stretti.
- **Uso:** 097 BRK GBP/JPY, M4 (apertura di Londra calma).

## Momento intraday sugli indici

### Momento intraday di mercato – Gao, Han, Li, Zhou (2018)
"Market Intraday Momentum", *Journal of Financial Economics* 129(2), 394–414. https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414
- Sull'ETF dello S&P 500 dal 1993 al 2013 il rendimento dalla chiusura del giorno prima alla fine della prima mezz'ora prevede quello dell'ultima mezz'ora (R² 1,6%, 1,2% fuori campione). L'effetto cresce con volatilità e volumi, nelle recessioni e nei giorni di dati macro.
- **Uso:** 165 DAX, M4 e M5.
- **Limiti:** misura solo l'ultima mezz'ora di una borsa; 165 DAX tiene le posizioni per 7 e 18 ore.

### Coperture gamma e momento intraday – Baltussen, Da, Lammers, Martens (2021)
"Hedging Demand and Market Intraday Momentum", *Journal of Financial Economics* 142(1), 377–403. https://pure.eur.nl/en/publications/hedging-demand-and-market-intraday-momentum/
- Su oltre 60 futures (azioni, obbligazioni, materie prime, valute) dal 1974 al 2020, il rendimento del resto della giornata prevede quello dell'ultima mezz'ora. La causa è la copertura di chi ha esposizione gamma negativa (market maker di opzioni, ETF a leva), che deve comprare quando il prezzo sale e vendere quando scende; con esposizione gamma positiva l'effetto sparisce, e nei giorni successivi il movimento si inverte in parte.
- **Uso:** 165 DAX, M4 (ampiezza del movimento) e M5 (periodi agitati). Confermato sugli short del DAX: nei periodi agitati 31 € a trade contro 7 € in quelli calmi. 185 NQ, M2 (uscita dello short alla chiusura americana) e M3 (periodi agitati). 3251 FDAX, M1 e M3 (short tenuto fino alla chiusura di Xetra nelle giornate in calo).
- **Dettagli letti nel testo (2026-11-21):** il futures sul DAX è nel campione, tra 8 futures europei; per i futures azionari si usano le ore della borsa a contanti, quindi per il DAX l'ultima mezz'ora è quella prima della chiusura di Xetra. Il risultato del gruppo europeo è significativo, quello del solo DAX non è riportato separatamente nelle tabelle principali.

### Indicizzazione e inversione degli indici – Baltussen, van Bekkum, Da (2019)
"Indexing and stock market serial dependence around the world", *Journal of Financial Economics* 132(1), 26–48. Testo: https://www3.nd.edu/~zda/Indexing.pdf
- Su 20 indici di 15 paesi l'autocorrelazione dei rendimenti giornalieri era positiva fino agli anni '90 ed è negativa dal 1999 (media da 0,094 a −0,026). La legano alla crescita di futures ed ETF: l'arbitraggio tra prodotto indicizzato e titoli porta sull'indice pressioni di prezzo non legate a notizie, che poi rientrano.
- **DAX** (tabella 1): giornaliera da 0,066 a −0,016, non significativa dopo il 1999; settimanale da 0,008 a −0,102, significativa.
- **Uso:** 138 DAX, M4 (long del martedì dopo un lunedì in forte calo).
- **Limiti:** campione fino al 2016; non separa i giorni di movimento grande, dove l'inversione dovrebbe concentrarsi.

### Effetto lunedì sul DAX – Miss, Charifzadeh, Herberger (2020)
"Revisiting the Monday effect: a replication study for the German stock market", *Management Review Quarterly* 70, https://ideas.repec.org/a/spr/manrev/v70y2020i2d10.1007_s11301-019-00167-4.html
- Sul DAX 2000-2017 nessun effetto lunedì stabile, prima, durante e dopo la crisi finanziaria.
- **Uso:** contesto per 138 DAX: la scelta del martedì non ha una base documentata.
- **Limiti:** letto solo il riassunto; non riporta il martedì.

### Il lunedì segue il venerdì – Abraham, Ikenberry (1994)
"The Individual Investor and the Weekend Effect", *Journal of Financial and Quantitative Analysis* 29(2), 263–277. https://ideas.repec.org/a/cup/jfinqa/v29y1994i02p263-277_00.html
- Negli USA dopo un venerdì negativo il lunedì è negativo quasi l'80% delle volte (media −0,61%); i piccoli investitori vendono di più il lunedì, soprattutto dopo cattive notizie.
- **Uso:** contesto per 138 DAX: il passaggio da un giorno all'altro a inizio settimana è prosecuzione, non inversione.
- **Limiti:** campione USA vecchio; letto solo il riassunto.

### Momento intraday nel mondo – Li, Sakkas, Urquhart (2022)
"Intraday time series momentum: Global evidence and links to market characteristics", *Journal of Financial Markets* 57, 100619. https://ideas.repec.org/a/eee/finmar/v57y2022ics138641812100001x.html
- Lo stesso legame di Gao et al. in 12 di 16 borse sviluppate, più forte con volatilità alta, liquidità bassa e notizie concentrate.
- **Uso:** 165 DAX, M5.
- **Limiti:** i numeri per la Germania non li ho letti (testo integrale non raggiungibile).

## Effetti di calendario sulle azioni

### Fine mese – McConnell, Xu (2008)
"Equity Returns at the Turn of the Month", *Financial Analysts Journal* 64(2), 49–64. https://econpapers.repec.org/RePEc:taf:ufajxx:v:64:y:2008:i:2:p:49-64
- Negli USA dal 1926 al 2005 l'ultimo giorno del mese e i primi tre del successivo rendono in media lo 0,15% al giorno (indice ponderato per capitalizzazione); l'effetto c'è in 31 borse su 35, regge nei sottoperiodi e non si spiega con un rischio più alto. La causa resta aperta.
- **Uso:** 165 DAX, M3: non trovato negli short pomeridiani del DAX. 185 NQ, M5 (long aggiunti nei giorni del cambio di mese).

### Vendite per liquidità a fine mese – Etula, Rinne, Suominen, Vaittinen (2020)
"Dash for Cash: Monthly Market Impact of Institutional Liquidity Needs", *Review of Financial Studies* 33(1), 75–111. Testo: https://acris.aalto.fi/ws/portalfiles/portal/40965155/hhz054.pdf
- Fondi pensione e istituzioni vendono azioni prima della fine del mese per avere liquidità per i pagamenti, e chi riceve i pagamenti reinveste dopo. Nei mercati liquidi di tutto il mondo i rendimenti sono bassi da 8 a 4 giorni di borsa prima dell'ultimo e alti nei sette giorni successivi; nello stesso periodo salgono i tassi a brevissimo (repo, fed funds). Offre un meccanismo per l'effetto fine mese di McConnell-Xu.
- **Uso:** 185 NQ, M5.
- **Limiti:** letti riassunto e diapositive; i numeri esatti vanno presi dal testo pubblicato.

### Il lunedì e le settimane del mese – Wang, Li, Erickson (1997)
"A New Look at the Monday Effect", *Journal of Finance* 52(5), 2171–2186. https://ideas.repec.org/a/bla/jfinan/v52y1997i5p2171-86.html
- Negli USA dal 1962 al 1993 il rendimento negativo del lunedì si concentra nelle ultime due settimane del mese; nelle prime tre il lunedì medio non è diverso da zero. Sun e Tong (2002) lo collocano tra il 18 e il 26 del mese.
- **Uso:** 185 NQ, M5 (variante che salta i lunedì della finestra delle vendite).
- **Limiti:** campione vecchio; l'effetto lunedì si è indebolito dagli anni '90 sui titoli grandi.

### Fine mese sui futures – Dzhabarov, Ziemba (2010) e Maberly, Waggoner (2000)
Dzhabarov, Ziemba, "Do seasonal anomalies still work?", https://ideas.repec.org/h/wsi/wschap/9789814405461_0016.html – Maberly, Waggoner, Fed di Atlanta working paper 2000-11, https://ideas.repec.org/p/fip/fedawp/2000-11.html
- Dzhabarov e Ziemba trovano l'effetto fine mese sui futures USA dal 1993 al 2009, con i giorni spostati in avanti perché anticipato; Maberly e Waggoner non lo trovano più dopo il 1990 sull'S&P 500 a contanti e sui futures.
- **Uso:** 185 NQ, M5: le prove sono in conflitto, quindi la direzione è dichiarata prima del test.

### Stagionalità delle azioni tedesche – Weigerding, Hanke (2018)
"Drivers of seasonal return patterns in German stocks", *Business Research* 11, 173–196. https://link.springer.com/article/10.1007/s40685-017-0060-0
- Sulle azioni tedesche la stagionalità di fine mese dipende soprattutto dalla liquidità, poco dagli squilibri tra ordini, e si è spostata tra 4 giorni prima e 2 dopo la fine del mese.
- **Uso:** 165 DAX, variante di M3.

### Rialzo prima della FOMC – Lucca, Moench (2015) e Kurov, Wolfe, Gilbert (2021)
"The Pre-FOMC Announcement Drift", *Journal of Finance* 70(1), https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf – "The disappearing pre-FOMC announcement drift", *Finance Research Letters* 40, https://ideas.repec.org/a/eee/finlet/v40y2021ics1544612320315956.html
- Dal 1994 al 2011 le borse hanno reso molto più della media nelle 24 ore prima delle decisioni FOMC, anche il DAX; dopo il 2015 l'effetto negli USA si è quasi annullato.
- **Uso:** non ancora; ipotesi H6 in `fonti/prodotti/dax.md`.

## Rendimenti notturni

### Rialzo all'apertura europea – Boyarchenko, Larsen, Whelan (2023)
"The Overnight Drift", *Review of Financial Studies* 36(9), 3502–3547. Working paper: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf
- Sui futures S&P 500 il rendimento più alto della giornata cade tra le 2:00 e le 3:00 di New York (08:00–09:00 italiane), all'apertura europea: 3,7% l'anno. Lo spiegano con i market maker che a fine giornata assorbono le vendite e le rivendono quando arrivano gli operatori europei: il rialzo è forte dopo le giornate di vendite e modesto dopo i rialzi.
- **Aggiornamento**: dal 2021 al 2025 quell'ora ha reso circa zero, perché gli squilibri di fine giornata si sono ridotti a meno della metà (stessi autori, https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/).
- **Uso:** 165 DAX, M11: spostare l'uscita del long dalle 08:00 alle 09:00 ha alzato il profitto del long dell'11%. 185 NQ, M1 (uscita del long a orario) e M2 (notte dello short dopo una giornata di vendite); l'effetto riguarda anche i futures sul Nasdaq 100.
- **Calo attorno all'apertura americana** (stesso lavoro, sezione II e appendice B, letti il 2026-11-21): dal 1998 al 2020 i rendimenti sono negativi dalle 9:00 alle 12:00 di New York (15:00–18:00 italiane), −1,2 punti base nell'ora 9:00–10:00 (t 2,6); per giorno della settimana significativi solo giovedì (−2,10) e venerdì (−3,03). Forte dal 1998 al 2010 e nelle crisi (2000-2003, 2007-2008, 2020), non significativo dal 2011 al 2020. Nell'ora dei dati delle 8:30 il rendimento medio è +3,22 punti base. Gli autori ipotizzano rialzi prima dei dati e rientri dopo, più frequenti il giovedì e il venerdì. **Uso:** 3251 FDAX, M1 e M2.

### Notte e giorno, clientele diverse – Lou, Polk, Skouras (2019)
"A Tug of War: Overnight Versus Intraday Expected Returns", *Journal of Financial Economics* 134(1), 192–213. PDF: https://personal.lse.ac.uk/polk/research/TugOfWar.pdf
- Scompongono il rendimento delle azioni USA in notte e giorno: le strategie di momento guadagnano solo di notte, le altre solo di giorno, spesso con segni opposti nei due tratti. Lo leggono come il tiro alla fune tra due clientele, piccoli investitori che operano all'apertura e istituzioni che operano durante la seduta.
- **Uso:** 185 NQ, M1 e M2, per giustificare la misura separata del tratto di giorno e di quello di notte.
- **Limiti:** letto solo il riassunto; riguarda titoli singoli e portafogli, non i futures sull'indice.

### Opzioni a scadenza giornaliera – Dim, Eraker, Vilkov (2024)
"0DTEs: Trading, Gamma Risk and Volatility Propagation", SSRN 4692190. Letti solo riassunti di terzi: https://harbourfrontquant.substack.com/p/impact-of-zero-dte-options-on-the e l'analisi di Cboe https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options
- L'esposizione gamma dei market maker sulle opzioni a scadenza giornaliera dello S&P 500 non propaga la volatilità; secondo Cboe i flussi si compensano e l'esposizione netta è vicina a zero. Altri lavori trovano un legame tra queste opzioni e la volatilità intraday, ma non attraverso le coperture gamma.
- **Uso:** contesto per 185 NQ (momento intraday dello short dopo il 2022).
- **Limiti:** paper non letto; riguarda lo S&P 500.

## Analisi tecnica

### Medie mobili sul Dow Jones – Brock, Lakonishok, LeBaron (1992)
"Simple Technical Trading Rules and the Stochastic Properties of Stock Returns", *Journal of Finance* 47(5), 1731–1764. https://ideas.repec.org/a/bla/jfinan/v47y1992i5p1731-64.html
- Sul Dow Jones dal 1897 al 1986 i rendimenti dopo i segnali di acquisto di medie mobili e rotture sono più alti e meno volatili di quelli dopo i segnali di vendita, che sono negativi; i risultati non si spiegano con i modelli statistici usuali dei rendimenti.
- **Uso:** non ancora; ipotesi H7 di `fonti/prodotti/nasdaq.md` (long sopra o sotto la media dei 200 giorni).
- **Limiti:** campione che finisce nel 1986, senza costi; le regole tecniche sugli indici USA hanno reso molto meno nei decenni successivi.

### Rottura dell'intervallo d'apertura – Holmberg, Lönnbark, Lundström (2013)
"Assessing the profitability of intraday opening range breakout strategies", *Finance Research Letters* 10(1), 27–33. https://ideas.repec.org/a/eee/finlet/v10y2013i1p27-33.html
- Sui futures sul petrolio una regola che compra o vende quando il prezzo supera di una soglia l'apertura della giornata ha reso più di quanto darebbe un prezzo senza memoria.
- **Uso:** contesto per 097 BRK GBP/JPY (rottura del massimo della notte asiatica).
- **Limiti:** altro mercato; letto solo il riassunto.

## Validazione dei backtest

Schemi in-sample/out-of-sample (CPCV, PBO, MinBTL, DSR, Reality Check, SPA, Romano-Wolf, Harvey-Liu) e metriche di regolarità, robustezza e portafoglio, con formule: `validazione-e-metriche.md` (2026-11-22).

### Sovra-adattamento – Bailey, Borwein, López de Prado, Zhu (2017) e Bailey, López de Prado (2014)
"The Probability of Backtest Overfitting", *Journal of Computational Finance*, https://papers.ssrn.com/abstract=2326253 – "The Deflated Sharpe Ratio", *Journal of Portfolio Management*, https://papers.ssrn.com/abstract=2460551
- Più varianti si provano, più è probabile che la migliore sia migliore per caso; il rapporto di Sharpe va corretto per il numero di prove fatte.
- **Uso:** regola di provare pochi valori tondi per parametro e di tenere da parte un periodo di verifica.

### Regole di calendario scelte tra molte – Sullivan, Timmermann, White (2001)
"Dangers of data mining: The case of calendar effects in stock returns", *Journal of Econometrics* 105(1), 249–286. https://econpapers.repec.org/RePEc:eee:econom:v:105:y:2001:i:1:p:249-286
- Con 100 anni di dati americani e un universo di circa 9.500 regole di calendario, le regole migliori hanno valori di significatività altissimi prese una per una, ma non sono più significative quando si tiene conto di tutto l'universo da cui sono state scelte (test con ricampionamento sul metodo di White).
- **Uso:** 3251 FDAX, che viene da un generatore di regole con i giorni scelti dopo sul backtest: il risultato del backtest va letto come sovrastimato, e i moduli verificano i meccanismi.
- **Limiti:** letto il riassunto.

## Annunci macro e banche centrali

### Premio delle giornate di annuncio – Savor, Wilson (2013)
"How Much Do Investors Care About Macroeconomic Risk? Evidence from Scheduled Economic Announcements", *Journal of Financial and Quantitative Analysis* 48(2), 343–375. https://ideas.repec.org/a/cup/jfinqa/v48y2013i02p343-375_00.html
- Negli USA dal 1958 al 2009 i giorni con dati su inflazione, occupazione e decisioni FOMC rendono in media 11,4 punti base contro 1,1 degli altri giorni, con rapporto rendimento/rischio molto più alto.
- **Uso:** 3251 FDAX, M2 (ingresso dopo i dati delle 14:30) e ipotesi H19 di `fonti/prodotti/dax.md`.
- **Limiti:** letto il riassunto; borsa americana, giornata intera.

### Solo la Fed muove le borse del mondo – Brusa, Savor, Wilson (2020)
"One Central Bank to Rule Them All", *Review of Finance* 24(2), 263–304. https://ideas.repec.org/a/oup/revfin/v24y2020i2p263-304..html
- Le borse di tutto il mondo rendono di più nei giorni delle decisioni FOMC; per BCE, Banca d'Inghilterra e Banca del Giappone non c'è un risultato simile, neanche sulle borse dei loro paesi. Dopo la FOMC l'incertezza scende ovunque, dopo le altre banche centrali no.
- **Uso:** 3251 FDAX: i giovedì della BCE non danno una direzione allo short.
- **Limiti:** letto il riassunto; BCE dal 1999 al 2016.

### Mercato intero attorno alle 24 ore – Bondarenko, Muravyev (2023)
"Market Return Around the Clock: A Puzzle", *Journal of Financial and Quantitative Analysis* 58(3), 939–967. https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/market-return-around-the-clock-a-puzzle/089E33AC0B4D3B9A02CBA31EDF6505B3
- Sui futures E-mini S&P 500 dal 2004 al 2018 le quattro ore attorno all'apertura europea fanno tutto il rendimento medio, con un rapporto di Sharpe di 1,6 anche dopo i costi; nelle altre 20 ore il rendimento è uno zero rumoroso. Lo spiegano con gli investitori europei che elaborano le notizie della notte.
- **Uso:** contesto per 3251 FDAX (di giorno l'indice non ha una deriva al rialzo).
- **Limiti:** letti riassunto e appendice.

## Oro

### Rendimenti notturni e diurni dell'oro – Blose, Gondhalekar, Kort (2018)
"Overnight versus day returns in gold and gold related assets", *Journal of Economics and Finance* 42(3), 526–549. https://ideas.repec.org/a/spr/jecfin/v42y2018i3d10.1007_s12197-017-9403-0.html
- Sui futures COMEX, sul fixing di Londra, sui titoli minerari e sui fondi in oro i rendimenti notturni sono positivi e quelli diurni negativi, nelle fasi di rialzo e di ribasso, anche dopo i costi; il prezzo all'apertura dei mercati occidentali risulta troppo alto.
- **Uso:** 185 oro, M1 (uscite attorno alla sessione asiatica).
- **Limiti:** letto solo il riassunto; una versione precedente di Blose (2011, convegno) riportava il contrario.

### L'oro nelle 24 ore – Donati, Jung (2019)
"Gold Price Dynamics Around the Clock", tesi magistrale, Copenhagen Business School. https://research-api.cbs.dk/ws/portalfiles/portal/59803241/651553_Thesis_Contract_13383.pdf
- Futures COMEX 2001-2018 a 5 minuti: l'oro sale dalle 23:00 alle 08:30 ora italiana, scende nelle ore di Londra con cadute sulle aste delle 11:30 e delle 16:00, risale fino alle 23:00. La salita asiatica c'è quasi ogni anno fino al 2016; nel 2017-2018 quasi sparisce. Le strategie che la sfruttano da sole, dopo i costi, restano in guadagno ma rendono meno del semplice possesso dell'oro.
- **Uso:** 185 oro, M1, per scegliere gli orari d'uscita.
- **Limiti:** tesi non sottoposta a revisione.

### Volatilità asimmetrica dell'oro – Baur (2012), Todorova (2017)
Baur, "Asymmetric volatility in the gold market", *Journal of Alternative Investments* 14(4), https://opus.lib.uts.edu.au/handle/10453/31217 – Todorova, "The asymmetric volatility in the gold market revisited", *Economics Letters* 150, https://ideas.repec.org/a/eee/ecolet/v150y2017icp138-141.html
- Sull'oro la volatilità sale più dopo i rialzi che dopo i ribassi, al contrario delle azioni: chi compra l'oro come rifugio lo fa a ondate.
- **Uso:** 185 oro, M2, come ragione per attendersi rotture al rialzo nei periodi agitati.
- **Limiti:** testi integrali non letti.

### Oro e rischio geopolitico – Baur, Smales (2020)
"Hedging geopolitical risk with precious metals", *Journal of Banking & Finance* 117. https://ideas.repec.org/a/eee/jbfina/v117y2020ics037842662030090x.html
- I metalli preziosi proteggono dal rischio geopolitico, soprattutto dalle minacce più che dagli eventi realizzati; nei casi estremi solo oro e argento.
- **Uso:** non ancora; in conflitto con l'effetto weekend negativo (B2 di `fonti/prodotti/oro.md`).

### Velocità di reazione dell'oro ai dati macro – Smales, Yang (2015); Elder, Miao, Ramchander (2012)
Smales, Yang, *International Review of Financial Analysis* 41, https://ideas.repec.org:443/a/eee/finana/v41y2015icp292-302.html – Elder, Miao, Ramchander, *Journal of Banking & Finance* 36(1), https://ideas.repec.org/a/eee/jbfina/v36y2012i1p51-65.html
- Sui futures COMEX la gran parte della reazione ai dati USA avviene entro 90 secondi; anche Elder e coautori trovano una risposta rapida (2002-2008).
- **Uso:** non ancora: le rotture sulle barre dei dati sono già prezzate alla chiusura della barra oraria.
