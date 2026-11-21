# 185 TOP UA 342 – Nasdaq 100, 1 ora

Sistema sul Nasdaq 100, US Tech 100 Cash da 1 € di IG (profitti e `StrategyProfit` in euro), grafico a 1 ora, con un long solo il lunedì e uno short in qualunque giorno, indipendenti, che tengono la posizione fino a quattro giorni. Il codice viene dalla stessa libreria di pattern numerati di [185 oro](../185-top-ua-342-gc-1h/analisi.md), ma le logiche sono diverse. Andrea ha limitato il long al lunedì dopo aver visto ingressi validi anche negli altri giorni. Backtest dal 15 febbraio 2016.

Ricerca sul prodotto (orari, costi IG, letteratura): `fonti/prodotti/nasdaq.md`. La prima versione di questa analisi supponeva barre da 15 minuti; Andrea ha chiarito il 2026-11-21 che sono da 1 ora.

**Stato:** pronto per il reale: [DEFINITIVO-produzione](versioni/DEFINITIVO-produzione.txt) = originale con una console a rischio per trade (6% del capitale allo stop sul long, 10% sullo short, manopola di aggressività del reinvestimento), equivalente a M8 con la manopola a 1. M9 (leve diverse su capitale e profitti) funzionava ma era troppo complicato da gestire. Filtri, uscite e ingressi (M1–M7) provati, nessuno promosso.

## Cosa fa

Orari in ora italiana. `Time` è l'ora di chiusura della barra e gli ordini vengono eseguiti all'apertura della barra successiva; IG quota il US Tech 100 da lunedì 00:00 a venerdì 23:00, anche di notte.

**Long**, solo il lunedì, con segnale tra le 08:00 e le 20:00: compra quando la media delle ultime 5 chiusure orarie supera quella delle ultime 10. La seconda condizione, chiusura sopra il 99% della media a 5, in quel momento è sempre vera. Stop al 4%, target al 2,5%, uscita dopo 90 barre, cioè il venerdì più o meno all'ora d'ingresso del lunedì; il venerdì alle 21:00 chiude comunque. Un 2,5% in quattro giorni è circa un movimento normale del Nasdaq, quindi il target scatta spesso, mentre lo stop al 4% scatta nelle settimane di ribasso.

**Short**, qualunque giorno, con segnale tra le 16:00 e le 20:00, cioè dalla prima mezz'ora della seduta americana alle 14:00 di New York: vende se ieri ha chiuso nel 20% più alto della sua escursione e oggi il prezzo è sceso sotto l'apertura della giornata di almeno 4 volte l'escursione oraria media delle ultime 20 ore, circa l'1,5-2%. È una giornata che si gira con forza al ribasso dopo una chiusura forte. L'apertura della giornata è quella della candela giornaliera di ProRealTime, mezzanotte o l'01:00 secondo il forum, non l'apertura di New York. Stop al 4%, target all'1,6%; esce dopo 100 barre, al quarto giorno di calendario in posizione o il venerdì alle 21:00, quello che arriva prima.

**Taglia**, con `Reinvest = 0`: contratti = 4% di 5.000 / (prezzo × 4%), cioè 5.000 / prezzo sul long e 10.000 / prezzo sullo short, che rischia l'8%, con un minimo di 0,5 e un massimo di 80. È una posizione di valore costante (5.000 € sul long, 10.000 € sullo short) finché non scatta il minimo, cosa che sul long succede da quando l'indice ha superato 10.000 (giugno 2020) e sullo short da quando ha superato 20.000 (2024). Da allora i contratti restano a 0,5 e il valore della posizione cresce con l'indice, fino ai 14.000 € di oggi su entrambi i lati. Ne seguono due cose: nel backtest gli anni dal 2020 pesano sul long fino a tre volte di più dei precedenti, e in reale uno stop del long costa oggi 560 € invece dei 200 previsti, l'11% di 5.000 invece del 4%.

## Risultati dell'originale

Dal 2016 al febbraio 2026: 422 trade, 68% vincenti, 41,05 € a trade, profit factor 2,32, profitto 17.321 €, drawdown −772 €, tutti gli anni positivi. Numeri e lettura in `registro-test.md`.

Il long su un solo giorno, dall'ottimizzazione di Andrea: lunedì 55 € a trade, mercoledì 27, martedì 24, venerdì 15, giovedì 1,5. Il lunedì si stacca di circa 2,5 volte l'incertezza dal secondo giorno, e la differenza non viene dalla durata: il long del martedì resta aperto quasi quanto quello del lunedì e guadagna meno della metà. Se i due condividono il tratto da martedì a venerdì, le prime 24 ore circa del lunedì valgono più del resto della settimana.

