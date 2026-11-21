# Libreria dei moduli validati

Qui finiscono solo i moduli che hanno migliorato almeno un sistema nei test, scritti in forma generica (blocco da incollare + variabili che si aspetta dal sistema ospite).

Per ogni modulo, un file `.txt` con in testa:

```
// MODULO: nome
// Validato su: sistema, periodo, risultato in una riga (vedi sistemi/<sistema>/registro-test.md)
// Richiede: variabili che il sistema deve definire (es. PsL, PsS)
// Produce:  variabili che il modulo definisce (es. FattoreRein)
```

| Modulo | Validato su | Quando usarlo |
|---|---|---|
| [console-rischio-per-trade.txt](console-rischio-per-trade.txt) | 185 NQ 1H (produzione) | sempre, dai sistemi nuovi: console standard (capitale versato, profitti precedenti, % persa allo stop per lato, manopola del reinvestimento) |
| [intestazione-capitale.txt](intestazione-capitale.txt) | 165 DAX 30m (M8) | intestazione precedente, ancora in uso su 165 DAX (leva costante, pesi long/short, freno) |
| [reinvestimento-frazione-fissa.txt](reinvestimento-frazione-fissa.txt) | 128 BIAS HOUR (M6) | sostituito dall'intestazione standard nei sistemi nuovi; resta in uso su 128 BIAS HOUR |
| [taglia-volatilita-uscita-a-tempo.txt](taglia-volatilita-uscita-a-tempo.txt) | 128 BIAS HOUR (M8, short) | posizioni che escono a tempo con stop lontano, non con stop stretto né se il guadagno per trade cresce con la volatilità |
| [freno-drawdown.txt](freno-drawdown.txt) | 128 BIAS HOUR (M10) | insieme al reinvestimento a frazione fissa |
| [reinvestimento-leva-sui-profitti.txt](reinvestimento-leva-sui-profitti.txt) | 185 NQ 1H (M9) | quando si vuole far crescere la posizione più in fretta con i profitti che con il capitale versato, con un tetto che scende a size grandi |
| [filtro-regime-volatilita.txt](filtro-regime-volatilita.txt) | 165 DAX 30m (M5, short) | gambe di momento intraday, il cui vantaggio cresce con la volatilità |

Esempio completo di tutti e tre insieme, con la gestione manuale del profitto dopo un riavvio: [DEFINITIVO-produzione.txt](../sistemi/128-bias-hour-audjpy-1h/versioni/DEFINITIVO-produzione.txt).
Esempio dell'intestazione standard in un sistema completo: [165 DAX, DEFINITIVO-produzione.txt](../sistemi/165-dax-30m/versioni/DEFINITIVO-produzione.txt).

Idee non adottate ma da riprovare su altri sistemi: aggiunta selettiva sui trade in guadagno ([M9](../sistemi/128-bias-hour-audjpy-1h/proposte/M9-aggiunta-selettiva.txt)), utile se i vincenti sono grandi rispetto allo spread.

Strumenti di backtest, che non cambiano i trade: [controllo-drawdown.txt](controllo-drawdown.txt), drawdown con il reinvestimento in percentuale o in euro, per tarare il rischio per trade (185 oro).

I candidati in prova stanno in `sistemi/<sistema>/proposte/`. Quello che si è imparato dai test, anche dai fallimenti, sta in [lezioni.md](lezioni.md).
