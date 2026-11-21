# 165 DAX 30m

Sistema intraday-notturno sul DAX (Germany 40 Cash di IG), grafico a 30 minuti, con una gamba long e una short indipendenti. Il backtest ProRealTime è in euro, la stessa valuta del capitale: qui non c'è il problema di valuta di 128 BIAS HOUR.

Ricerca sul prodotto (orari, costi IG, letteratura): `fonti/prodotti/dax.md`.

**In produzione:** [DEFINITIVO-produzione.txt](versioni/DEFINITIVO-produzione.txt) = originale + M5 + M8 + M9 + M10 + M11, con l'intestazione standard di gestione del capitale. Versioni intermedie: C1 (+ M5), C2 (+ M5 + M8 + M9).

**Con 1 contratto, 2015-2026:** long 699 trade a 19,08 € (drawdown −1.298 €), short 389 trade a 26,29 € (drawdown −860 €), contro 17,14 € e 18,07 € dell'originale. Valori da report separati di long e short; il drawdown del sistema completo non è stato misurato.

## Cosa fa

**Long**, da lunedì a giovedì: alla chiusura della barra delle 13:30 compra se il prezzo è sopra la media esponenziale delle ultime 25 barre (circa 12 ore) e l'RSI a 2 periodi è sopra 65, cioè se l'ultima ora è stata di salita. Esce alle 08:00 del giorno dopo, quindi tiene la posizione circa 18 ore e mezza: il pomeriggio europeo, la sessione americana e la notte. Stop al 3%, target al 3,5%.

**Short**, da martedì a venerdì: alla chiusura della barra delle 12:30 vende se il prezzo è sotto la stessa media e se il minimo di ieri è sotto o uguale a quello di cinque giorni fa (settimana debole). Esce dopo 13 barre, cioè alle 19:30: copre i dati USA delle 14:30, l'apertura di Wall Street e la chiusura di Xetra. Stop al 2,5%, target all'1,4%.

**Taglia**: il rischio allo stop è il 5% (long) o il 4% (short) di 6.000 € più il 12% dei profitti, ai quali sono sommati a mano 1.600 € (900 + 550 + 150) di profitti di esecuzioni precedenti. I contratti si ottengono dividendo questo rischio per la distanza dello stop in punti, quindi 1 lotto vale 1 € per punto (contratto Germany 40 Cash da 1 €; se il backtest usa il contratto da 5 o 25 € tutti i rischi vanno moltiplicati di conseguenza).

Con il DAX a 26.700 lo stop del long vale circa 800 punti e quello dello short 670, mentre il target dello short (circa 375 punti in 7 ore) è raggiungibile in una giornata di forte ribasso. Gli stop valgono più del doppio dell'escursione di una giornata normale del DAX (circa 1,2%, stima): **entrambe le gambe escono quasi sempre a tempo**.

## Da dove sembra venire il vantaggio

Entrambe le gambe comprano o vendono a metà giornata nella direzione in cui il mercato si è già mosso e tengono la posizione durante le ore della sessione americana: è la forma del momento intraday documentato sugli indici (Gao et al. 2018; Li, Sakkas, Urquhart 2022), che si spiega con le coperture di chi ha esposizione gamma negativa (Baltussen et al. 2021). Lo stesso studio trova che il movimento si inverte in parte nei giorni successivi, e il long tiene la posizione anche di notte, dove sui futures americani il rialzo medio si concentrava all'apertura europea, tra le 08:00 e le 09:00, cioè proprio dopo l'uscita del long; quel rialzo dal 2021 è sparito (dettagli e fonti in `fonti/prodotti/dax.md`, A1 e B1). Quanto del guadagno del long venga dal pomeriggio e quanto dalla notte non si può dire senza un test.

**Dopo la prima tornata.** Per lo short la spiegazione regge: guadagna quasi solo nei periodi agitati (M5) e un po' di più quando la mattina si è mossa molto (M4, nel margine del caso). Il long invece non dipende dall'ampiezza del movimento della mattina (M4), quindi probabilmente il suo vantaggio non è momento intraday; resta da capire se stia nel pomeriggio o nella notte (M6).