## Che tipo di vantaggio hanno le gambe

Secondo i principi trasversali di `idee/idee-di-trading.md`:

- **Long: calendario** (come V1), con dentro il rialzo di fondo dell'indice. L'incrocio delle medie orarie decide a che ora del lunedì si entra; il risultato lo fanno i giorni successivi. Tutti i giorni della settimana sono positivi, e questo è il rialzo di fondo del Nasdaq (circa sei volte dal 2015); il lunedì aggiunge qualcosa di suo, concentrato a quanto pare nel primo giorno. Ipotesi possibili sul perché, nessuna provata: il lunedì raccoglie le notizie e gli ordini del fine settimana, e i flussi di fine mese lo fanno andare male solo nelle ultime settimane del mese (`fonti/prodotti/nasdaq.md`, A3). La tornata misura dove sta il guadagno nella settimana (M1), gestisce il rischio di un trade che è esposizione all'indice (M4) e aggiunge i giorni con una ragione indipendente dal backtest (M5).
- **Short: momento intraday**, come gli short del DAX (V4): vende una giornata che si gira al ribasso durante la seduta americana. Prima ipotesi è che renda nei periodi agitati (M3). Resta però aperto per giorni, e nei giorni dopo il movimento si inverte in parte (Baltussen et al. 2021), mentre la notte che segue una giornata di vendite è stata la più favorevole ai long: il guadagno dello short potrebbe stare nelle ore fino alla chiusura americana (M2).

## Problemi trovati nel codice

1. **Rischio reale più alto del previsto** per il minimo di 0,5 contratti (vedi Taglia): oggi il long rischia allo stop l'11% di 5.000 € invece del 4%, lo short l'11% invece dell'8%.
2. **Taglia dello short calcolata con lo stop del long** (`MySLL` invece di `MySLS`). Oggi sono uguali (4%), quindi non ha effetto; se si cambia lo stop dello short la taglia non lo segue.
3. **Reinvestimento.** Con `Reinvest = 1` il codice aggiunge al profitto 1.000 € inesistenti (`Strategyprofit + 1000`) e con `RiskOnProfit = 18` ogni euro di profitto aggiunge 4,5 euro di posizione, contro 1 euro per ogni euro di capitale. L'intestazione standard lo sostituisce con una leva unica sul capitale attuale.
4. **Contatore dei giorni in posizione.** Riparte solo quando si passa da fuori a dentro il mercato, quindi uno short che inverte un long eredita i giorni del long; `Day > Day[1]` non scatta al cambio di mese. Il limite di 4 giorni fa uscire gli short del lunedì e quelli nati da un'inversione il venerdì all'01:00 invece che alle 21:00. È un comportamento dell'originale e resta com'è: togliendolo, la prima versione di C0 ha perso un trade e 481 €.
5. **Condizioni che non fanno niente.** La chiusura sopra il 99% della media a 5; il limite di 8 giorni del long. `MaxEntriesPerDay = 1` è dichiarato ma non usato: dopo uno stop o un target lo stesso lato può rientrare nella giornata. Inutilizzati anche `PortATRpiu`, `uptn65`, `highd1`, `lowd1`, `BuyLot`, `TagliaPosizione` e il blocco dello stop dinamico.
6. **Long e short insieme.** Il long del lunedì è aperto fino al venerdì e lo short può scattare ogni pomeriggio: `SELLSHORT` chiude il long e apre lo short. Un modulo che cambia la durata del long cambia anche gli short (lezione di 165 DAX, M4).
7. **Lunedì festivi USA.** Circa 4 long l'anno partono con la borsa americana chiusa e i futures a orario ridotto.
8. **Costi non visti dal backtest.** Lo spread di IG (1,3 punti nella seduta americana, 2,5 nelle altre ore) vale lo 0,005-0,009% del prezzo e pesa poco. Pesa di più il finanziamento: il long tiene quattro notti, circa lo 0,02% del valore della posizione a notte con i tassi di oggi, cioè circa 11 € a trade con la posizione attuale da 14.000 €, contro un guadagno medio di 41-55 €. Lo short riceve o paga poco.

## Prima tornata: M1–M5

