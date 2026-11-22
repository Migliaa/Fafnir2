# Progetto trading system (ProRealTime / IG)

Tavolo di lavoro per migliorare i sistemi automatici di Andrea su ProRealTime. Ogni sessione può partire da zero: tutto quello che serve sta in questa cartella.

**Da leggere all'inizio di ogni sessione, in quest'ordine:**
1. `metodo.md`: come si lavora con Andrea, cosa valuta, contesto del conto.
2. `moduli/lezioni.md`: cosa hanno insegnato i test, errori da non ripetere.
3. `moduli/README.md`: moduli già validati, da riusare prima di scriverne di nuovi.
4. `idee/idee-di-trading.md`: principi trasversali (che tipo di vantaggio ha una gamba e quali moduli servono di conseguenza) e logiche di mercato estratte dai sistemi, con grado di prova (validate, da misurare, smentite). Quando un nuovo sistema funziona o un test conferma o smentisce una logica, aggiornalo.
5. `fonti/prorealtime/sintassi-verificata.md` e `fonti/paper/schede.md` prima di cercare online; le fonti nuove vanno aggiunte lì.
6. **Fafnir2** (il software di ricerca di sistemi nuovi in `motore/` e `cruscotto/`): `ricerca/fafnir2.md` dice cosa fa, come si lancia una ricerca o una campagna, dove leggere i risultati senza aprire i dati e cosa manca. Leggerlo prima di qualunque ricerca di sistemi nuovi.

**Quando Andrea incolla un codice nuovo** (di solito con "hai 5 tentativi"), senza aspettare altre istruzioni:
1. salva `sistemi/<nome>/originale.txt` e scrivi `analisi.md` (cosa fa, problemi, che tipo di vantaggio ha ogni gamba secondo i principi trasversali di `idee/idee-di-trading.md`);
2. fai la ricerca online sul prodotto e sui paper e salvala in `fonti/prodotti/<prodotto>.md`, con le ipotesi e la direzione attesa;
3. scrivi la prima tornata di moduli indipendenti in `proposte/`, con l'intestazione standard, e un `registro-test.md` vuoto;
4. nel messaggio: problemi trovati, tabella dei moduli, quale riferimento lanciare per ciascuno, cosa serve da Andrea.
Ai suoi screenshot: numeri nel registro subito, confronto con il riferimento giusto (anche se Andrea ha confrontato con l'originale), versione combinata con i promossi, tornata successiva sopra quella. A fine sistema: definitivo per il reale e aggiornamento di idee, lezioni e README (`metodo.md`, passi 6 e 7).

Struttura delle cartelle in `README.md`. Sistemi già lavorati: `sistemi/*/analisi.md` e `registro-test.md`.

## Regole

- **Dati a 1 minuto (`Dati/`): mai guardare l'ultimo anno prima di oggi.** È il fuori campione di Andrea, che lo verifica su ProRealTime con i dati IG (oggi fino a novembre 2026): niente dal 21 novembre 2025 in poi, né prezzi, né statistiche, né grafici. I dati attuali finiscono il 30 maggio 2025 e si usano tutti; se ne arrivano di più recenti, il lettore `motore/dati` li taglia alla data `TAGLIO` (da spostare solo su indicazione di Andrea). Per l'inventario di file nuovi si usano solo i metadati della colonna delle date. Progetto del software in `ricerca/progetto-software.md`.

- Su un sistema nuovo, librerie, lezioni e idee dei sistemi precedenti sono ipotesi da ritestare, non impostazioni: si parte dall'analisi del codice e dalla ricerca sul prodotto (`metodo.md`, passi 2 e 2b), e un modulo già validato entra solo come tentativo con interruttore.
- Prima delle proposte si fa la ricerca sul prodotto e la si salva in `fonti/prodotti/<prodotto>.md`, indicando per ogni informazione il tipo di fonte.

- Un nuovo codice di Andrea va in `sistemi/<nome-sistema>/originale.txt` e non si modifica mai.
- Le proposte sono codice ProRealCode completo, una per file in `proposte/`, numerate di seguito (M1, M2…), con un interruttore `UsaMx` che con 0 riproduce l'originale.
- Ogni codice, proposte e versioni, ha in cima la console di gestione di `moduli/console-rischio-per-trade.txt` (dal 2026-11-21): capitale versato, profitti precedenti, % di capitale persa allo stop per lato, manopola `Aggressivita` del reinvestimento. Nelle proposte `Aggressivita = 0` (stesso rischio in euro per ogni trade). I sistemi già in produzione con `moduli/intestazione-capitale.txt` restano così finché Andrea non chiede di cambiarli.
- Nel messaggio a Andrea va detto contro cosa confrontare: il riferimento (stesso file con `UsaMx = 0`), mai l'originale con un'altra taglia. I file da incollare vanno mandati come allegati: Andrea non vede i percorsi.
- Ogni proposta dice nel messaggio quale riferimento lanciare: di solito lo stesso file con `UsaMx = 0`. Andrea altrimenti confronta con l'originale a 1 contratto.
- Non si vede la curva dei rendimenti prima dei test: niente parametri ottimizzati a tavolino, solo valori tondi da provare in 2-3 varianti.
- I risultati dei test (dagli screenshot di Andrea) vanno subito in `registro-test.md`, con i numeri e l'interpretazione.
- Un modulo entra in `moduli/` solo dopo che Andrea riporta un miglioramento. La combinazione dei moduli promossi va in `sistemi/<sistema>/versioni/`; la versione per il reale non ha righe `GRAPH` e ha i parametri del capitale in testa.
- `StrategyProfit` è nella valuta dello strumento (yen sui cross in yen): capitale e profitto vanno sempre nella stessa valuta.
- Un modulo che aggiunge esposizione si confronta con l'originale ingrandito dello stesso guadagno, non con l'originale.
- Testi in italiano, secondo le preferenze di scrittura di Andrea (brevi, senza frasi di raccordo, numeri di attendibilità diversa mai affiancati senza dirlo).
