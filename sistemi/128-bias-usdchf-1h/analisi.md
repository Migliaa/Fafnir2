# 128 BIAS USDCHF 1H – analisi

Codice passato da Andrea il 2026-11-21, solo short attivo. Grafico a 1 ora, orari italiani (da confermare: lo suggeriscono le date escluse, vedi sotto). Contratto supposto: USD/CHF Mini di IG, 10.000 dollari, 1 franco per pip; `StrategyProfit` è quindi in franchi. Ricerca sul prodotto: `fonti/prodotti/usdchf.md`.

Andrea lo considera un sistema con poche speranze («il core si è rotto o era sovra-adattato di suo, o comunque non guadagna abbastanza») e chiede modifiche anche non modulari, con pochi tentativi.

## Cosa fa

**Short.** Vende il mercoledì alla barra che chiude alle 13:00 (ingresso all'apertura delle 13:00), tranne febbraio e agosto, e chiude il venerdì alle 17:00, cioè al fixing WM/Reuters di Londra; il limite di 51 barre coincide con quell'uscita (dalle 13:00 del mercoledì alle 17:00 del venerdì sono 52 barre). Stop all'1%, target al 3,5%.

- Con un'escursione giornaliera di circa lo 0,55%, in 52 ore il prezzo oscilla di circa lo 0,8%: lo stop all'1% scatta in una parte dei trade, il target solo con eventi come quelli della BNS. È un'uscita a tempo con stop abbastanza lontano.
- Due condizioni dalla libreria di pattern:
  - `uptn042` (richiesta): oggi il calo dall'apertura al minimo è meno di 1,5 volte quello di ieri. Evita di vendere dopo una mattina già in forte calo.
  - `uptn020` (esclusione): `abs(Open[5]-Close[1]) > 0.7*(high[5]-low[1])`. Il secondo termine non è un'escursione, ma la differenza tra il massimo di 5 barre fa e il minimo dell'ultima: dopo cinque ore in calo vale circa l'ampiezza del calo, e la condizione esclude i cali regolari; dopo cinque ore in salita è piccolo o negativo, e la condizione esclude quasi sempre. In pratica lo short entra solo se le ultime cinque ore non hanno avuto una direzione netta.
- Febbraio e agosto esclusi senza una ragione economica: quasi certamente scelti sul backtest.

**Long (spento).** Compra il venerdì alle 17:00, tranne luglio, se `Dlow(0) > 2*Dlow(1)`, condizione che su un cambio vicino a 1 non è mai vera: anche acceso non entrerebbe. Andrea dice di averlo cercato a lungo senza trovarlo.

**Date escluse.** Il 14 gennaio 2015 è il mercoledì prima dell'abbandono del cambio minimo con l'euro da parte della BNS (giovedì 15, USD/CHF da 1,02 a sotto 0,90 in pochi minuti): uno short aperto quel giorno avrebbe preso il target del 3,5% con un movimento che nessun sistema avrebbe potuto eseguire a quei prezzi. Toglierlo è corretto. Il 2 settembre 2011 è il venerdì prima dell'introduzione del cambio minimo (martedì 6 settembre, USD/CHF +8%): toglie un long fortunato. Le due date confermano grafico giornaliero e orari italiani.

## Problemi

1. **Indizi di sovra-adattamento.** Mesi esclusi senza motivo, due pattern scelti da una libreria, giorno e ora d'ingresso e d'uscita fissati su un solo valore. Sui cambi gli effetti del giorno della settimana documentati negli anni '70 e '80 sono spariti dagli anni '90 (Yamori-Kurihara 2004, `fonti/prodotti/usdchf.md`, B1): la probabilità a priori che un ciclo settimanale su USD/CHF sia stabile è bassa. Il test che distingue un vantaggio vero da uno trovato per caso è se il risultato regge spostando di qualche ora ingresso e uscita e togliendo mesi e pattern.
2. **Costi che il backtest non vede.** Lo short tiene la posizione la notte del mercoledì (finanziamento triplo) e quella del giovedì: quattro giorni di finanziamento a trade. Chi è short USD/CHF paga la differenza tra tasso del dollaro e del franco più lo 0,8% annuo di IG: con circa il 4% di differenza oggi, sono circa 1 franco al giorno per contratto mini, 4 franchi a trade, circa il 5% della perdita a stop. Lo spread (circa 2 pip) aggiunge altri 2 franchi. Nel 2016-2021 la differenza era più piccola; dal 2022 è salita. Su un sistema dal guadagno sottile questo può bastare a spiegare un reale peggiore del backtest.
3. **Formula della taglia.** `StopLossEURShort` è in franchi, non in euro (prezzo × 10.000 × stop), mentre il capitale di 6.000 è in euro: con EUR/CHF a 0,93 l'errore è del 7%, piccolo. Il rischio sui profitti moltiplicato per 6 e il fattore 1,5 fanno crescere la posizione molto in fretta appena il sistema guadagna: la curva in franchi dell'originale dipende soprattutto dal reinvestimento e non dice quanto vale il vantaggio. I test usano rischio fisso per trade (console standard, `Aggressivita = 0`).
4. **Il rischio allo stop non è costante nel tempo.** Lo stop è fisso all'1% del prezzo, mentre la volatilità di USD/CHF è cambiata molto (2011, 2015, 2020, 2022, aprile 2025). Con un'uscita a tempo la perdita dipende dalla volatilità del periodo (V3 di `idee/idee-di-trading.md`).

## Tipo di vantaggio

**Calendario**, secondo i principi trasversali di `idee/idee-di-trading.md`: posizione fissa nella settimana, uscita a tempo, stop lontano. È la stessa finestra dello short di 128 BIAS HOUR su AUD/JPY (giovedì 12:00 – venerdì 17:00, V1), che vende un cambio di rischio contro una valuta rifugio: qui si compra il franco, l'altra valuta rifugio (Ranaldo-Söderlind 2010). L'ipotesi comune è che prima del fine settimana chi ha posizioni a rischio le riduca comprando le valute rifugio. Lo stesso short giovedì-venerdì guadagna anche su GBP/JPY (097 BRK, M6: profit factor 1,32 su 536 trade dal 2016, contro 1,6 su AUD/JPY), quindi sullo yen la finestra regge su due cambi. Sul franco non c'è ancora una misura indipendente da questo sistema, e su AUD/JPY la parte del lunedì della spiegazione è stata smentita (S2).

Conseguenze per le proposte:
- da una gamba di calendario non ci si aspetta che i filtri di trend aiutino (S1); i pattern vanno misurati togliendoli;
- su una posizione a tempo con stop lontano la taglia inversa alla volatilità ha ridotto il drawdown del 25% su AUD/JPY (V3): qui si ottiene mettendo lo stop in escursioni giornaliere medie con rischio fisso in franchi;
- l'ora d'ingresso decide quante notti di finanziamento si pagano: entrare dopo le 23:00 del mercoledì ne evita tre su quattro.