**Riferimento comune**: qualunque file della tornata con `UsaMx = 0`, che dà gli stessi trade dell'originale con un'altra taglia. **Taglia dei test**: posizione di valore fisso, 30.000 € per trade su entrambi i lati (`Reinvesti = 0`, `ContrattiFissi = 0`, `Leva = 6` su 5.000 €), cioè circa 1 contratto ai prezzi di oggi e 7 nel 2016: ogni anno pesa allo stesso modo, come ha insegnato l'oro, e il minimo di 0,5 contratti non scatta mai. Con lo stop fisso al 4%, valore fisso vuol dire anche rischio fisso allo stop (1.200 € a trade). È una variante dell'intestazione standard: con `ContrattiFissi = 0` e `Reinvesti = 0` la posizione vale `Leva × Capitale` e non cresce con i profitti. Le proposte hanno `DEFPARAM PreLoadBars = 3000` per la volatilità giornaliera di M3 e M4, quindi il backtest può partire qualche mese dopo quello dell'originale.

[C0](versioni/C0-originale-con-intestazione.txt) è l'originale con l'intestazione standard e la sua taglia: con `Capitale = 5000`, `Leva = 1`, `PesoShort = 2` e `MinContratti = 0.5` deve dare gli stessi numeri dell'originale. È la base per le versioni combinate.

| Modulo | Idea | Lato | Da dove viene |
|---|---|---|---|
| [M1](proposte/M1-uscita-long-a-orario.txt) | uscita del long il martedì alle 22:00; varianti martedì alle 09:00 e venerdì alle 09:00 | long | report per giorno di Andrea (lunedì 55 €, martedì 24 €); rialzo notturno all'apertura europea (A1); tratto della posizione (principio 1) |
| [M2](proposte/M2-short-esce-alla-chiusura-usa.txt) | uscita dello short alla chiusura americana dello stesso giorno; variante il giorno dopo | short | momento fino alla chiusura e inversione nei giorni dopo (A2), rialzo notturno dopo le vendite (A1) |
| [M3](proposte/M3-regime-di-volatilita.txt) | solo periodi agitati: volatilità di 2 settimane almeno pari a quella di 5 mesi | short; long per misurarlo | momento intraday (A2); `moduli/filtro-regime-volatilita.txt` |
| [M4](proposte/M4-taglia-long-a-volatilita.txt) | taglia del long inversa alla volatilità recente, tra metà e una volta e mezza | long (variante sullo short) | Moreira-Muir, Harvey (A4); `moduli/taglia-volatilita-uscita-a-tempo.txt` |
| [M5](proposte/M5-flussi-di-fine-mese.txt) | long anche negli altri giorni del cambio di mese; varianti: niente long nei lunedì da 8 a 4 giorni di borsa prima della fine del mese; long tutti i giorni, per misurare | long | Etula et al. 2020, McConnell-Xu 2008, Wang-Li-Erickson 1997 (A3) |

M2 e M5 non vengono dalla libreria. La variante proposta di M1 nasce dai report di Andrea e non da una fonte indipendente: va confermata anche sugli anni, non solo sul totale. M5 con `TuttiIGiorni = 1` è la misura chiesta da Andrea: i long del lunedì restano identici, e i trade in più sono solo quelli aperti negli altri giorni quando il lunedì non era in posizione.

## Prima tornata: esiti

Confronti con il riferimento a valore fisso (30.000 € a trade), ricavato dai long di M2 e dagli short di M4; Andrea li aveva confrontati con l'originale, che ha un'altra taglia. Numeri in `registro-test.md`.

| Modulo | Esito |
|---|---|
| M1 long esce martedì 22:00 | il tratto da martedì sera a venerdì rende 74 € a trade e il drawdown sale: scartato. Il guadagno del long è distribuito su tutta la settimana, e le perdite arrivano nei primi giorni |
| M2 short esce alla chiusura | 60 € nel primo giorno, 99 € nei giorni dopo: lo short è momento di più giorni. Scartato |
| M3 solo periodi agitati | long 226 contro 128 € a trade, short 242 contro 100 €; trade scartati positivi e drawdown tutto nei periodi agitati: non adottato come filtro |
| M4 taglia del long a volatilità | profitto / drawdown da 16,5 a 17,2, dentro il rumore: non adottato |
| M5 cambio di mese | i 118 long aggiunti perdono 34 € a trade: scartato |

