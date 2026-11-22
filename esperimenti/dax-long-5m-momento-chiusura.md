# DAX long a 5 minuti: momento verso la chiusura Xetra

Lanciato il 2026-11-22; file `dax-long-5m-momento-chiusura.json`, risultati in `risultati/esperimenti/dax-long-5m-momento-chiusura/`.

**Ipotesi** (scritta prima del lancio): se alle 17:00 il DAX è sopra la chiusura di ieri, sale ancora fino alla chiusura dell'asta delle 17:30, perché chi ha venduto opzioni copre il gamma nella direzione della giornata (Gao et al. 2018; Baltussen et al. 2021, studio accademico, DAX compreso). Prove: 12 varianti per lato (soglia 0 / 0,25 / 0,5 / 0,75 escursioni × uscita 17:30 / 17:40 / 21:55) più lo specchio short, 24 in tutto su un budget di 332. Prima del lancio avevo già visto la mappa oraria del DAX a 30 minuti, dove i long serali del lunedì e del giovedì dalle 17:00 erano in cima: l'ipotesi non è nata da lì, ma l'orario non era del tutto all'oscuro.

**Risultati** (2011-2023, netto dei costi IG, in escursioni giornaliere medie per trade):

| Variante | Trade | Media | Profit factor | Sharpe annuo | Anni positivi | 2019-2023 |
|---|---|---|---|---|---|---|
| giorno in rialzo, 17:00 → 21:55 | 1.676 | +0,024 | 1,29 | 1,01 | 10 su 13 | +0,015 |
| giorno in rialzo, 17:00 → 17:30 | 1.676 | +0,010 | 1,25 | 0,92 | 10 su 13 | +0,006 |
| rialzo ≥ 0,75, 17:00 → 17:30 | 321 | +0,019 | 1,43 | 0,68 | 10 su 13 | +0,027 |
| tutti i giorni, 17:00 → 17:30 (controllo, fuori griglia) | 3.232 | +0,001 | 1,02 | 0,12 | 8 su 13 | +0,002 |
| giorno in ribasso, 17:00 → 17:30 (controllo, fuori griglia) | 1.556 | −0,009 | 0,86 | −0,60 | 4 su 13 | −0,003 |

- Il vantaggio dipende dalla condizione: senza, la mezz'ora rende zero; nei giorni in ribasso il long perde. Lo short specchiato (giorni in ribasso) al lordo è zero e al netto perde: l'effetto c'è solo dal lato long, coerente con la direzione dichiarata ma non con la simmetria del meccanismo.
- Uscire alle 17:40 invece delle 17:30 dimezza o annulla il risultato: dopo l'asta il prezzo torna indietro.
- Lo spread IG (1,2 punti) costa circa 0,008 escursioni a trade, cioè quasi metà del lordo della variante a 30 minuti: con costi doppi quella variante va a zero, quella fino alle 21:55 resta positiva.
- Validazione: DSR 0,99 (prove effettive circa 3), CPCV positiva nell'82% delle combinazioni, ma PBO 0,37 sopra la soglia di 0,2, quindi per le regole del software nessuna variante passa. Il PBO alto qui viene dal fatto che le 12 varianti sono quasi uguali fra loro (scegliere la migliore conta poco), non da varianti che perdono; resta comunque un no.
- Curva: 86% dei giorni sotto il massimo precedente, il drawdown più lungo dura 573 giorni di borsa, Sharpe su 12 mesi mobili fra −2,0 e +1,0 di mediana; dal 2020 le curve si appiattiscono.

**Esito**: vantaggio piccolo e dipendente dal costo, che non passa la soglia del PBO. Il passo successivo sensato è la verifica di Andrea su ProRealTime della variante fino alle 21:55, l'unica che regge i costi doppi, oppure aggiungere il filtro dei giorni di gamma negativo indicato da Baltussen (effetto più forte), che però richiede un dato sulle opzioni che non abbiamo.
