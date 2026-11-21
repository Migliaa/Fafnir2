# GBP/JPY – ricerca sul prodotto

Ricerca del 2026-11-21. Orari in ora italiana. Londra è sempre un'ora indietro rispetto all'Italia, perché le due cambiano l'ora negli stessi giorni; Tokyo, che non ha ora legale, è 8 ore avanti d'inverno e 7 d'estate; New York è 6 ore indietro, 5 in circa tre settimane l'anno in cui l'ora legale americana ed europea non coincidono.

**Gradi** (come in `README.md` di questa cartella)
- **A**: meccanismo chiaro, fonte solida, traducibile in ProRealCode.
- **B**: plausibile ma con fonte debole, oppure solo in parte traducibile.
- **C**: contesto, non diventa codice.

---

## Orari

| Evento | Ora italiana | Fonte |
|---|---|---|
| Apertura di Tokyo (09:00 in Giappone) | 01:00 d'inverno, 02:00 d'estate | dato ufficiale |
| Fixing di Tokyo (09:55 in Giappone) | 01:55 d'inverno, 02:55 d'estate | Krohn-Mueller-Whelan 2024 (A1) |
| Decisioni della BoJ | in genere attorno a mezzogiorno di Tokyo, giorni variabili: circa 04:00-05:00 | orario non confermato dalle fonti lette |
| Dati britannici (inflazione, lavoro, PIL) | 08:00 (07:00 a Londra) | dato ufficiale, non riletto in questa ricerca |
| Apertura di Londra | 09:00 | dato ufficiale |
| Decisione della BoE | 13:00 (12:00 a Londra), di solito di giovedì, 8 volte l'anno dal 2016 | [Bank of England](https://www.bankofengland.co.uk/news/2016/september/mpc-announcement-dates-for-2017-and-2018), date 2026 [qui](https://www.bankofengland.co.uk/news/2024/december/mpc-dates-for-2026) |
| Fixing della BCE e benchmark WM/Reuters delle 14:00 | 14:15 e 14:00 | Krohn-Mueller-Whelan 2024 |
| Dati USA | 14:30 | calendario ufficiale USA |
| Fixing WM/Reuters di Londra | 17:00 (16:00 a Londra) | Krohn-Mueller-Whelan 2024 |
| Decisione FOMC | 20:00, sempre di mercoledì (19:00 nelle settimane sfasate) | calendario Fed |
| Calcolo del finanziamento IG | 23:00 (22:00 a Londra) | IG, vedi Costi |
| Chiusura della giornata di New York | 23:00 (17:00 a New York) | convenzione di mercato |

Nel sistema 097 BRK il massimo di riferimento si misura fino alle 03:30, cioè le 11:30 di Tokyo d'inverno e le 10:30 d'estate: copre sempre il fixing di Tokyo, ma d'estate solo un'ora e mezza di seduta giapponese invece di due e mezza. L'ingresso alle 10:30 è un'ora e mezza dopo l'apertura di Londra.

## Costi su IG

