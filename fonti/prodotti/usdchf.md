# USD/CHF – ricerca sul prodotto

Ricerca del 2026-11-21. Orari in ora italiana. Gradi come in `README.md` di questa cartella (A utilizzabile, B plausibile o con fonte debole, C contesto).

## Orari

| Evento | Ora italiana | Fonte |
|---|---|---|
| Decisione della BNS | giovedì, quattro volte l'anno (marzo, giugno, settembre, dicembre); 2026: 19/3, 18/6, settembre, 10/12; 2027: 18/3, 24/6, 23/9, 16/12. Ora di solito 09:30, non confermata dalle fonti lette | dato ufficiale, [BNS](https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy/decisions) |
| Dati USA (occupazione il primo venerdì del mese) | 14:30 | calendario ufficiale USA |
| Fixing WM/Reuters di Londra | 17:00 (16:00 a Londra) | Krohn-Mueller-Whelan 2024 |
| Decisione FOMC | mercoledì 20:00 (19:00 nelle settimane sfasate) | calendario Fed |
| Calcolo del finanziamento IG | 23:00 (22:00 a Londra), triplo il mercoledì | IG, vedi Costi |

Il sistema 128 BIAS USDCHF entra il mercoledì alle 13:00 e esce il venerdì alle 17:00: attraversa le decisioni FOMC del mercoledì, le decisioni BNS del giovedì e i dati sull'occupazione del primo venerdì.

## Costi su IG

