# 128 BIAS HOUR – AUDJPY 1H

Sistema stagionale settimanale: long il lunedì alle 03:00 e short il giovedì alle 12:00, ciascuno con due condizioni di esclusione. Il long esce mercoledì alle 22:00 o dopo 66 barre, lo short venerdì alle 18:00 o dopo 29 barre. Stop e target sono in percentuale del prezzo di ingresso. Il backtest ProRealTime è in yen (capitale iniziale 800.000 ¥).

**In produzione:** [DEFINITIVO-produzione.txt](versioni/DEFINITIVO-produzione.txt) = originale + M4 + M6 + M8 + M10. Esiti della terza tornata: M10 promosso, M9 vantaggio troppo piccolo rispetto ai costi, M11 scartato (dettagli in `registro-test.md`).

Ricerca sul prodotto e ipotesi non ancora provate (prima settimana di gennaio, settimane RBA, fixing di Tokyo): `fonti/prodotti/audjpy.md`.

## Problemi trovati nel codice originale

1. **Il reinvestimento è di fatto spento anche con `Reinvest = 1`.** `RiskProfit = (SProfit / close) * (RiskOnProfit / 100)` divide il profitto per il prezzo (circa 100 su AUDJPY), quindi il profitto pesa un centesimo di quanto previsto.
2. **`StrategyProfit` è nella valuta dello strumento (yen), non in euro.** Sommarlo a `InitCapital = 3000` mescola due valute: è l'errore che ha rotto M1.
3. **Long e short rischiano cifre diverse a stop** (circa 15.000 ¥ contro 45.000 ¥) per il `* 3` nel denominatore del long. Lo stop dello short però non scatta quasi mai: tutti gli short, vincenti e perdenti, durano 29 barre.

## Come funzionano le due gambe

**Long** (287 trade dal 2014): quasi tutti i perdenti escono a stop pieno (perdita media 14.683 ¥ contro uno stop di 15.040 ¥) dopo circa 20 barre; i vincenti (44%) guadagnano in media 2,75 volte lo stop ed escono a tempo il mercoledì. Il trend dei 100 giorni non cambia il risultato (M5).

**Short** (393 trade dal 2015): è un'operazione a tempo, da giovedì 12:00 a venerdì 17:00, con il 56% di vincenti, vincente medio 16.600 ¥ e perdente medio 12.500 ¥. Guadagna circa un terzo del long per trade e ha un drawdown simile.

**Ripartizione del rischio tra le gambe.** Ho stimato dai report media e dispersione dei risultati per trade (long circa 10.300 ± 28.000 ¥, short circa 3.700 ± 18.000 ¥, dispersioni ricostruite dai medi di vincenti e perdenti e quindi approssimate): il rapporto tra le taglie che massimizza la crescita è vicino a quello attuale, entro il 15%. Per questo non ho speso un tentativo per spostare rischio da una gamba all'altra.

## Risultati per tornata

| Modulo | Esito | Cosa ne ricaviamo |
|---|---|---|
| M1 reinvestimento + freno | test nullo | errore di valuta |
| M2 taglia a volatilità (entrambi i lati) | DD peggiore | sul long la perdita è già fissata dallo stop |
| M3 stop adattivi | meglio solo dal 2022 | scartato |
| M4 filtro shock sui long | DD long −10% | effetto prodotto da 3 trade su 287, tenuto perché scatta di rado |
| M5 filtro trend | profitto dimezzato | il trend non informa il long |
| **M6 reinvestimento corretto** | **crescita composta regolare** | **promosso** |
| M7 aggiunta sui long | profitto long +29%, DD +68% | peggio che ingrandire l'originale del 29% (DD ~187.000 ¥ invece di 243.000 ¥); la condizione scattava in circa metà dei long, quindi non selezionava |
| **M8 volatilità solo sugli short** | **DD short −25%, profitto +7%** | **promosso**: conferma che la gestione per volatilità serve dove la perdita non è limitata dallo stop |

## Terza tornata: M9, M10, M11

| Modulo | Ipotesi | Come giudicarlo |
|---|---|---|
| [M9](proposte/M9-aggiunta-selettiva.txt) aggiunta selettiva | una conferma rapida (+1 volta lo stop entro 8 ore, cosa che il caso produce circa una volta su tre) seleziona le settimane buone meglio di quella di M7 | guadagno per posizione e drawdown contro l'originale ingrandito dello stesso profitto (istruzioni nel file) |
| [M10](proposte/M10-freno-drawdown-su-C1.txt) freno sul drawdown, sopra C1 | ridurre la taglia sotto il massimo di capitale dà più crescita, a parità di drawdown, che ridurre il rischio sempre | M10 contro C1 con `RiskOnCapital` più basso e stesso drawdown % |
| [M11](proposte/M11-sperimentale-ciclo-settimanale.txt) sperimentale, ciclo settimanale | il long riassorbe la riduzione di rischio prima del weekend, lo short anticipa quella successiva: ogni gamba va presa solo se la mezza settimana precedente si è mossa in senso opposto | guadagno medio dei trade tenuti contro quello dei trade scartati, per ciascun lato (`ApplicaLong`, `ApplicaShort`) |

M9 e M11 sono scritti sull'originale per confrontarli con i report già fatti; M10 è scritto su C1 perché un freno sul drawdown ha senso solo con il reinvestimento.

**Considerati e non proposti.** Prolungare i long oltre il mercoledì va contro lo short del giovedì; un'uscita anticipata dei long in perdita non cambia il guadagno atteso se in quella fase il prezzo non ha una direzione; un filtro sulle festività giapponesi o australiane non è gestibile in modo affidabile in ProRealCode.

## Come leggere i test

- **Con il reinvestimento il drawdown va letto in percentuale** (riga `GRAPH DDPercento`), non in yen.
- **Con `CumulateOrders = True` ProRealTime conta le aggiunte come trade separati** (M7, M9): il guadagno medio per trade del report non è confrontabile con l'originale.
- **I parametri sono valori tondi scelti a priori**; nei commenti di ogni modulo ci sono le 2-3 varianti da provare.
- **Accanto a ogni miglioramento va scritto quanti trade lo producono.**
- **Le righe `GRAPH` non sono ammesse in ProOrder**: vanno tolte prima del reale.

Risultati in `registro-test.md`.
