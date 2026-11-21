# AUD/JPY – ricerca sul prodotto

Ricerca del 2026-11-20. Orari in ora italiana: CET d'inverno, CEST d'estate. Il Giappone non ha ora legale; Sydney sì (AEDT, UTC+11, da inizio ottobre a inizio aprile). Per questo la distanza oraria con Sydney cambia nel corso dell'anno, e nelle settimane dei cambi d'ora di 1 ora in più o in meno.

**Gradi**
- **A**: meccanismo chiaro, fonte solida, traducibile in ProRealCode.
- **B**: plausibile ma con fonte debole, oppure solo in parte traducibile.
- **C**: contesto, non diventa codice.

---

## A – Utilizzabile

### A1. Le valute ad alto tasso perdono quando la volatilità globale sale di colpo
- **Fatto.** Le variazioni inattese della volatilità valutaria globale spiegano oltre il 90% della differenza di rendimento tra portafogli di carry: le valute ad alto tasso come l'AUD perdono, quelle a basso tasso come lo JPY guadagnano (Menkhoff, Sarno, Schmeling, Schrimpf, *Journal of Finance* 2012, [testo](https://openaccess.city.ac.uk/id/eprint/3391/1/CTVOL_R3_v4_paper.pdf)). I crolli dei carry trade coincidono con aumenti della volatilità e del costo del finanziamento (Brunnermeier-Nagel-Pedersen 2008, già in `fonti/paper/schede.md`).
- **Conferma recente.** Il 5 agosto 2024 i carry trade finanziati in yen sono stati i più colpiti e in gran parte chiusi per forza; il TOPIX ha perso il 12% in un giorno ([BIS Bulletin 90](https://www.bis.org/publ/bisbull90.pdf), [BIS Quarterly Review settembre 2024](https://bis.org/publications/qr-202409/carry-off-carry-on)).
- **In ProRealCode.** Non si può leggere la volatilità globale né il VIX; si usa come segnale sostitutivo la volatilità di AUDJPY stesso (`AverageTrueRange` breve contro lungo). È già sfruttato in M4 e M8.

### A2. Crolli improvvisi in assenza di liquidità, all'apertura asiatica e nei giorni festivi
- **Fatto.** Il 3 gennaio 2019, con Tokyo chiusa per festività, AUDJPY ha perso oltre il 7% nella sessione asiatica, circa 450 pip in un'ora. La RBA lo attribuisce alla liquidità ridotta del periodo di Capodanno e agli ordini automatici scattati a catena ([RBA, Statement on Monetary Policy febbraio 2019, Box B](https://www.rba.gov.au/publications/smp/2019/feb/box-b-the-recent-japanese-yen-flash-event.html)).
- **Perché conta.** Nella fascia tra chiusura di New York e apertura asiatica (circa 23:00-02:00 ora italiana) gli stop possono essere eseguiti molto peggio del livello impostato. Il long di 128 BIAS HOUR entra il lunedì alle 03:00, poco dopo questa fascia, e resta aperto durante le due notti successive.
- **In ProRealCode.** Le date si gestiscono con `Month` e `Day`. Ipotesi H1 qui sotto.

### A3. Una valuta tende a indebolirsi durante le ore di lavoro del suo paese
- **Fatto.** Su molte valute e fusi orari, una valuta tende a deprezzarsi nelle proprie ore di lavoro, perché in quelle ore chi vi opera compra soprattutto valuta estera. Lo stesso andamento compare nel flusso degli ordini (Breedon-Ranaldo, *Journal of Money, Credit and Banking* 2013, [working paper](https://www.snb.ch/en/publications/research/working-papers/2011/working_paper_2011_04)).
- **Per AUDJPY** le ore di Sydney e Tokyo quasi coincidono, quindi l'effetto netto non è prevedibile a tavolino; va misurato ora per ora.
- **In ProRealCode.** Con `Time` / `OpenTime` si misura il rendimento medio per ora del giorno. È uno strumento di diagnosi per spostare o confermare gli orari di un sistema; il rischio di adattarsi al passato è alto se si scelgono le ore migliori.

### A4. Decisioni della RBA
- **Fatto.** La RBA decide alle 14:30 di Sydney.
  - Dal 2024: 8 riunioni l'anno di due giorni, con la decisione il secondo giorno, di solito un martedì. Le date 2026 sono pubblicate dalla [RBA](https://www.rba.gov.au/media-releases/2025/mr-25-02.html): 2-3 febbraio, 16-17 marzo, maggio, 15-16 giugno, agosto, settembre, novembre, dicembre.
  - Prima del 2024: il primo martedì di ogni mese tranne gennaio.
- **Orario italiano.** Circa le 04:30 da novembre a marzo e le 06:30 da aprile a settembre; nelle settimane dei cambi d'ora anche alle 05:30.
- **Perché conta.** Il long di 128 BIAS HOUR (da lunedì 03:00 a mercoledì 22:00) attraversa ogni decisione della RBA.
- **In ProRealCode.**
  - Per il periodo fino al 2023: `DayOfWeek = 2 AND Day <= 7 AND Month <> 1`.
  - Dal 2024: serve l'elenco delle date scritto nel codice.
  - Ipotesi H2.

### A5. Dati sul lavoro australiani
- **Fatto.** Il dato mensile sul mercato del lavoro esce alle 11:30 di Sydney. Dal riferimento di settembre 2026 esce il terzo giovedì del mese ([ABS](https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia/latest-release/)); prima, in genere a metà mese, sempre di giovedì.
- **Orario italiano.** Circa 01:30 d'inverno, 03:30 d'estate. Arriva prima dello short del giovedì alle 12:00, quindi il dato è già nel prezzo all'ingresso.
- **In ProRealCode.** Il terzo giovedì si riconosce con `DayOfWeek = 4 AND Day >= 15 AND Day <= 21`.

### A6. Costi su IG
Fonti: [IG AUD/JPY](https://www.ig.com/en/forex/markets-forex/aud-jpy), [IG Australia, dettagli forex](https://www.ig.com/au/forex-product-details), [IG, dettagli CFD forex](https://www.ig.com/en-ch/help-and-support/cfds/fees-and-charges/what-are-igs-forex-cfd-product-details). Pagine di altre sedi IG: verificare sul sito italiano.
- Contratto mini da 10.000 AUD, 100 ¥ per punto (0,01). È coerente con la perdita a stop di circa 15.000 ¥ calcolata sul long.
- Spread minimo 1,3 punti, medio circa 1,6-1,8 punti tra 00:00 e 21:00. Nelle ore notturne e attorno ai dati è più largo.
- Finanziamento overnight: tasso tom-next più un costo IG fino allo 0,0022% al giorno. Il backtest di ProRealTime non lo include.
- Costo di un'operazione di andata e ritorno su 3,75 contratti con 1,7 punti di spread: circa 640 ¥, cioè il 4% della perdita a stop e il 6% del guadagno medio di un long.

---

## B – Plausibile, da usare con cautela

### B1. Fixing di Tokyo alle 9:55
- I clienti delle banche giapponesi comprano soprattutto dollari prima del fixing, e il prezzo del fixing risulta sistematicamente spostato. Il calendario (fine mese, giorni di pagamento) influisce sul movimento attorno al fixing (Ito-Yamada, *Journal of International Economics* 2017, [NBER w22820](https://www.nber.org/papers/w22820)).
- **Orario italiano.** 9:55 a Tokyo sono le 01:55 d'inverno e le 02:55 d'estate: il long del lunedì entra alle 03:00, subito dopo il fixing.
- **Limite.** Lo studio riguarda USD/JPY; che l'effetto si trasmetta ad AUDJPY è un'ipotesi.

### B2. Flussi di copertura al fixing di Londra di fine mese
- Gli investitori azionari internazionali aggiornano le coperture valutarie al fixing delle 16:00 di Londra dell'ultimo giorno del mese. Se le azioni estere sono salite nel mese, la valuta estera tende a indebolirsi prima del fixing (Melvin-Prins, *Journal of Financial Markets* 2015, [presentazione BCE](https://ecb.eu/events/pdf/conferences/131216/Third_FX_Workshop_MELVIN_PRINS_Equity%20hedging%20and%20exchange%20rates%20Nov%202013.pdf)).
- **Coincidenza.** Lo short di 128 BIAS HOUR esce il venerdì verso le 17:00 italiane, cioè esattamente all'ora del fixing.
- **Limite.** I flussi studiati sono soprattutto contro il dollaro; per AUDJPY la direzione dipende da azioni australiane e giapponesi, che ProOrder non può leggere.

### B3. Legame con le borse
- AUDJPY si muove con l'appetito per il rischio: correlazione con lo S&P 500 vicina a +0,8 in alcuni periodi, e divergenze tra i due segnalate come avvisi di inversione ([Forex.com](https://www.forex.com/en-uk/news-and-analysis/audjpy-the-fx-stock-market-correlation-play/), fonte di broker).
- Non utilizzabile in ProOrder (vedi `README.md` di questa cartella).

---

## C – Contesto

- **Tassi.** La RBA era al 3,60% a novembre 2025. La BoJ ha alzato i tassi a dicembre 2025 e a giugno 2026, ed era all'1,0% a luglio 2026 ([BoJ](https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm)). La differenza di tasso a favore dell'AUD, base del carry, si è ridotta rispetto al 2023. Le riunioni BoJ sono 8 l'anno, di due giorni, con decisione di solito verso mezzogiorno di Tokyo (orario non confermato dalle fonti trovate).
- **Piccoli operatori giapponesi** (i "Mrs Watanabe"). Fanno molto volume, circa l'80% in giornata secondo una ricerca BoJ del 2023 citata da [Macrobond](https://macrobond.com/insights/blogs/mrs-watanabes-japanese-retails-yen-carry-trade). La loro fama di operatori controcorrente non è confermata da studi. Il dato sulle posizioni non è disponibile in ProRealTime.
- **Rimpatrio di yen a marzo** (fine dell'anno fiscale giapponese). Non c'è un effetto stabile: i controlli disponibili trovano anni in un senso e anni nell'altro ([FXStreet su Nomura](https://www.fxstreet.com/amp/news/japan-march-seasonality-is-jpy-negative-nomura-201802221007)). Non usarlo.
- **Episodi da usare come prova di resistenza in backtest.**
  - 2008: crollo dei carry trade.
  - 24 agosto 2015.
  - 3 gennaio 2019: crollo improvviso.
  - Marzo 2020.
  - 5 agosto 2024: chiusura in massa dei carry trade in yen.

---

## Ipotesi pronte per i prossimi tentativi

Direzione dichiarata prima del test. Ognuna va giudicata anche sul numero di trade che tocca: sono eventi rari.

| Id | Ipotesi | Direzione attesa | Codice | Note |
|---|---|---|---|---|
| H1 | Non aprire posizioni nella prima settimana di gennaio | meno perdite estreme; profitto quasi invariato | `NOT (Month = 1 AND Day <= 7)` | circa 2 trade per gamba all'anno; vale come protezione più che come miglioramento |
| H2 | Il long che attraversa una decisione RBA ha un rischio di stop più alto (stop stretto + evento) | guadagno medio più basso nelle settimane RBA; ridurre la taglia a metà in quelle settimane | regola del primo martedì fino al 2023 + elenco date dal 2024 | da misurare prima con un backtest che opera solo nelle settimane RBA |
| H3 | L'ingresso del long subito dopo il fixing di Tokyo paga un prezzo spostato dai flussi del fixing | entrare un'ora dopo non peggiora il risultato | spostare `TriggerL` alle 04:00 | rischio di adattamento: provare solo +1 ora, non una griglia di orari |
| H4 | Per i sistemi nuovi su AUDJPY: un'operazione long aperta durante uno shock di volatilità perde più spesso (A1) | saltare i long con volatilità del giorno oltre 2 volte quella di lungo periodo | modulo M4 | su 128 BIAS HOUR l'effetto è stato visto su soli 3 trade |
