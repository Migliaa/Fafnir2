# Oro (Spot Gold su IG) – ricerca sul prodotto

Ricerca del 2026-11-20. Orari in ora italiana (CET d'inverno, CEST d'estate); Londra e l'Italia cambiano l'ora negli stessi giorni, New York qualche settimana prima o dopo. L'oro era tra 3.900 e 4.150 $ l'oncia a metà novembre 2026, al minimo da oltre un anno il 12 novembre ([Nation Thailand](https://www.nationthailand.com/business/40073439), [pricegold.net](https://pricegold.net/2026/november/12/); stampa e sito di prezzi).

**Gradi** (come in `README.md` di questa cartella)
- **A**: meccanismo chiaro, fonte solida, traducibile in ProRealCode.
- **B**: plausibile ma con fonte debole, oppure solo in parte traducibile.
- **C**: contesto, non diventa codice.

---

## Orari

| Evento | Ora italiana | Fonte |
|---|---|---|
| Spot Gold su IG | quotato tutto il giorno tranne una pausa di un'ora la sera (23:00-00:00), dalla notte tra domenica e lunedì fino al venerdì sera; le pagine IG si contraddicono sull'ora esatta | broker, [IG Svizzera](https://www.ig.com/en-ch/help-and-support/cfds/fees-and-charges/what-are-igs-commodities-cfd-product-details), [IG internazionale](https://www.ig.com/en/help-and-support/cfds/fees-and-charges/what-are-igs-commodities-cfd-product-details) |
| Apertura di Tokyo | 01:00 d'inverno, 02:00 d'estate (09:00 in Giappone, che non ha ora legale) | dato ufficiale |
| Apertura di Londra | 09:00 (08:00 a Londra) | dato ufficiale |
| LBMA Gold Price, asta del mattino e del pomeriggio | 11:30 e 16:00 (10:30 e 15:00 a Londra) | dati ufficiali LBMA, non riletti in questa ricerca |
| Dati macro USA (occupazione, inflazione) | 14:30 | calendario ufficiale USA |
| Fascia principale del COMEX (ex grida) | 14:20-19:30 | tesi CBS citata in A1 |
| Decisione FOMC | 20:00 | calendario Fed |

Nelle circa tre settimane l'anno con ora legale sfasata tra USA ed Europa i dati USA escono alle 13:30 e la FOMC decide alle 19:00.

## Costi su IG

Fonti: pagine IG Svizzera e internazionale citate sopra, datate settembre 2026 (broker). La pagina italiana non era raggiungibile: verificare in piattaforma ("Info").

- **Contratti**: Spot Gold da 100 $ per punto (100 once), mini da 10 $, e Spot Gold $1 (1 oncia, 1 $ per punto); un punto è 1 $ per oncia. Andrea usa lo Spot Gold (E1), da 1 € per punto, con profitti in euro (contratto non trovato sulle pagine IG lette: dato di Andrea). Il mini da 10 € non serve: oggi la taglia normalizzata scende sotto 1 contratto da 1 €.
- **Spread**: 0,3 $ sul contratto standard (0,6 $ sulla pagina svizzera), 0,1 $ su quello da 1 $; IG avverte che varia con l'ora, senza dare le fasce. Con l'oro a 4.000 $ è circa lo 0,01% del prezzo.
- **Margine**: 0,5% sulle tabelle per clienti professionali, 5% per i clienti al dettaglio; dal venerdì alle 17:00 per il weekend il minimo sale all'1% (pagina internazionale).
- **Finanziamento notturno**: basato sul tasso tom-next dell'oro più una commissione IG dello 0,8% annuo (le pagine riportano anche 0,3% e 1%), applicato alle posizioni aperte dopo le 23:00; il venerdì vale tre giorni. Il backtest di ProRealTime non lo include.
- Esiste anche un "Weekend Gold" separato, con spread 2,5 $, che non riguarda le posizioni sullo Spot Gold.

## A – Utilizzabile

### A1. L'oro sale nelle ore asiatiche e scende in quelle occidentali
- **Fatto.** Sui futures COMEX, sul prezzo del fixing di Londra, sui titoli minerari e sui fondi in oro i rendimenti notturni sono positivi e quelli diurni negativi, sia nelle fasi di rialzo sia in quelle di ribasso, anche dopo i costi (Blose, Gondhalekar, Kort, *Journal of Economics and Finance* 2018, [scheda](https://ideas.repec.org/a/spr/jecfin/v42y2018i3d10.1007_s12197-017-9403-0.html); letto solo il riassunto). Una versione precedente dello stesso autore (Blose 2011, presentata a un convegno) riportava il contrario, probabilmente con altre definizioni di giorno e notte.
- **Profilo orario.** Sui futures COMEX dal 2001 al 2018 il rendimento cumulato della giornata sale dalle 23:00 alle 08:30 circa (+12,3% annualizzato), scende fino alle 16:00 con due cadute brusche sulle aste di Londra (11:30 e 16:00) e risale fino alle 23:00, chiudendo a +8,3% annualizzato; la salita asiatica c'è in quasi tutti gli anni fino al 2016, nel 2017-2018 quasi sparisce (tesi di laurea magistrale, Donati e Jung, Copenhagen Business School 2019, [PDF](https://research-api.cbs.dk/ws/portalfiles/portal/59803241/651553_Thesis_Contract_13383.pdf); non sottoposta a revisione). La caduta sulle aste è forte soprattutto nel 2007-2011, gli anni delle presunte manipolazioni del fixing.
- **Dato recente.** Nel primo semestre 2026 l'oro è salito del 12,9% nelle ore asiatiche, è sceso dell'1,3% in quelle europee e del 15% in quelle nordamericane, secondo un grafico del World Gold Council riportato in un articolo d'opinione ([FXStreet, luglio 2026](https://www.fxstreet.com/analysis/a-strange-dichotomy-gold-up-on-the-year-in-asian-markets-down-big-in-the-west-202607131959)); il grafico originale non l'ho letto.
- **Meccanismo.** Cina e India fanno circa metà della domanda mondiale e comprano nelle loro ore di mercato; secondo Blose e coautori il prezzo all'apertura dei mercati occidentali risulta troppo alto. Chi in Occidente copre o vende lo fa nelle proprie ore.
- **Quanto vale per trade.** In media circa lo 0,05% del prezzo per sessione asiatica (12% annuo su circa 250 giorni), nel 2026 circa il doppio: 2 $ per oncia con l'oro a 4.000 $, contro uno stop di circa 36 $. Su un singolo trade è rumore, su qualche centinaio di trade si vede solo come differenza appaiata tra due uscite.
- **In ProRealCode.** Uscite a orario con `Time`. Ipotesi H1 e H2.
- **Su 185 oro (2016-2026) non si vede**: tenere il long fino alle 09:00 non ha cambiato il risultato e chiudere lo short prima della terza notte lo ha peggiorato (M1). Coerente con la tesi CBS, che vede l'effetto quasi sparire dal 2017.

### A2. Momento di lungo periodo sulle materie prime
- **Fatto.** Il rendimento degli ultimi 12 mesi di un future predice il segno di quello successivo su azioni, obbligazioni, valute e materie prime (Moskowitz, Ooi, Pedersen 2012, già in `fonti/paper/schede.md`), con prove fino al 1880 (Hurst, Ooi, Pedersen, [sintesi](https://fairmodel.econ.yale.edu/ec439/hurst.pdf)). Dopo il 2009 sulle materie prime il vantaggio si è ridotto (Georgopoulou e Wang, citato in una tesi del 2025; non letto). Statistiche separate per l'oro non le ho trovate.
- **Perché conta.** Lo short vende i crolli contro la salita di lungo periodo dell'oro, che dal 2001 è durata quasi sempre tranne nel 2011-2015 e da gennaio 2026. Se il crollo prosegue per giorni solo quando anche il trend di fondo è in calo, gli short contro il trend sono quelli deboli.
- **In ProRealCode.** `TIMEFRAME(daily, updateonclose)` e `close - close[250]`. Ipotesi H3.

### A3. Il momento cresce con la volatilità, e sull'oro la volatilità cresce con i rialzi
- **Fatto.** Il momento intraday è più forte con volatilità alta su oltre 60 futures, materie prime comprese (Baltussen et al. 2021), e sui futures cinesi di metalli, oro compreso, più forte con volatilità alta e liquidità bassa (working paper, [AUT](https://acfr.aut.ac.nz/__data/assets/pdf_file/0008/686816/4a-Z-Ivy-Zhou.pdf); non letto). Sull'oro, al contrario delle azioni, la volatilità sale più dopo i rialzi che dopo i ribassi (Baur, *Journal of Alternative Investments* 2012, [scheda](https://opus.lib.uts.edu.au/handle/10453/31217); confermato su dati intraday da Todorova, *Economics Letters* 2017, [scheda](https://ideas.repec.org/a/eee/ecolet/v150y2017icp138-141.html)): chi compra l'oro come rifugio lo fa a ondate.
- **Perché conta.** Il long compra rotture al rialzo, cioè proprio i momenti in cui la volatilità tende a salire. È il test di principio 1 di `idee/idee-di-trading.md` per capire se le gambe sono di momento.
- **In ProRealCode.** Modulo `moduli/filtro-regime-volatilita.txt`. Ipotesi H4.

### A4. Taglia legata alla volatilità
- **Fatto.** Scalare la posizione con la volatilità riduce code e drawdown su tutti gli strumenti; il miglioramento del rapporto rendimento/rischio è forte su azioni e credito, piccolo su materie prime e valute (Harvey et al. 2018, già in `fonti/paper/schede.md`).
- **Perché conta.** L'originale lo fa già, con lo stop in escursioni orarie; l'intestazione standard dei sistemi di Andrea usa invece la leva costante. Va deciso quale delle due tenere. Ipotesi H5.

## B – Plausibile, da usare con cautela

### B1. Notizie macro già nel prezzo alla chiusura della barra oraria
- Sui futures COMEX la maggior parte della reazione ai dati macro USA avviene entro 90 secondi (Smales, Yang, *International Review of Financial Analysis* 2015, [scheda](https://ideas.repec.org:443/a/eee/finana/v41y2015icp292-302.html)); risposta rapida anche in Elder, Miao, Ramchander (*Journal of Banking & Finance* 2012, [scheda](https://ideas.repec.org/a/eee/jbfina/v36y2012i1p51-65.html)).
- Le rotture delle 14:30-15:00 sono quindi in gran parte notizie già prezzate; se proseguono, è per altri flussi. Non ho una direzione da dichiarare.

### B2. Weekend
- I rendimenti dalla chiusura del venerdì a quella del lunedì sono più bassi di quelli del resto della settimana (Blose 2011, convegno; Ball, Torous, Tschoegl 1982 sui futures). Al contrario, l'oro protegge dalle minacce geopolitiche (Baur, Smales, *Journal of Banking & Finance* 2020, [scheda](https://ideas.repec.org/a/eee/jbfina/v117y2020ics037842662030090x.html)), che arrivano anche nel weekend e farebbero salire l'oro alla riapertura. Le due cose spingono in direzioni opposte: niente proposta.

### B4. Dopo i crolli comprano i compratori fisici
- Dopo la caduta di aprile 2013 (−200 $ in due giorni) la domanda di lingotti e monete ha toccato il record di 508 tonnellate nel secondo trimestre, metà da India e Cina, mentre i fondi quotati vendevano 402 tonnellate (World Gold Council, *Gold Demand Trends Q2 2013*, [comunicato](https://www.gold.org/news-and-events/press-releases/consumer-demand-gold-53-q2-2013-led-strong-growth-china-and-india); dati di settore).
- Un crollo dell'oro prosegue finché vendono i fondi, poi trova compratori a prezzi più bassi: è una ragione per chiudere lo short a un target invece di aspettare il tempo massimo. Ipotesi H8.

### B3. Aste di Londra
- Cadute del prezzo attorno alle aste delle 11:30 e delle 16:00, forti nel 2007-2011 e poi molto ridotte (tesi CBS, A1); nel 2014 Barclays è stata sanzionata per aver manipolato l'asta del 28 giugno 2012. Effetto non stabile, non diventa proposta.

## C – Contesto

- **Regimi.** Rialzo 2001-2011 (massimo circa 1.920 $ a settembre 2011), ribasso 2011-2015 con il crollo di aprile 2013, rialzo 2019-gennaio 2026 fino al record di 5.595 $ del 29 gennaio 2026 ([Yahoo Finance](https://finance.yahoo.com/news/gold-accelerates-losses-silver-tumbles-20-as-precious-metals-trade-unwinds-184131825.html)). Il 30 gennaio 2026 l'oro ha perso il 9,5% in chiusura e oltre il 12% durante la seduta, la caduta giornaliera più forte dal 1983, dopo la nomina del nuovo presidente della Fed e la chiusura di posizioni speculative ([ThinkAdvisor](https://www.thinkadvisor.com/amp/2026/01/30/gold-and-silver-plunge-as-wild-swings-rock-metals-markets/); stampa).
- **Episodi da usare come prova di resistenza**: settembre 2011, 12-15 aprile 2013, marzo 2020, agosto 2020, 30 gennaio 2026.
- La domanda dell'oro come rifugio rende i rialzi più nervosi dei ribassi (A3), al contrario delle azioni.

---

## Ipotesi per i tentativi

Direzione dichiarata prima del test.

| Id | Ipotesi | Direzione attesa | Esito |
|---|---|---|---|
| H1 | Il long che esce all'01:00 perde la salita delle ore asiatiche (A1) | uscita alle 09:00 con guadagno medio un po' più alto, effetto piccolo | M1: non confermata, −0,43 € a trade a 1 contratto |
| H2 | Lo short perde nelle notti asiatiche (A1) | uscire alle 21:00 del secondo giorno, prima della terza notte, alza il guadagno medio | M1: smentita, profitto dello short −8%, drawdown +9% |
| H3 | Gli short contro il trend di 12 mesi sono i più deboli; per i long vale l'opposto, più debolmente (A2) | guadagno medio dei trade scartati più basso di quello dei tenuti, soprattutto sullo short | M3: smentita sullo short (gli short contro il trend rendevano di più), sul long effetto nel margine del caso |
| H4 | Le gambe sono di momento e rendono di più nei periodi agitati (A3) | guadagno medio più alto con volatilità di 2 settimane sopra quella di 5 mesi | M2 a 1 contratto: sì sul long (18,9 contro 7,8 €, al limite del caso), opposta sullo short; da rimisurare a rischio fisso (M6) |
| H5 | Con lo stop in escursioni medie, il rischio costante allo stop regge meglio della leva costante (A4) | rapporto profitto / drawdown più alto con il rischio costante | M4 non lanciato; Andrea tiene il rischio costante per la curva diritta (C0) |
| H6 | L'esclusione di giugno-novembre 2011 nasconde perdite | il riferimento con `Escludi2011 = 0` ha profitto più basso o drawdown più alto | senza oggetto: il backtest parte dal 2016 |
| H7 | Lo short eredita il target dell'ultimo long | report degli short diverso tra sistema completo e `EntraLong = 0` | molto probabile: senza i long i vincenti dello short durano di più e mancano le chiusure rapide in guadagno |
| H8 | Lo short di un crollo rende di più con un target, perché dopo i crolli arrivano compratori fisici (B4) | target esplicito di 13 escursioni orarie con profit factor più alto di nessun target | M5: risultato non ricevuto |
| H9 | Lo short rende di più quando il crollo arriva in un periodo calmo, perché chi gestisce il rischio sulla volatilità riduce le posizioni per giorni (ipotesi nata dai risultati di M2) | short dei periodi agitati con guadagno medio più basso a rischio fisso | M6: smentita, con metà posizione agli short agitati il rapporto profitto / drawdown scende da 8,23 a 7,70 |
| H10 | Nei periodi calmi la taglia a rischio costante porta la leva troppo in alto e lo stop stretto esce per rumore | tetto alla leva con drawdown del long più basso e profitto simile | M7: nessun effetto, profitto e drawdown −7% |
| H11 | Le rotture vere proseguono subito; chi è in perdita dopo mezza giornata è una rottura fallita (V2, Kaminski-Lo) | uscita alla barra 10 dei trade in perdita: perdente medio più piccolo, profit factor più alto | M8: smentita, vincenti del long dal 46 al 32%, drawdown quasi doppio |
| H12 | Le tendenze dell'oro durano più di 4 giorni (A2) | long a trailing senza target: guadagno medio e profitto del long più alti | M9: profitto +19% ma drawdown +54%, rapporto da 11,46 a 8,88 |
| H13 | Anche i cali meno violenti proseguono, con meno forza | short con calo di 4 escursioni orarie: short aggiunti con guadagno medio positivo, profitto più alto | M10: smentita, gli short aggiunti perdono 38,76 € ciascuno |
| H14 | Lo stop di 3 escursioni orarie è dentro il rumore di una posizione di più giorni | stop di 1,5 escursioni giornaliere: più vincenti, profit factor più alto | M11: più vincenti (56%) e profit factor 1,89 sul long, ma rapporto profitto / drawdown più basso |
| H15 | I pattern di esclusione `uptn104` e `uptn139` non hanno una ragione economica | toglierli aggiunge trade con guadagno medio simile | M12: smentita per `uptn104` (long aggiunti a −120 € ciascuno); `uptn139` toglie short a zero |