Fonti (broker): [pagina italiana GBP/JPY](https://www.ig.com/it/forex/mercati-forex/forex-spot-gbp-jpy), [dettagli dei contratti forex](https://www.ig.com/en/forex/forex-contract-details) (datata settembre 2026), [pagina UK](https://www.ig.com/uk/ig-forex/gbp-jpy).

- **Contratti.** Standard da 100.000 sterline, 1.000 ¥ per pip (0,01); mini da 10.000 sterline, 100 ¥ per pip, cioè 10.000 ¥ per ogni yen di movimento del prezzo. La pagina italiana mostra solo lo standard, con taglia minima 0,04. Quale contratto usa Andrea va confermato: con il mini e 1 contratto lo stop dello 0,75% vale circa 16.000 ¥ al prezzo di oggi (212), che con 6.000 € di capitale è circa l'1,5%.
- **Spread.** Minimo 2,5 pip; in media 3,5 tra le 00:00 e le 21:00 GMT da lunedì a venerdì e 4,4 sull'intera giornata, quindi più largo fuori da quella fascia. Sono medie di 12 settimane fino al 29 maggio 2020, vecchie. Con 3,5 pip un'andata e ritorno su 1 contratto mini costa 350 ¥, circa il 2% dello stop.
- **Fascia dello spread largo.** Se le 21:00 GMT sono ora di Londra, l'uscita del sistema alle 22:00 italiane cade proprio all'inizio della fascia larga tutto l'anno; se sono GMT fisso, solo d'inverno. Da verificare in piattaforma.
- **Finanziamento.** Tasso tom-next più lo 0,8% annuo di IG, sulle posizioni aperte alle 22:00 di Londra (23:00 italiane), triplo il mercoledì. Un long che esce alle 22:00 italiane non lo paga mai.
- **Margine** 3,33% per i clienti al dettaglio; distanza minima dello stop 20 (la pagina non dice in che unità).
- **Orari.** Quotato da domenica sera (21:00-22:00 di Londra) a venerdì alle 22:00 di Londra, senza pause giornaliere.

---

## A – Utilizzabile

### A1. Movimenti prevedibili ora per ora attorno ai fixing
- **Fatto.** Dal 1999 al 2019, sulle nove valute più scambiate, il dollaro sale prima dei fixing di Tokyo, della BCE e di Londra e scende dopo. Il disegno è stabile in tutti i sottoperiodi e altamente significativo, ma si è ridotto negli ultimi anni del campione: sull'insieme delle valute la discesa del dollaro dopo il fixing di Londra vale 2,80 punti base al giorno nel 1999-2003 e 0,86 nel 2014-2019, non più significativa. Gli autori lo spiegano con i dealer che si coprono prima del fixing contro una domanda di dollari che arriva sempre al fixing (Krohn, Mueller, Whelan, *Journal of Finance* 2024, [working paper](https://www.wu.ac.at/fileadmin/wu/d/ri/isk/VSFX_2022/Paper/Session_III_1a_Krohn__foreign_Exchange_Fixings_Returns_Around_The_Clock_0712.pdf), [scheda](https://econpapers.repec.org/RePEc:bla:jfinan:v:79:y:2024:i:1:p:541-578); letto il testo, tabella I).
- **Numeri per sterlina e yen** (punti base al giorno, valuta contro dollaro, 1999-2019). GBP/JPY l'ho ricavato io sottraendo le due medie, che per i rendimenti logaritmici è esatto; la significatività del cross non è nel paper.

| Tratto (ora italiana) | GBP | JPY | GBP/JPY ricavato |
|---|---|---|---|
| 23:00 → fixing di Tokyo (01:55 o 02:55) | −1,89 | −1,61 | −0,28 |
| fixing di Tokyo → 08:00 | +1,27 | +3,15 | −1,88 |
| 08:00 → 14:15 | −2,29 | −1,03 | −1,26 |
| 14:15 → 17:00 | +0,42 | +0,62 | −0,20 |
| **17:00 → 23:00** | **+2,65** | **−1,16** | **+3,81** |
| intera giornata | +0,15 | −0,03 | +0,18 |

- **Cosa dice per GBP/JPY.** Sull'intera giornata non c'è direzione, ma dentro la giornata il cambio tende a scendere dal fixing di Tokyo fino alla prima parte del pomeriggio e a salire dopo il fixing di Londra, perché la sterlina si rafforza e lo yen è l'unica valuta che si indebolisce sul dollaro in quel tratto. Lo yen, al contrario di quanto dice la regola "una valuta si indebolisce nelle sue ore di lavoro" (Breedon-Ranaldo 2013, in `fonti/prodotti/audjpy.md`, A3), si rafforza nelle ore asiatiche.
- **Per il long di 097 BRK** (10:30-22:00), in media e prima di qualunque condizione d'ingresso: circa −0,9 punti base tra le 10:30 e le 17:00 e circa +3,2 tra le 17:00 e le 22:00. Con 1 contratto mini a 212, 3 punti base valgono circa 640 ¥, il 4% dello stop: un effetto che si vede solo come differenza appaiata tra due uscite su qualche centinaio di trade.
- **In ProRealCode.** Uscite a orario con `Time`. Ipotesi H3.

### A2. Il momento intraday è più forte nei periodi agitati
- **Fatto.** Sul rublo-dollaro alla borsa di Mosca (2005-2014) la prima mezz'ora predice l'ultima, più nelle crisi; la causa indicata è che chi fornisce liquidità non vuole tenere posizioni fuori orario e le chiude nella direzione del movimento (Elaut, Frömmel, Lampaert, *Journal of Financial Markets* 2018, [scheda](https://econpapers.repec.org/RePEc:eee:finmar:v:37:y:2018:i:c:p:35-51); letto solo il riassunto). Lo stesso legame su oltre 60 futures, valute comprese, più forte con volatilità alta (Baltussen et al. 2021, già in `fonti/paper/schede.md`).
- **Limite.** GBP/JPY si scambia 24 ore su 24 e non ha una chiusura netta come la borsa di Mosca: l'equivalente più vicino è la chiusura di New York delle 23:00, a cui il sistema esce un'ora prima.
- **Perché conta.** Il long compra la rottura del massimo asiatico durante la mattina di Londra ed esce a sera: è una gamba di momento intraday (principio 1 di `idee/idee-di-trading.md`), quindi la prima ipotesi è che renda di più nei periodi agitati.
- **In ProRealCode.** `moduli/filtro-regime-volatilita.txt`. Ipotesi H1.

### A3. Le rotture accelerano dove si accumulano gli stop
- **Fatto.** Con i dati degli ordini di una grande banca (1999-2002), gli ordini di presa di profitto si concentrano sui numeri tondi e gli stop appena oltre; quando il prezzo raggiunge un livello con molti stop il movimento accelera, di più e più a lungo che per gli ordini di presa di profitto, con effetti significativi nell'arco di ore e non di giorni (Osler, *Journal of Finance* 2003, [scheda](https://ideas.repec.org/a/bla/jfinan/v58y2003i5p1791-1819.html); Osler, *Journal of International Money and Finance* 2005, [working paper](https://www.newyorkfed.org/research/staff_reports/sr150.html); letti i riassunti).
- **Perché conta.** È il meccanismo più solido per un ingresso sulla rottura di un massimo recente: chi è short dalla notte asiatica tiene lo stop sopra il massimo della sessione, e superarlo fa partire acquisti a catena. Osler non studia i massimi di sessione ma i numeri tondi, quindi il legame con il massimo asiatico è un'estensione mia.
- **Contro.** Le regole tecniche intraday sul forex trovate cercando tra molte combinazioni su dati a 30 minuti non hanno dato rendimenti in eccesso fuori campione con costi e orari realistici (Neely, Weller, *Journal of International Money and Finance* 2003, [scheda](https://gpbib.cs.ucl.ac.uk/gp-html/neely_2003_JIMF.html)). È lo stesso avvertimento di Bailey et al. sui pattern scelti per ottimizzazione.
- **Uso.** Nessun modulo diretto: spiega l'ingresso e dice che l'effetto, se c'è, si esaurisce entro la giornata, quindi l'uscita a sera è coerente.

### A4. Ciclo settimanale dello yen (da 128 BIAS HOUR)
- **Fatto.** Su AUDJPY il long da lunedì 03:00 a mercoledì 22:00 e lo short da giovedì 12:00 a venerdì 17:00 funzionano in reale e su 12 anni di backtest, con qualunque trend (V1 di `idee/idee-di-trading.md`; sistema di Andrea). La spiegazione non è dimostrata.
- **Perché conta.** Il long di 097 BRK opera solo lunedì e mercoledì, dalle 10:30 alle 22:00: entrambi i giorni stanno dentro la finestra rialzista di V1 e il mercoledì esce alla stessa ora. Se il vantaggio di 097 BRK è in parte lo stesso ciclo, il martedì deve rendere come lunedì e mercoledì e giovedì-venerdì meno; se è solo rottura, i giorni devono rendere in modo simile.
- **In ProRealCode.** `DayOfWeek`. Ipotesi H2.

### A5. Crolli improvvisi fuori dalle ore di Londra
- **Fatto.** Il 7 ottobre 2016 la sterlina ha perso circa il 9% sul dollaro nelle prime ore asiatiche, recuperando poi gran parte del movimento, per una combinazione di liquidità scarsa, personale inesperto e ora del giorno ([BIS, Markets Committee, gennaio 2017](https://www.bis.org/publ/mktc09.htm)). Il 3 gennaio 2019 lo yen è salito di colpo nelle stesse ore (`fonti/prodotti/audjpy.md`, A2). Il 24 giugno 2016 il voto sulla Brexit ha fatto crollare la sterlina durante la notte del conteggio.
- **Perché conta.** Il long di 097 BRK è chiuso tra le 22:00 e le 10:30, quindi non è mai esposto alle ore in cui sono avvenuti questi episodi: è una protezione da tenere in qualunque modifica che allunghi la posizione oltre la sera.

### A6. I cross di carry perdono di notte e guadagnano nelle ore americane (dati fino al 2023)
- **Fatto.** Dal 1999 al 2023, sulle nove valute principali, il carry trade (lungo sulle valute a tasso alto, corto su quelle a tasso basso) perde di notte, dalle 17:00 alle 07:00 di New York (23:00-13:00 italiane), quasi esattamente l'interesse che incassa (−3,45% l'anno sul solo cambio), e lo recupera di giorno, dalle 07:00 alle 17:00 di New York (13:00-23:00 italiane), con +3,44% l'anno; il risultato regge spostando l'inizio del giorno alle 14:00 italiane. Il movimento a favore del carry parte con l'avvicinarsi dell'apertura americana (Krohn, Mueller, Whelan, "Uncovered Interest Parity in High Frequency", working paper 2024, [PDF](https://jbs.cam.ac.uk/wp-content/uploads/2024/11/uncovered-interest-parity-in-high-frequency.pdf); letto il testo).
- **Per GBP/JPY.** Da quando la BoE ha alzato i tassi (2022) GBP/JPY è un cross di carry, con lo yen come valuta di finanziamento: è lo stesso disegno di A1, misurato su un campione più recente e con un'altra scomposizione. Le due fonti dicono la stessa cosa: GBP/JPY tende a scendere dalla chiusura americana alla prima parte del pomeriggio europeo e a salire nelle ore americane.
- **Cosa dice dei due lati di 097 BRK.** Il long (10:30-22:00) sta quasi tutto nella metà favorevole; lo short spento dell'originale (01:00-10:30) sta tutto nella metà sfavorevole al carry, cioè favorevole allo short. M3 ha confermato nella direzione il tratto 17:00-22:00 del long (`registro-test.md`).
- **In ProRealCode.** Orari d'ingresso e d'uscita. Ipotesi H10.

---

## B – Plausibile, da usare con cautela

### B5. Operatori al dettaglio giapponesi
- Su dati di transazione ad alta frequenza, chi fa trading al margine sul forex in Giappone va controcorrente sulle posizioni tenute per la notte o più, ma dentro la giornata segue il movimento quando il cambio comincia a muoversi; in un sondaggio il 70% dichiara di seguire la tendenza (Mukoyama, Kikuta, Washimi, Bank of Japan Review 2018-E-3, [scheda](https://www.boj.or.jp/en/research/wps_rev/rev_2018/rev18e03.htm); letto il riassunto). Le società di intermediazione valutano le posizioni dei clienti verso le 07:00 di Tokyo (23:00-24:00 italiane) e chiudono d'ufficio quelle in perdita oltre i limiti, con vendite concentrate a inizio giornata giapponese ([Bloomberg, 2019](https://www.bnnbloomberg.ca/japan-s-margin-traders-why-they-matter-for-currency-markets-1.1213278); stampa).
- **Per GBP/JPY.** I piccoli operatori giapponesi tendono a essere lunghi sui cross contro yen e a comprare i ribassi: dopo una giornata di calo le loro posizioni sono in perdita, e le chiusure forzate di inizio giornata giapponese spingono il cambio ancora giù nelle ore asiatiche. È un meccanismo possibile per lo short dell'originale, che vende all'01:00 se il prezzo è sotto il minimo asiatico del giorno prima. Non ci sono dati per GBP/JPY.

### B6. Giorni della settimana sullo yen
- Sul dollaro-yen l'effetto giorno della settimana c'era nel 1973-1989 ed è sparito negli anni '90 (Yamori, Mourdoukoutas 2003, [scheda](https://emerald.com/insight/content/doi/10.1016/S1569-3767(03)04021-4)); in campioni successivi è segnalato un martedì più debole (Yu, Chiou, Jordan-Wagner 2008, [scheda](https://ideas.repec.org/a/taf/applec/v40y2008i20p2631-2643.html)). Letti solo i riassunti.
- Gli studi accademici non confermano un ciclo settimanale stabile sullo yen; il ciclo di AUDJPY (A4) resta un risultato dei backtest e del reale di Andrea, non della letteratura.

### B1. Giornate FOMC
- Un portafoglio short dollaro guadagna molto di più nei giorni delle decisioni FOMC, di più per le valute con tassi alti; per lo yen la differenza non è significativa, e al fixing di Londra solo dollaro australiano e sterlina mostrano differenze significative (Mueller, Tahbaz-Salehi, Vedolin, *Journal of Finance* 2017, [working paper](https://www.fmg.ac.uk/sites/default/files/publications/dp-54.pdf); letto il testo: sul portafoglio delle valute ad alto tasso 16,83 punti base nei giorni FOMC contro 1,67 negli altri, 1994-2010).
- **Per GBP/JPY.** La FOMC decide sempre di mercoledì alle 20:00, con il long aperto. Direzione: i long dei mercoledì FOMC rendono più degli altri.
- **Limiti.** Il campione finisce nel 2010, prima del backtest; sull'azionario l'analogo rialzo prima della FOMC è quasi sparito dopo il 2015 (Kurov et al. 2021, in `fonti/paper/schede.md`). Serve l'elenco delle date nel codice. Ipotesi H5.

### B2. Giornate BoJ
- Nello stesso paper, un portafoglio lungo su tutte le valute e corto sullo yen guadagna 18,16 punti base nei giorni delle decisioni BoJ contro 1,41 negli altri (1998-2010).
- **Per GBP/JPY.** La decisione arriva di solito dopo le 03:30, quindi dopo la fine del massimo asiatico: nei giorni BoJ la rottura delle 10:30 è spesso la reazione alla decisione. Direzione: long dei giorni BoJ con guadagno medio più alto. Pochi trade (8 riunioni l'anno, a giorni variabili, di cui solo una parte di lunedì o mercoledì) e serve l'elenco delle date. Ipotesi H6.

### B3. Fixing di Tokyo e giorni gotobi
- I clienti delle banche giapponesi comprano dollari prima del fixing delle 09:55, soprattutto nei giorni di pagamento (5, 10, 15, 20, 25, fine mese), e il prezzo del fixing ne risulta spostato (Ito-Yamada 2017, `fonti/prodotti/audjpy.md`, B1); dopo il fixing lo yen recupera (A1).
- **Per 097 BRK.** Nei giorni gotobi il massimo asiatico può essere gonfiato dal fixing, il che rende più difficile la rottura delle 10:30. Non so dire se le rotture di quei giorni siano più o meno affidabili: nessuna direzione, niente proposta.

### B4. Lunedì festivi a Londra o a Tokyo
- Quattro lunedì l'anno sono festivi in Inghilterra (Pasquetta, primo e ultimo lunedì di maggio, ultimo lunedì di agosto) e cinque o sei in Giappone. Senza Londra la rottura delle 10:30 avviene senza l'apertura europea dietro; senza Tokyo il massimo asiatico si forma con poca liquidità.
- Direzione: guadagno medio più basso in quei lunedì. Sono circa 10 lunedì l'anno, di cui solo una parte con il trade aperto: troppo pochi per una prova (lezione M4 di 128 BIAS HOUR). Ipotesi H7.

---

## C – Contesto

- **Tassi.** BoE al 3,75%, con un rialzo al 4% atteso per il 5 novembre 2026 per l'inflazione spinta dall'energia (esito non confermato dalle fonti lette); BoJ all'1,25% dal settembre 2026, con un rialzo a dicembre prezzato all'80% circa a fine ottobre ([FXStreet](https://www.fxstreet.com/news/british-pound-trades-lower-against-japanese-yen-ahead-of-boes-policy-outcome-202611050543), [FXStreet](https://www.fxstreet.com/news/british-pound-remains-almost-steady-against-japanese-yen-after-bojs-dovish-hold-202610300313); stampa). La differenza di tasso a favore della sterlina rende GBP/JPY un cross di carry, esposto ai crolli delle fasi di fuga dal rischio come AUDJPY (`fonti/prodotti/audjpy.md`, A1).
- **Livello.** GBP/JPY era tra 210 e 213 tra fine ottobre e inizio novembre 2026 (stampa). Dal 2016 è passato da circa 125-130 nei minimi (estate 2016, marzo 2020; dato a memoria, da controllare sul grafico) a oltre 210: a 1 contratto fisso un trade di oggi vale circa 1,7 volte uno di quei periodi.
- **Episodi da usare come prova di resistenza in backtest**: 24 giugno 2016, 7 ottobre 2016, 3 gennaio 2019, marzo 2020, settembre-ottobre 2022 (crisi dei titoli di Stato britannici), agosto 2024.
- **Rotture dell'intervallo iniziale su altri mercati.** Sui futures sul petrolio una regola di rottura dell'intervallo d'apertura ha reso più del caso (Holmberg, Lönnbark, Lundström, *Finance Research Letters* 2013, [scheda](https://ideas.repec.org/a/eee/finlet/v10y2013i1p27-33.html)). Altro mercato, solo contesto.
- **Attività per ora del giorno.** Sul circuito EBS (dollaro-yen, euro-dollaro) volumi e volatilità hanno picchi all'apertura di Tokyo e di Londra e calano nella pausa di mezzogiorno; volatilità alta va insieme a spread stretti (Ito, Hashimoto, *Journal of the Japanese and International Economies* 2006, [NBER w12413](https://www.nber.org/papers/w12413)).

---

## Ipotesi per i tentativi

Direzione dichiarata prima del test.

| Id | Ipotesi | Direzione attesa | Codice | Esito |
|---|---|---|---|---|
| H1 | Il long è momento intraday e rende di più nei periodi agitati (A2) | guadagno medio dei trade dei periodi calmi più basso di quello dei periodi agitati | modulo `filtro-regime-volatilita` | **smentita** (M1, con la stima del riferimento): circa 2.100 ¥ a trade in entrambi i regimi, ma vincenti e perdenti più grandi nei periodi agitati |
| H2 | Il long sfrutta in parte il ciclo settimanale dello yen (A4) | martedì simile a lunedì e mercoledì; giovedì e venerdì più deboli. Se tutti i giorni sono simili, il vantaggio è la rottura | `DayOfWeek` | report di M2 non ricevuto; si misura in M5 (`GiorniTutti`) e in M6 |
| H3 | Dopo il fixing di Londra GBP/JPY sale (A1) | uscire alle 17:00 toglie circa 3 punti base a trade; uscire alle 21:00 invece che alle 22:00 toglie poco nel backtest e fa risparmiare spread nel reale | uscita a orario | **confermata nella direzione** (M3, 17:00): −560 ¥ a trade, 2,8 punti base, al limite del caso; variante delle 21:00 non lanciata |
| H4 | L'esclusione dei giorni con apertura di Londra più calma della mezz'ora prima (pattern `uptn133`) toglie rotture senza partecipazione di Londra | i trade che il pattern scarta guadagnano meno di quelli tenuti | `PtnUNMRLN = 0` | nella direzione ma su 22 trade (M4): circa 400 ¥ contro 2.100; il pattern resta |
| H9 | Con lo stesso guadagno medio nei due regimi, una taglia inversa alla volatilità riduce le oscillazioni del long senza togliere profitto (risultato di M1) | drawdown più basso, profitto simile | taglia × volatilità lunga / breve, tra 0,5 e 1,5 | **non confermata sul long** (M5, 2016-2026: drawdown più alto, anni calmi 2016-2017 in perdita); confermata sullo short (profitto / drawdown da 10 a 15,5) |
| H10 | Lo short dell'originale (01:00-10:30) sta nelle ore in cui i cross di carry scendono (A1, A6, B5) | short positivo nel giro dell'orologio, con il long nelle ore americane; da controllare il 2026, negativo | short dell'originale con il livello reso esplicito | **positivo** (M5: 241 trade, 2.747 ¥ a trade, profit factor 2,5), ma il 22% del profitto viene da un trade, il crollo della sterlina del 7 ottobre 2016 |
| H11 | Il ciclo settimanale di AUDJPY (A4) vale anche per GBP/JPY | con gli orari di 128 BIAS HOUR, profit factor sopra 1,3 su entrambi i lati | sistema nuovo | **confermata** (M6): long 1,50, short 1,32 |
| H12 | Il ciclo settimanale e l'orologio della giornata si sommano: ogni lato rende di più entrando nelle ore favorevoli (A1, A6) | short del giovedì alle 22:00 e long del lunedì alle 13:00 con guadagno medio / drawdown più alto di M6 | ora d'ingresso | da misurare (M7, M8) |
| H5 | Mercoledì FOMC più forti (B1) | guadagno medio più alto nei mercoledì FOMC | elenco date | non proposta: campione vecchio |
| H6 | Rotture dei giorni BoJ più forti (B2) | guadagno medio più alto nei giorni BoJ | elenco date | non proposta: pochi trade |
| H7 | Lunedì festivi a Londra o a Tokyo più deboli (B4) | guadagno medio più basso | elenco date | non proposta: pochi trade |
| H8 | Prolungare il long nella notte asiatica (ritorni positivi della notte o del carry) | — | — | scartata a priori: dopo le 23:00 GBP/JPY scende in media fino al pomeriggio successivo (A1) ed entra nelle ore dei crolli improvvisi (A5) |
