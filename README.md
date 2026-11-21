# Trading system ProRealTime

```
CLAUDE.md                    istruzioni per ogni nuova sessione
metodo.md                    come si lavora: ciclo, criteri di Andrea, contesto del conto
sistemi/<nome-sistema>/      un sistema per cartella
   originale.txt             codice fornito da Andrea, mai modificato
   analisi.md                cosa fa, problemi trovati, risultati per tornata
   proposte/                 varianti da testare, una per file, codice completo
   versioni/                 combinazioni dei moduli promossi; DEFINITIVO-produzione = in reale
   registro-test.md          risultati dei backtest e decisioni
fonti/prorealtime/           sintassi ProRealCode verificata e note sul report / conto IG
fonti/paper/                 schede dei paper usati
fonti/prodotti/              ricerca su ogni strumento (flussi, legami, calendario, costi), da riusare
idee/idee-di-trading.md      principi trasversali e logiche di mercato dei sistemi, con grado di prova
ricerca/                     ricerca di sistemi nuovi e diversificazione: cosa distingue gli eccellenti,
                             librerie di pattern, piano dei cantieri (dal 2026-11-21)
moduli/                      modifiche che hanno funzionato, riusabili su altri sistemi
moduli/intestazione-capitale.txt   intestazione standard da mettere in cima a ogni codice
moduli/lezioni.md            cosa hanno insegnato i test, anche quelli falliti
```

| Sistema | Stato |
|---|---|
| [128 BIAS HOUR – AUDJPY 1H](sistemi/128-bias-hour-audjpy-1h/analisi.md) | in produzione: originale + M4 + M6 + M8 + M10 (novembre 2026) |
| [165 DAX 30m](sistemi/165-dax-30m/analisi.md) | in produzione: originale + M5 + M8 + M9 + M10 + M11, con intestazione standard (novembre 2026) |
| [097 BRK IN – GBP/JPY 30m, long](sistemi/097-brk-in-gbpjpy-30m/analisi.md) | M1–M4 senza moduli adottati; M5 (short 01:00-10:30 migliore dell'originale) e M6 (ciclo settimanale confermato) valutati; da lanciare M7 (short giovedì sera-venerdì) e M8 (long lunedì-mercoledì), poi il sistema finale (novembre 2026) |
| [185 TOP UA 342 – oro 1H](sistemi/185-top-ua-342-gc-1h/analisi.md) | in produzione: logica dell'originale con intestazione standard a rischio allo stop, manopola `Aggressivita` e target dello short esplicito; 12 moduli provati, nessuno promosso (novembre 2026) |
| [3251 ORAF FDAX – DAX 5m, short](sistemi/3251-oraf-fdax-5m/analisi.md) | pronto per il reale: originale con la vendita alle 15:00 (M2) e console a rischio per trade (9,5%, Aggressivita 1,5); 8 moduli provati (novembre 2026) |
| [185 TOP UA 342 – Nasdaq 100 1H](sistemi/185-top-ua-342-nq-1h/analisi.md) | in produzione: originale con console a rischio per trade (6% long, 10% short), novembre 2026 |
| [128 BIAS USDCHF 1H, short mercoledì-venerdì](sistemi/128-bias-usdchf-1h/analisi.md) | M1 e M2 scartati (5,47 e 2,63 franchi a trade contro 26,72 dell'originale); da lanciare M3 (stessa logica negli altri giorni) e M4 (stessi trade: ingresso dopo il finanziamento triplo, uscita del venerdì, taglia a volatilità), novembre 2026 |
| [138 DAX LSD2H4 – DAX 1H, short del martedì](sistemi/138-dax-lsd2h4-1h/analisi.md) | pronto per il reale: C1 = originale + ingresso alle 09:00 (M2) con console a rischio per trade; 7 moduli provati, long scartato (novembre 2026) |