Fonti (broker): [dettagli dei contratti forex](https://www.ig.com/en/forex/forex-contract-details), datata 8/9/2026; [pagina svizzera](https://www.ig.com/en-ch/help-and-support/cfds/fees-and-charges/what-are-igs-forex-cfd-product-details), datata 20/9/2026; [pagina italiana USD/CHF](https://www.ig.com/it/forex/mercati-forex/forex-spot-usd-chf).

- **Contratti.** Standard da 100.000 dollari, 10 franchi per pip (0,0001); mini da 10.000 dollari, 1 franco per pip, cioè 10.000 franchi per ogni 1,00 di movimento del prezzo. Taglia minima: 0,01 sulla pagina italiana (contratto standard), un contratto sulla pagina inglese. Da confermare quale contratto usa Andrea nel backtest.
- **Spread.** Minimo 1,5 pip; medio 1,95-1,99 tra le 00:00 e le 21:00 GMT, 2,2-2,3 sull'intera settimana (medie del 2020-2021, vecchie).
- **Finanziamento.** Tasso tom-next più lo 0,8% annuo di IG, sulle posizioni aperte alle 22:00 di Londra; il mercoledì vale tre giorni. Lo short USD/CHF paga la differenza tra i tassi del dollaro e del franco: BNS allo 0% da giugno 2025 ([BNS](https://www.snb.ch/en/publications/communication/press-releases-restricted/pre_20260618)), dollaro intorno al 3,5-4%. Stima: circa 4,5% annuo, 1 franco al giorno per contratto mini al prezzo di 0,79. La pagina svizzera dà un tetto dello 0,0022% al giorno per il costo di IG, in contrasto con lo 0,8% annuo: da verificare in piattaforma.
- **Margine** 3,33% per i clienti al dettaglio sulla pagina italiana; distanza minima dello stop 10.
- Il backtest ProRealTime non include il finanziamento.

## Regimi

- 2011-2015: cambio minimo EUR/CHF a 1,20; USD/CHF segue EUR/USD.
- 15 gennaio 2015: la BNS abbandona il cambio minimo, USD/CHF perde oltre il 10% in pochi minuti.
- 2015-2022: tassi negativi (−0,75%) e interventi sul cambio per indebolire il franco.
- 2022-2023: rialzi fino all'1,75% e vendite di valuta estera per rafforzare il franco.
- 2024-2025: tagli fino allo 0%. Dal 2025 franco forte (USD/CHF 0,77-0,80), con la BNS che si dice pronta a intervenire (fonti giornalistiche, grado C).

---

## A – Utilizzabile

### A1. Il franco è una valuta rifugio, su orizzonti da ore a giorni
- **Fatto.** Dal 1993 al 2008, su dati ad alta frequenza, il franco e lo yen si apprezzano sul dollaro quando le borse americane scendono, i titoli di stato americani salgono e la volatilità dei cambi aumenta. L'effetto si vede da poche ore a più giorni ed è più forte, in modo non lineare, quando la volatilità è alta e nelle crisi (Ranaldo, Söderlind, *Review of Finance* 2010, [working paper BNS](https://www.snb.ch/en/publications/research/working-papers/2007/working_paper_2007_17); letti riassunto e sintesi).
- **Per il sistema.** Dentro USD/CHF non si legge la borsa, ma si legge il movimento del cambio stesso: un forte apprezzamento del franco in una giornata è il segno di un'ondata di domanda di rifugio. Se le ondate durano giorni come sull'oro e sul Nasdaq di Andrea (V6, P4 e S7 di `idee/idee-di-trading.md`), un forte calo di USD/CHF prosegue.
- **Rischio opposto.** La BNS frena gli apprezzamenti rapidi del franco con interventi: alcune ondate si interrompono di colpo (settembre 2011, e la minaccia di interventi nel 2025-2026).

### A2. Una valuta si indebolisce nelle sue ore di lavoro
- **Fatto.** Le valute tendono a deprezzarsi nelle ore lavorative del proprio paese e ad apprezzarsi in quelle estere, per gli scompensi di inventario dei dealer: gli operatori nazionali comprano valuta estera nelle loro ore (Ranaldo, *Journal of Banking & Finance* 2009, [working paper BNS](https://www.snb.ch/en/publications/research/working-papers/2007/working_paper_2007_03); letto il riassunto).
- **Per USD/CHF.** Il franco tende a indebolirsi nelle ore europee e il dollaro nelle ore americane: uno short USD/CHF guadagna nel pomeriggio e nella sera italiana e perde nella mattina europea. Effetto di pochi punti base al giorno, più piccolo dello spread su un singolo trade: conta solo per scegliere le ore d'ingresso e d'uscita.

### A3. Fixing di Londra
- **Fatto.** Dal 1999 al 2019 il dollaro sale prima del fixing di Londra e scende dopo, di circa 2 punti base, con l'effetto in calo negli ultimi anni del campione (Krohn-Mueller-Whelan 2024, scheda in `fonti/paper/schede.md`; dettagli in `fonti/prodotti/gbpjpy.md`, A1).
- **Per il sistema.** L'uscita del venerdì alle 17:00 cade proprio al fixing: tenere lo short fino a sera prenderebbe la discesa del dollaro dopo il fixing, circa 2 punti base, cioè circa 1,6 franchi per contratto mini. Si vede solo come differenza tra due uscite su qualche centinaio di trade.

## B – Plausibile, da misurare

### B1. Effetti del giorno della settimana sui cambi
- Negli anni '70 e '80 alcune valute avevano rendimenti diversi a seconda del giorno (mercoledì sopra la media, venerdì sotto, Jaffe-Westerfield, citato in [Corhay et al. 1995](https://orbi.uliege.be/bitstream/2268/96132/1/Corhay_A_%201995_Managerial%20finance_21_32-43.pdf)). Su 29 mercati valutari l'effetto c'era negli anni '80 ed è sparito quasi ovunque negli anni '90 (Yamori, Kurihara, *Research in International Business and Finance* 2004, [scheda](https://ideas.repec.org/a/eee/riibaf/v18y2004i1p51-57.html); letto tramite citazioni). Il disegno ora per ora di Krohn-Mueller-Whelan non dipende dal giorno della settimana.
- **Per il sistema.** La letteratura non sostiene un ciclo settimanale su USD/CHF. Il sistema di Andrea va trattato come un'ipotesi: o il vantaggio regge spostando di qualche ora ingresso e uscita, o è stato trovato per caso.

### B2. Riduzione del rischio prima del fine settimana
- Fonti giornalistiche descrivono acquisti di franchi il venerdì nelle settimane di tensione (per esempio febbraio e marzo 2026, Medio Oriente; [FXStreet](https://www.fxstreet.com/news/usd-chf-declines-as-swiss-franc-strengthens-on-geopolitical-risks-trade-concerns-202602271048)). Nessuno studio trovato misura un effetto del venerdì sul franco. È lo stesso meccanismo supposto per lo short del giovedì-venerdì di AUD/JPY (V1), non dimostrato neanche lì.

### B3. Coperture di fine mese
- Le coperture valutarie degli investitori in azioni estere si concentrano al fixing di fine mese, e i rendimenti delle borse nel mese predicono il movimento del cambio prima del fixing (Melvin, Prins, [workshop BCE 2013](https://ecb.eu/events/pdf/conferences/131216/Third_FX_Workshop_MELVIN_PRINS_Equity%20hedging%20and%20exchange%20rates%20Nov%202013.pdf); non letto). Richiede i rendimenti delle borse, che ProOrder non legge: resta come contesto.

## C – Contesto

- La BNS decide quattro volte l'anno di giovedì, in mezzo alla finestra dello short; nessuna fonte trovata su una direzione media del franco in quei giorni.
- Franco e dollaro competono come rifugio: in alcune crisi sale il dollaro (fonti giornalistiche).

---

## Ipotesi

| Codice | Ipotesi | Direzione attesa | Dove | Esito |
|---|---|---|---|---|
| H1 | Il ciclo di fine settimana è un vantaggio vero solo se regge spostando ingresso e uscita e senza mesi e pattern (B1) | zona larga di orari tutti positivi, non un picco isolato su mercoledì 13:00 / venerdì 17:00 | M1 | **non risolta**: ogni mercoledì senza filtri, con stop diverso, guadagna 5,47 franchi a trade su 637 (M1); l'ottimizzazione degli orari non è stata lanciata. Il guadagno dell'originale sta nella selezione dei pattern; M3 la prova sugli altri giorni |
| H2 | Su una posizione a tempo con stop lontano, stop in escursioni giornaliere e rischio fisso riducono il drawdown (V3) | drawdown più basso a parità di guadagno medio in franchi | M1, poi M4 | non leggibile in M1 (tre cambi insieme); riproposta in M4 con lo stop dell'originale |
| H3 | Entrare dopo le 23:00 del mercoledì evita tre notti di finanziamento su quattro | nel backtest il guadagno cala meno di 3 franchi a trade per contratto mini, quanto si risparmia nel reale | M4 | – |
| H4 | Un forte apprezzamento del franco in giornata prosegue per uno-tre giorni (A1) | short dopo un forte calo dall'apertura con profit factor sopra 1,3; long simmetrico più debole | M2 | **non confermata**: profit factor 1,11 su 375 short dal 2014, tutto il profitto nel 2025-2026 |
| H5 | Dopo il fixing di Londra il dollaro scende (A3) | uscita del venerdì alle 19:00-21:00 meglio delle 17:00 di 1-2 franchi a trade | M4 | – |
| H6 | La selezione dei pattern dell'originale non dipende dal mercoledì | lunedì, martedì e giovedì vicini ai 26 franchi a trade; se il vantaggio è di fine settimana regge solo il giovedì | M3 | – |