**Cosa dice sul tipo di vantaggio.** Lo short non è momento intraday come gli short del DAX, ma la prosecuzione per giorni di un forte calo, più forte nei periodi agitati. Il long è il lunedì più il rialzo della settimana: guadagna in tutti i tratti, rende di più nei periodi agitati (al contrario di quanto previsto) ma è lì che ha il drawdown. Ne segue che filtri e uscite anticipate tolgono profitto quanto rischio; restano da provare più trade dove il vantaggio è più forte (M6, M7) e la gestione della taglia (M8).

## Seconda tornata: M6–M8, sopra C0

Tre tentativi più audaci, su richiesta di Andrea. Il riferimento di M6 e M7 è già noto (riferimento della prima tornata), quindi basta lanciare i moduli attivi.

| Modulo | Idea | Lato | Da dove viene |
|---|---|---|---|
| [M6](proposte/M6-short-su-ogni-forte-calo-agitato.txt) | short anche sui forti cali senza il pattern dell'originale, solo nei periodi agitati e senza toccare i long; varianti: anche nei periodi calmi, target al 3% | short | M2 (il calo prosegue per giorni), M3 (più forte nei periodi agitati) |
| [M7](proposte/M7-long-tutti-i-lunedi.txt) | long anche nei lunedì senza incrocio, alle 20:00; variante: ogni lunedì alle 09:00 | long | report per giorno (il lunedì è il giorno buono), M5 (gli altri giorni no) |
| [M8](proposte/M8-reinvestimento-a-leva-costante.txt) | reinvestimento a leva 1,5 con PesoShort 1,65, che pareggia i drawdown dei due lati; varianti leva 1 e 2, freno | entrambi | intestazione standard (165 DAX, M8), drawdown della prima tornata |

M6 e M7 aggiungono trade, quindi si giudicano sul guadagno medio dei trade aggiunti e sul rapporto profitto / drawdown. M8 si giudica sul drawdown in percentuale del capitale e sul capitale finale.

## Seconda tornata: esiti e M9

| Modulo | Esito |
|---|---|
| M6 short su ogni forte calo agitato | 55 short aggiunti da 8 € a trade, drawdown dello short +52%: il pattern dell'originale seleziona davvero. Scartato |
| M7 long tutti i lunedì | 170 long aggiunti da 24 € a trade, meno di quattro notti di finanziamento e spread. L'incrocio delle medie contiene un'informazione. Scartato |
| M8 leva 1,5, PesoShort 1,65 | da 5.000 a 213.000 € in dieci anni, circa 46% l'anno, profit factor 2,48. Andrea lo vuole più aggressivo sui profitti |

Il sistema resta quello dell'originale: dieci prove di filtri, uscite e ingressi non l'hanno migliorato, e il vantaggio sta nella combinazione esatta di lunedì, incrocio e pattern dello short. Quello che si può ancora migliorare è la taglia.

[M9](proposte/M9-leva-piu-alta-sui-profitti.txt): leva 1,5 sul capitale versato e 4 sui profitti, con la leva effettiva che arriva a 3 quando il capitale è triplicato e poi scende a 2 tra 4 e 10 volte il versato; PesoShort 1,65. Ha una riga `GRAPH` del drawdown in percentuale del capitale, che il report non dà.

## Come leggere i test

- Ogni modulo si legge lato per lato (report long e short separati): guadagno medio, profit factor, profitto / drawdown, tempo in posizione e anni.
- **Uscite (M1, M2) e taglia (M4)**: stessi ingressi del riferimento, quindi si confrontano guadagno medio, drawdown e profitto / drawdown. Tra due varianti di uscita la differenza di profitto è quanto rende il tratto di posizione che le separa. Un'uscita più rapida con meno profitto ma drawdown molto più basso vale se profitto / drawdown sale, perché poi si alza la taglia.
- **Filtri (M3, variante di M5)**: guadagno medio dei trade scartati = (profitto riferimento − profitto modulo) / (trade riferimento − trade modulo), confrontato con quello dei tenuti e con l'incertezza ricavata da vincente e perdente medio.
- **Trade aggiunti (M5)**: stessa formula con i segni opposti, confrontata con il guadagno medio dei lunedì. Aggiunge esposizione, quindi si confronta con il riferimento ingrandito dello stesso guadagno.
- Al guadagno medio del long va tolto il finanziamento delle notti, che il backtest non conta: con i tassi di oggi circa lo 0,02% del valore della posizione a notte, 6 € a notte con i 30.000 € dei test, meno della metà negli anni a tassi vicini a zero. Conta soprattutto per M1, che toglie tre notti su quattro.

Risultati in `registro-test.md`.