Le esclusioni (niente long il venerdì, niente short il lunedì) evitano il weekend per il long; per lo short non ho trovato una ragione documentata.

## Problemi trovati nel codice

1. **Con il DAX sopra 20.000 punti la taglia minima di 1 contratto decide tutto.** La formula vorrebbe 0,61 contratti per il long (492 € di rischio su 800 punti di stop) e 0,65 per lo short; il minimo li porta a 1, quindi oggi lo stop del long costa circa 800 € (13% di 6.000 €) e quello dello short circa 670 € (11%), più del doppio del rischio scritto nei parametri. Un contratto vale circa 26.700 €, 4,4 volte il capitale. Il reinvestimento comincia ad agire solo quando i profitti, compresi i 1.600 € riportati a mano, superano circa 4.200 € sul long e 3.600 € sullo short; fino ad allora ogni modulo che cambia la taglia non ha effetto in reale.
2. **Il rischio cresce più in fretta del capitale.** Il rischio a stop in percentuale del capitale attuale è (5% × 6.000 + 12% × profitti) / (6.000 + profitti): 5% all'inizio, 8,5% quando i profitti raddoppiano il capitale, 10,6% quando lo quintuplicano, con il 12% come limite. Il sistema diventa più aggressivo man mano che cresce, e il drawdown in percentuale tende a salire nel tempo. Su questo punto ci sono M1 e, ricalibrato, M8.
3. **I 1.600 € riportati a mano entrano anche nel backtest**, che quindi parte come se avesse già quei profitti. Per i confronti va tenuto uguale in tutte le versioni; nella versione di produzione diventerà un parametro `ProfittoPrecedente` come in 128 BIAS HOUR.
4. **Costi non visti dal backtest.** Lo spread di IG è 1,6 punti dalle 09:00 alle 17:30 e 3,8 punti dalle 08:00 alle 09:00 e dalle 17:30 alle 22:00: entrambe le gambe entrano con lo spread stretto ed escono con quello largo (08:00 e 19:30), per un costo di andata e ritorno di circa 2,7 punti. Il long paga anche il finanziamento di una notte, circa 3,7 € a contratto con il DAX a 26.700. In totale circa 6,4 € a trade per contratto sul long e 2,7 € sullo short; il backtest usa uno spread fisso e nessun finanziamento.
5. **Short e long possono scontrarsi.** Da martedì a giovedì lo short entra alle 12:30 e il long può scattare alle 13:30; in ProRealTime un `BUY` con uno short aperto chiude lo short e apre il long ([forum ProRealCode](https://www.prorealcode.com/topic/invert-position)). Serve una risalita forte in un'ora, quindi è raro.
6. **Dettagli senza effetto pratico.** Stop e target vengono impostati alla barra dopo l'ingresso, quindi nei primi 30 minuti la posizione non li ha; con stop del 2,5-3% non conta. La condizione d'uscita del venerdì alle 21:00 non scatta mai, perché il venerdì non si aprono long.
7. **Settimane con ora legale sfasata.** Gli orari sono fissi in ora italiana: per circa tre settimane l'anno i dati USA escono alle 13:30, nello stesso momento in cui il long entra.
8. **Dal 10 dicembre 2018 i futures sul DAX trattano anche di notte (dalle 01:10).** Prima di quella data le barre notturne di IG erano quotazioni con pochi scambi; la media delle 25 barre copre quindi tratti di giornata diversi prima e dopo il 2018.

## Prima tornata: M1–M5 (esiti)

Numeri e calcoli in `registro-test.md`. Riferimento: originale a 1 contratto.

| Modulo | Esito |
|---|---|
| [M1](proposte/M1-rischio-frazione-fissa.txt) rischio a frazione fissa | non confrontabile; il 5% con stop al 3% vuol dire leva 1,7, troppo poca: rifatto come M8 |
| [M2](proposte/M2-taglia-a-volatilita.txt) taglia a volatilità | non confrontabile; contraddetto da M5, scartato |
| [M3](proposte/M3-short-fuori-dal-fine-mese.txt) niente short a fine mese | gli short scartati guadagnavano più degli altri: scartato |
| [M4](proposte/M4-ampiezza-del-movimento.txt) ampiezza del movimento | long: nessun effetto; short: guadagno medio dei tenuti 21,75 contro 12,53 € degli scartati, nel margine del caso; non adottato |
| **[M5](proposte/M5-regime-di-volatilita.txt) regime di volatilità** | **short: 31,38 € a trade contro 7,12 € dei periodi calmi, drawdown dimezzato; promosso (C1)**. Long: 23,05 contro 13,17 €, ma la curva peggiora: non adottato |

## Seconda tornata: M6–M9, sopra C1 (esiti)

Riferimento: C1 a 1 contratto (dettagli in `registro-test.md`).

| Modulo | Esito |
|---|---|
| [M6](proposte/M6-long-esce-a-sera-se-in-guadagno.txt) long in guadagno esce alle 21:30 | la notte dei long in guadagno rende 3.371 € su 11.981: scartato. Il long guadagna soprattutto di notte |
| [M7](proposte/M7-target-short-legato-alla-volatilita.txt) target dello short legato alla volatilità | guadagno medio uguale (+0,67 €), drawdown +28%: non migliora C1. Nella versione di produzione è un interruttore spento |
| **[M8](proposte/M8-reinvestimento-a-leva-costante.txt) leva costante** | **promosso** (leva 3 sul long, 4 sullo short); diventa l'intestazione standard di gestione del capitale |
| **[M9](proposte/M9-piu-short-nei-periodi-agitati.txt) short anche il lunedì** | **promosso**: 37 short in più a 23 € a trade, profitto dello short +11,5%, drawdown +4% |

## Terza tornata: M10–M11, sopra C2 (esiti)

| Modulo | Esito |
|---|---|
| **[M10](proposte/M10-short-calmi-dopo-forte-calo.txt) short calmi solo dopo un forte calo** | **promosso**: 114 short in più a 16,7 € a trade (contro 7 € di tutti gli short calmi), profitto dello short +23%, drawdown +17%; il 2023 diventa un anno in perdita sullo short |
| **[M11](proposte/M11-long-esce-dopo-apertura-xetra.txt) long esce alle 09:00** | **promosso**: profitto del long +11%, +1,94 € a trade, drawdown uguale, anni dal 2021 positivi; nel reale si aggiungono circa 1,1 punti di spread risparmiati |

## Per una prossima tornata

Considerati e non provati (in `fonti/prodotti/dax.md`, ipotesi H6, H8):
- niente short nei giorni FOMC: l'effetto sul DAX era forte fino al 2011 ma negli USA è quasi sparito dopo il 2015, riguarda circa 3 trade l'anno e richiede di scrivere a mano circa 130 date;
- short tenuto fino alle 21:30: il momento intraday documentato riguarda l'ultima mezz'ora della sessione americana (21:30–22:00), che si potrebbe prendere solo uscendo dopo le 22:00 con spread 7 su IG;
- scadenze del terzo venerdì e settimane con ora legale sfasata: direzione non dichiarabile o troppi pochi trade;
- variante di M9 senza la condizione della settimana debole, mai lanciata;
- il freno sul drawdown (`UsaFreno = 1`) non è stato provato su questo sistema.

## Come leggere i test

- Per i filtri e le uscite si confronta con la versione su cui il modulo è scritto, a 1 contratto (lo stesso file con `UsaMx = 0`), lato per lato; per il reinvestimento si confronta il drawdown in percentuale, non in euro.
- Accanto a ogni miglioramento va scritto quanti trade lo producono; con circa 100 € di dispersione per trade, una differenza di guadagno medio sotto i 20 € tra gruppi di 200-400 trade può essere caso.
- Il backtest usa uno spread fisso: le uscite alle 08:00, alle 19:30 e alle 21:30 su IG pagano 3,8 punti, e il long paga il finanziamento notturno.

Risultati in `registro-test.md`.
