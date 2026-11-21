# 185 TOP UA 342 – oro 1H

Sistema sull'oro a pronti, grafico a 1 ora, con una gamba long e una short indipendenti che entrano dopo un forte movimento della giornata e tengono la posizione per alcuni giorni. Gira sullo Spot Gold (E1) di IG, il contratto da 1 € per punto (1 punto = 1 $ del prezzo dell'oro): profitti, `StrategyProfit` e capitale sono tutti in euro. Backtest di Andrea dal 3 ottobre 2016.

Ricerca sul prodotto (orari, costi IG, letteratura): `fonti/prodotti/oro.md`.

**In produzione:** [DEFINITIVO-produzione.txt](versioni/DEFINITIVO-produzione.txt) = logica dell'originale invariata, intestazione standard a rischio allo stop con la manopola `Aggressivita`, target dello short scritto nel codice. Dodici moduli in tre tornate, nessuno promosso.

## Cosa fa

Orari in ora italiana. `Time` è l'ora di chiusura della barra e gli ordini vengono eseguiti all'apertura della barra successiva; l'oro su IG è quotato dalle 00:00 alle 23:00, con una pausa ogni sera.

**Long**, con segnale tra le 11:00 e le 22:00 di qualunque giorno: compra se il prezzo è salito dall'apertura della giornata di almeno 2,5 volte l'escursione media oraria delle ultime 200 ore (circa 9 giorni di quotazione) e se il massimo dell'ultima barra supera quello della barra precedente di almeno lo 0,5%. Non entra se il minimo di oggi è già più dell'1% sopra quello di ieri. Stop a 3 volte l'escursione media delle ultime 20 ore, target a 13 volte. Esce alla prima barra del quarto giorno di calendario dopo l'ingresso (verso l'01:00), oppure dopo 80 barre se è in perdita, e comunque dopo 106.

**Short**, stessi orari: vende se il prezzo è sceso dall'apertura della giornata di almeno 5,5 volte l'escursione media oraria delle ultime 200 ore e se il minimo dell'ultima barra è sotto quello della precedente di almeno lo 0,5%, cioè solo nelle giornate di forte ribasso. Non entra se ieri ha chiuso in calo dopo un giorno in rialzo. Stop a 3 volte l'escursione media delle ultime 20 ore, nessun target scritto (ma vedi il problema 3), uscita dopo 60 barre, cioè verso la mattina del terzo giorno dopo l'ingresso.

**Taglia**: si perde allo stop il 4% di 4.000 + 200 + profitti, quindi contratti = rischio / distanza dello stop in punti, con un minimo di 0,5 e un massimo di 80. Lo stop è misurato in escursioni medie, per cui è una taglia legata alla volatilità: meno contratti quando l'oro si muove molto, di più quando si muove poco. Con il contratto da 1 € per punto la formula torna senza correzioni.

**Perché all'inizio entra con 15-20 contratti.** La formula è corretta e fa quello per cui è scritta: nel 2016 l'oro valeva circa 1.300 $ e si muoveva di pochi dollari l'ora, quindi lo stop di 3 escursioni orarie valeva circa 8-10 punti e per rischiare 168 € (4% di 4.200) servivano 17-20 contratti; oggi l'oro vale 4.000 $ e lo stop vale molti più punti, quindi bastano molti meno contratti. È questo che rende diritta la curva: ogni trade rischia la stessa frazione del capitale, nel 2016 come nel 2026. A 1 contratto fisso invece un trade del 2016 vale pochi euro e uno del 2026 decine, e il 2026 da solo fa metà del profitto del long.

Quello che c'è di pericoloso è la leva, non lo spread: 20 contratti con l'oro a 1.300 $ valgono 26.000 € di posizione su 4.200 € di capitale (leva circa 6), e un salto di prezzo di 30-40 $ alla riapertura del lunedì costerebbe 600-800 € invece dei 168 previsti. Lo spread (0,3 punti a contratto, già nel backtest) vale circa il 3% del rischio quando lo stop è di 10 punti e meno dell'1% oggi; IG non applica commissioni sull'oro; il finanziamento notturno, che il backtest non conta, vale qualche euro a trade.

## Che tipo di vantaggio hanno le gambe

Secondo i principi trasversali di `idee/idee-di-trading.md` le due gambe sono di **momento**, ma non intraday come gli short del DAX (V4): entrano dopo un movimento ampio della giornata e restano aperte per due o tre giorni, attraversando due o tre sessioni asiatiche.

- **Long**: rottura al rialzo con conferma di una barra oraria molto ampia. Una parte del suo guadagno potrebbe non venire dalla rottura ma dalle notti: tra il 2001 e il 2018 l'oro è salito in media nelle ore asiatiche (23:00-09:00) e sceso in quelle di Londra (`fonti/prodotti/oro.md`, A1). Il long esce verso l'01:00, cioè proprio all'inizio di quella finestra.
- **Short**: vende i crolli della giornata, quando partono liquidazioni e stop a catena (30 gennaio 2026: −9,5% in una seduta). Va contro la salita di fondo dell'oro, sia di lungo periodo (2001-2011, 2019-gennaio 2026) sia notturna, e per questo può funzionare solo se la spinta del crollo prosegue per più giorni.
- **Filtro di volatilità nascosto**: la barra dello 0,5% è una soglia fissa, non legata alla volatilità. Negli anni calmi una barra oraria così ampia è rara, negli anni agitati è normale, quindi il sistema opera soprattutto negli anni agitati e il backtest dipende da pochi periodi. I risultati vanno letti anno per anno.

Restano da misurare tre cose: quanto del long viene dalle notti (M1), se tra i trade presi quelli dei periodi più agitati guadagnano di più (M2), se lo short funziona solo quando l'oro è in calo da mesi (M3).

## Problemi trovati nel codice

1. **Valuta del capitale.** Risolto: con il contratto E1 `StrategyProfit` è in euro come il capitale.
2. **Esclusione di giugno-novembre 2011.** Toglie a mano i mesi del massimo dell'oro e del crollo successivo, ma il backtest di Andrea parte dal 2016, quindi non ha alcun effetto; resta come interruttore (`Escludi2011`) nei file.
3. **Target dello short.** Con `TPmultS = 0` lo short non imposta un target, ma usa quello dell'ultimo long ancora attivo: senza i long (`EntraLong = 0`) i suoi vincenti durano di più e spariscono i grandi guadagni chiusi entro il primo giorno. Il target dello short è quindi 13 escursioni orarie misurate all'ingresso dell'ultimo long, un valore che dipende da un altro trade. Funziona (profit factor 2,71 contro 2,48), ma va reso esplicito: M5.
4. **Parametri e pattern scelti per ottimizzazione.** Il codice viene da una libreria di pattern numerati (`ptnl25`, `uptn104`, `uptn139`), con valori come 2,5, 5,5, 13, 106, 80 e 60 e forti asimmetrie tra long e short; per i due pattern di esclusione non ho trovato una ragione economica. Un backtest scelto così sovrastima il vantaggio (Bailey et al., `fonti/paper/schede.md`): il confronto onesto è sul periodo successivo alla costruzione del sistema, per cui serve sapere quando è stato costruito.
5. **Contatore dei giorni.** `Day > Day[1]` non scatta al cambio di mese (dal 31 all'1), quindi una posizione aperta a cavallo di fine mese resta un giorno in più o esce per numero di barre. Il weekend conta un solo giorno, per cui un long aperto il giovedì esce il mercoledì successivo con lo stesso numero di barre di uno aperto il lunedì. `MaxEntriesPerDay = 1` è dichiarato ma non usato: dopo uno stop il sistema può rientrare lo stesso giorno.
6. **Uscita del long all'01:00.** L'uscita a tempo scatta alla prima barra del giorno, subito dopo la pausa serale, quando lo spread di IG è più largo, e all'inizio delle ore asiatiche in cui l'oro è salito in media. Su questo c'è M1.
7. **Stop e target ricalcolati.** Se la condizione d'ingresso si ripete con la posizione già aperta, l'ordine non parte ma `SET STOP` e `SET TARGET` vengono rieseguiti con l'escursione media del momento, di solito più alta dopo una barra ampia: lo stop si allarga. Probabilmente raro.
8. **Leva alta quando l'oro è calmo.** Con il 4% di rischio e uno stop stretto la posizione arriva a 6 volte il capitale (vedi sopra); un salto di prezzo oltre lo stop costa allora più del 4% previsto. Su questo c'è M7.
9. **Costi non visti dal backtest.** Spread già incluso (0,3 punti). Il finanziamento notturno (tasso tom-next più 0,8% annuo) non c'è: con un tasso del 4-5% annuo e una leva media di circa 4, ogni notte di un long costa circa lo 0,05% del capitale, e con circa 50 notti l'anno in posizione sono 2-3 punti percentuali di rendimento l'anno (stima). Lo short ne paga molto meno.

## Prima tornata: M1–M4 (esiti)

Riferimento: originale a 1 contratto. Numeri e calcoli in `registro-test.md`. A 1 contratto il 2026 fa da solo metà del profitto del long, quindi questi confronti pesano quasi solo gli ultimi due anni.

| Modulo | Esito |
|---|---|
| [M1](proposte/M1-uscite-attorno-sessione-asiatica.txt) long esce alle 09:00 | stessi trade, −0,43 € a trade, drawdown −5%: nessun effetto, scartato. Short non visto |
| [M2](proposte/M2-regime-di-volatilita.txt) solo periodi agitati | long: 18,88 € a trade contro 7,81 € dei calmi (al limite del caso), ma restano 78 trade su 183; short: direzione opposta, i calmi rendono di più (17,33 contro 6,98 €). Si rimisura a rischio fisso come peso (M6) |
| [M3](proposte/M3-trend-di-fondo-12-mesi.txt) trend di 12 mesi | gli screenshot indicati come M4 sono di M3. Long: i trade contro il trend guadagnano meno ma sono positivi, drawdown uguale; short: toglie 50 trade su 65 che rendevano più dei tenuti. Scartato |
| [M4](proposte/M4-taglia-rischio-o-leva.txt) rischio o leva | non lanciato; Andrea tiene la taglia normalizzata dell'originale, che diventa C0 |

**Cosa dice sul tipo di vantaggio.** Il long rende di più quando la volatilità è già in salita, come una gamba di momento, e perde negli anni calmi (2016, 2017, 2019 nell'originale). Lo short, se c'è un segnale, va al contrario: rende di più quando il crollo arriva in un periodo calmo. Una spiegazione possibile è che dopo una fase tranquilla le posizioni sull'oro sono grandi e chi gestisce il rischio sulla volatilità (fondi a volatilità obiettivo, trend follower) deve ridurle per giorni quando la volatilità salta, mentre in una fase già agitata le posizioni sono già state ridotte. È un'ipotesi nata guardando i risultati, quindi M6 non è una prova indipendente.

## Seconda tornata: M5–M7, sopra C0

**C0** ([versioni/C0-originale-con-intestazione.txt](versioni/C0-originale-con-intestazione.txt)) è l'originale con l'intestazione standard, nella variante per sistemi con stop legato alla volatilità: al posto della leva c'è `RischioStop`, la percentuale del capitale persa allo stop, e un tetto alla leva per lato. Con `Reinvesti = 1`, `Capitale = 4000` e `ProfittoPrecedente = 200` riproduce l'originale. Con `Reinvesti = 0` il rischio è fisso, 160 € per trade, ed è il modo dei test: la curva resta diritta come quella dell'originale, ogni anno pesa allo stesso modo e i guadagni medi sono confrontabili.

| Modulo | Idea | Lato | Da dove viene |
|---|---|---|---|
| [M5](proposte/M5-target-short-esplicito.txt) | target dello short scritto nel codice (13 escursioni orarie, varianti 8 e nessun target) invece di quello ereditato dal long | short | problema 3; acquisti fisici dopo i crolli (WGC, aprile 2013) |
| [M6](proposte/M6-peso-per-regime-di-volatilita.txt) | metà posizione ai long dei periodi calmi e agli short dei periodi agitati, senza togliere trade | entrambi | M2 rimisurato a rischio fisso |
| [M7](proposte/M7-tetto-alla-leva.txt) | leva massima 5 sul long | long (variante sullo short) | problema 8; anni calmi in perdita |

## Seconda tornata: esiti

Andrea ha lanciato i moduli con la taglia del suo originale; riferimento l'originale (dettagli in `registro-test.md`).

| Modulo | Esito |
|---|---|
| [M1](proposte/M1-uscite-attorno-sessione-asiatica.txt) short esce prima della terza notte | profitto −8%, drawdown +9%: scartato. Con il risultato sul long, la salita asiatica dell'oro non si vede in questi trade |
| [M5](proposte/M5-target-short-esplicito.txt) target dello short esplicito | non ricevuto |
| [M6](proposte/M6-peso-per-regime-di-volatilita.txt) metà posizione nei regimi deboli | long: profitto e drawdown −22-23%, rapporto uguale; short: rapporto da 8,23 a 7,70. Equivale a ridurre la taglia: scartato |
| [M7](proposte/M7-tetto-alla-leva.txt) leva massima 5 sul long | profitto −7%, drawdown −7%: nessun effetto, scartato |

**Cosa ne viene.** Le modifiche di taglia per regime e i ritocchi delle uscite spostano profitto e drawdown nella stessa proporzione: il vantaggio delle due gambe non dipende dal regime di volatilità né dall'ora d'uscita. Per cambiare davvero il risultato bisogna cambiare il modo in cui il sistema entra, esce o misura il rischio.

## Terza tornata: M8–M12, sopra C0

Modifiche più forti, una per file, ciascuna con un interruttore che con 0 riproduce C0. I file hanno le impostazioni del capitale dell'originale (`Reinvesti = 1`, 4.000 + 200 €), così il riferimento è l'originale già lanciato.

| Modulo | Idea | Cosa cambia |
|---|---|---|
| [M8](proposte/M8-uscita-rapida-trade-fermi.txt) | chi dopo 10 barre è ancora in perdita esce | trade più "oculati", meno tempo in posizione e meno finanziamento |
| [M9](proposte/M9-long-segue-il-trend.txt) | il long esce a trailing (6 escursioni orarie sotto la chiusura più alta), senza target e con scadenza a 10 giorni | il long diventa un sistema di trend; più giorni in posizione |
| [M10](proposte/M10-piu-short.txt) | allo short basta un calo di 4 escursioni orarie dall'apertura invece di 5,5 | più short |
| [M11](proposte/M11-volatilita-giornaliera.txt) | stop e target in escursioni giornaliere (stop 1,5 volte quella degli ultimi 20 giorni), stesso rischio in euro | gestione della volatilità: stop più largo, meno contratti, meno leva |
| [M12](proposte/M12-senza-pattern-di-esclusione.txt) | via i due pattern di esclusione `uptn104` e `uptn139` | più trade; dice se i pattern contengono informazione |

## Terza tornata: esiti

Dettagli in `registro-test.md`; riferimento l'originale con la sua taglia.

| Modulo | Esito |
|---|---|
| M8 uscita dei trade in perdita alla barra 10 | long: vincenti dal 46 al 32%, drawdown quasi doppio; short peggiore. Le rotture dell'oro non partono subito: scartato |
| M9 long a trailing | profitto +19% con vincenti molto più grandi, ma drawdown +54% e rapporto da 11,46 a 8,88: scartato |
| M10 short con calo di 4 escursioni | i 55 short aggiunti perdono 38,76 € ciascuno: la soglia di 5,5 è vera, scartato |
| M11 stop in escursioni giornaliere | più vincenti (56%) e profit factor del long 1,89, ma rapporto profitto / drawdown più basso su entrambi i lati e posizioni più lunghe: scartato |
| M12 senza pattern di esclusione | i long aggiunti perdono 120 € ciascuno, gli short aggiunti sono a zero: i pattern restano |

## Conclusione

Il vantaggio del sistema sta nelle sue parti originali: rotture forti della giornata, stop e taglia legati alla volatilità oraria, uscita a tempo dopo 3-4 giorni, crollo minimo di 5,5 escursioni per lo short, esclusione dei long a giornata già tutta sopra ieri. Le prove che toglievano o allargavano una di queste parti hanno peggiorato i risultati, quelle che cambiavano taglia o ora d'uscita hanno solo spostato profitto e drawdown insieme. Quello che si è guadagnato è nella gestione del capitale: la taglia a rischio costante rende diritta la curva (a 1 contratto il 2026 faceva metà del profitto), e la manopola `Aggressivita` permette di scegliere il drawdown.

Restano aperti: il costo del finanziamento notturno, che il backtest non conta (stima di 2-3 punti di rendimento l'anno sul long); la taratura di `Aggressivita` sul drawdown del sistema intero, mai letto nel report "tutte le posizioni"; il target dello short scritto nel codice (M5), da verificare con un lancio della versione definitiva contro l'originale.

## Uso in reale

- **File**: [DEFINITIVO-produzione.txt](versioni/DEFINITIVO-produzione.txt) in ProOrder; [DEFINITIVO-controllo-drawdown.txt](versioni/DEFINITIVO-controllo-drawdown.txt) è la stessa versione con le righe del drawdown, solo per il backtest (`MostraEuro` sceglie percentuale o euro).
- **Capitale**: Andrea ha 7.200 € sul conto; `Capitale = 7200`, `ProfittoPrecedente` = profitti già realizzati da contare per la taglia.
- **Nessun capitale minimo**: la posizione non scende mai sotto `MinContratti` (0,5), quindi il sistema entra sempre. Con 7.200 € e il 4% il minimo scatta solo con uno stop oltre 576 punti; il margine IG (circa 5% della posizione per i clienti al dettaglio) per 5 contratti con l'oro a 4.000 $ è circa 1.000 €. Da verificare nella scheda "Info" di IG la taglia minima dello Spot Gold (E1).
- **Aggressività**: Andrea non vuole essere conservativo. Si sceglie con `Aggressivita` = drawdown accettato / drawdown massimo % letto con 1, poi si rilancia. In un lancio con aggressività più alta il drawdown massimo in euro è stato 29.370 € su circa 185.000 € di capitale finale; la percentuale va letta sulla riga corretta. Con l'aggressività sale la leva: un salto di prezzo alla riapertura del lunedì oltre lo stop costa un multiplo del rischio previsto.

## Come leggere i test

- Dalla terza tornata si confronta con l'originale con la sua taglia, come fa Andrea: rapporto profitto / drawdown, profit factor, guadagno medio e barre annuali, lato per lato. Con il reinvestimento un modulo su un lato sposta di poco anche l'altro, perché il capitale è comune.
- Un modulo che cambia la taglia di un gruppo di trade va giudicato sul rapporto profitto / drawdown: se resta uguale, equivale a cambiare la taglia di tutto il sistema.
- I filtri si giudicano sul guadagno medio dei trade scartati, con l'incertezza ricavata da vincente e perdente medio del report.
- Obiettivo di Andrea per il reale: drawdown massimo del sistema intero tra 1.000 e 1.500 €. A rischio fisso il drawdown in euro è proporzionale a `RischioStop`, quindi si tara alla fine leggendo il drawdown del report "tutte le posizioni".

Risultati in `registro-test.md`.
