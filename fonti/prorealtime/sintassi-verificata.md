# ProRealCode – sintassi verificata

Controllata sulla documentazione ufficiale il 2026-11-20. Indice generale: https://www.prorealcode.com/documentation/ – manuale ProBacktest/ProOrder in PDF: https://www.prorealcode.com/wp-content/uploads/2025/12/probacktest_en.pdf

| Istruzione | Sintassi | Note |
|---|---|---|
| Stop e target | `SET STOP LOSS x`, `SET TARGET PROFIT x` | `x` è una distanza in prezzo dall'ingresso. Le varianti `%LOSS`/`%PROFIT` (percentuale), `pLOSS`/`pPROFIT` (punti), `$LOSS` (denaro) sono in uso comune ma non descritte nella pagina [SET](https://www.prorealcode.com/documentation/set/). Sul forum si usa `SET STOP pLOSS 0` per togliere lo stop. |
| Stop e target al prezzo d'ingresso | `SET STOP BREAKEVEN`, `SET TARGET BREAKEVEN` | Il primo sposta lo stop al prezzo d'ingresso della posizione, il secondo mette lì il target (utile su una posizione in perdita); restano attivi finché un nuovo `SET STOP` o `SET TARGET` non li cambia ([doc](https://prorealcode.com/documentation/breakeven), letta tramite riassunto il 2026-11-21). Usati in 138 DAX. |
| Persistenza di stop e target | `SET TARGET %PROFIT x` eseguito per un ordine resta attivo sugli ordini successivi che non ne impostano uno | Osservato in backtest, non documentato: su 185 oro lo short senza target usa quello dell'ultimo long (con `EntraLong = 0` i vincenti dello short durano di più e spariscono le chiusure rapide in guadagno). Per non ereditarlo, ogni gamba deve impostare il proprio target; un target irraggiungibile (`SET TARGET %PROFIT 50`) equivale a nessun target. |
| Profitto della strategia | `StrategyProfit` | Somma dei soli trade chiusi, **nella valuta dello strumento** (manuale ProBacktest), esclusi i costi: su AUDJPY è in yen. Sul forum ci sono segnalazioni contrastanti per il reale da conto in altra valuta: verificare prima di usarlo per la taglia. Non va mai sommato a un capitale in euro. [doc](https://www.prorealcode.com/documentation/strategyprofit/), [forum](https://www.prorealcode.com/topic/calculating-working-capital-for-money-management/) |
| Prestazione posizioni chiuse | `PositionPerf(n)` | n = 0 posizione aperta, n ≥ 1 n-esima posizione chiusa. È un rapporto (0,2 = +20%). Il segno per gli short non è documentato. [doc](https://www.prorealcode.com/documentation/positionperf/) |
| Dimensione posizione | `CountOfLongShares`, `CountOfShortShares`, `CountOfPosition` | Lotti in essere; `CountOfPosition` ha segno (negativo se short). |
| Ordini pendenti | `BUY x LOTS AT livello STOP`, `SELL AT livello STOP`, `... LIMIT` | Valgono una sola barra: vanno ripetuti a ogni barra. `SELL` senza quantità chiude tutto il long. |
| Ordine stop già superato | `BUY x LOTS AT livello STOP` con il prezzo già sopra `livello` | Non documentato, ma **verificato in backtest**: ProBacktest lo esegue all'apertura della barra successiva. Su 097 BRK GBP/JPY la versione che in quel caso compra al mercato ha dato esattamente gli stessi trade dell'originale su entrambi i lati (457 long, 241 short, 2016-2026). In reale su IG, gli ordini troppo vicini al prezzo o dal lato sbagliato vengono rifiutati e il sistema può fermarsi (forum, per gli ordini limite: [1](https://www.prorealcode.com/topic/order-level-too-close-to-market-level-with-limit-buy-order/), [2](https://www.prorealcode.com/reply/60596)); il backtest può contenere ordini che IG non eseguirebbe ([3](https://prorealcode.com/topic/backtest-resullt-with-limit-orders-too-close-to-market-level)). Soluzione usata in 097 BRK C0: se il prezzo è già oltre il livello, ordine al mercato (`IngressoEsplicito`). |
| Ordine opposto con posizione aperta | `BUY` con uno short aperto | Chiude lo short e apre il long (inversione); per chiudere senza invertire si usa `EXITSHORT`. Non si possono avere long e short insieme. Fonte: risposte dei moderatori sul [forum](https://prorealcode.com/topic/invert-position), non la documentazione. |
| Cicli | `FOR k = a TO b DO` … `NEXT` | Usato in 165 DAX M3 per contare i giorni di borsa del mese; con `a > b` va protetto da un `IF`. |
| Data e calendario | `Date`, `Day`, `Month`, `Year`, `DayOfWeek` | `Date` è un numero YYYYMMDD; `DayOfWeek` va da 0 (domenica) a 6 (sabato). Esiste anche l'operatore `MOD` per il resto della divisione ([doc](https://prorealcode.com/documentation/mod)). |
| Ordini cumulati | `DEFPARAM CumulateOrders = True` | Stop e target impostati con `SET` sono ricalcolati sul prezzo medio di carico a ogni variazione della posizione (manuale ProBacktest). `TRADEINDEX` dopo un'aggiunta punta alla barra dell'aggiunta. |
| Grafici di controllo | `GRAPH variabile AS "nome"` | Solo in ProBacktest; non ammesso in ProOrder, va tolto prima del reale. Tutte le righe `GRAPH` di un sistema finiscono nello stesso riquadro con una scala sola: una riga in euro (migliaia) schiaccia sul fondo una in percentuale (decine). Grandezze con scale diverse vanno mostrate una alla volta con un interruttore (185 oro, controllo del drawdown). [doc](https://www.prorealcode.com/documentation/graph/) |
| Valore del punto | `PointValue`, `PointSize` | Valore monetario di un punto (nella valuta dello strumento) e sua ampiezza in prezzo. Perdita in denaro ≈ distanza / PointSize × PointValue × contratti. [doc](https://www.prorealcode.com/documentation/pointvalue/) |
| ATR | `AverageTrueRange[N](close)` | Media di Wilder del true range. [doc](https://www.prorealcode.com/documentation/averagetruerange) |
| Più timeframe | `TIMEFRAME(daily, updateonclose)` … `TIMEFRAME(default)` | `updateonclose` usa solo barre chiuse. I timeframe superiori devono essere multipli di quello del grafico; dal forum, massimo 6 timeframe. [doc](https://prorealcode.com/documentation/timeframe-probacktest-proorder) |
| Orari | `Time`, `OpenTime` | `OpenTime` è l'ora di apertura della barra (HHMMSS). La documentazione di `Time` non dice se è apertura o chiusura; nell'uso comune è l'ora di chiusura. |
| Barre precaricate | `DEFPARAM PreLoadBars = n` | Almeno quanto il periodo più lungo usato. Dal forum, massimo 10000. [doc](https://www.prorealcode.com/documentation/preloadbars/) |
| Inizializzazione | `ONCE variabile = valore` | Eseguita solo alla prima barra. [doc](https://www.prorealcode.com/documentation/once/) |
| Prezzi dei trade | `TradePrice(N)`, `PositionPrice` | Prezzo del trade N-esimo all'indietro; prezzo medio della posizione aperta. |
| Funzioni matematiche | `EXP`, `LOG`, `SQRT`, `ABS`, `max(a,b)`, `min(a,b)` | Per le potenze si può usare `EXP(k*LOG(x))`. |

## Report di ProBacktest e conto IG

- Il backtest è nella valuta dello strumento (AUD/JPY Mini: yen, capitale iniziale 800.000 ¥ usato da Andrea).
- Il "Rapporto dettagliato" si filtra per posizioni long o short: utile per giudicare i moduli che toccano un solo lato.
- Con `CumulateOrders = True` ogni aggiunta conta come trade separato nel numero di trade e nel guadagno medio.
- Il backtest non include il costo di finanziamento overnight; spread e commissioni vanno considerati quando un modulo aggiunge molte posizioni piccole.
- Lo spread del backtest è fisso, mentre su IG cambia con l'ora: sul Germany 40 è 1,6 punti dalle 09:00 alle 17:30 e 3,8 o più nelle altre ore (`fonti/prodotti/dax.md`). Un sistema che esce fuori dall'orario di Xetra paga più di quanto mostra il backtest.
- Su AUD/JPY Mini un contratto vale circa 100 ¥ per pip (0,01): con stop allo 0,4% e circa 3,75 contratti, la perdita a stop del long è circa 15.000 ¥.
- Un riavvio del sistema in ProOrder azzera `StrategyProfit` e le variabili `ONCE`: per il reinvestimento serve riportare a mano il profitto precedente.

Esempi di trailing stop dal blog di ProRealCode: https://www.prorealcode.com/blog/learning/kinds-trailing-stop-proorder/
