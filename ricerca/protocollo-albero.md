# Protocollo di ricerca in profondità (albero)

Scritto il 2026-11-22. Fonti e ragionamenti in `fonti/paper/ricerca-in-profondita.md` (attendibilità dichiarata riga per riga: molti practitioner letti solo da sintesi). Qui le decisioni.

## Perché un albero e non 10.000 sistemi

Andrea ha indicato tre sistemi del primo esperimento DAX con curve belle e guadagno medio piccolo (4,4 €, 5,1 € e circa 2 € a trade). Per portarli sopra 20 € servono ingressi più selettivi, uscite diverse o condizioni di volatilità: è lavoro in profondità su una radice, non nuove radici. Il rischio è noto: con circa 1.700 trade e una dispersione di circa 100 € a trade, il migliore di 20 filtri che tengono un quarto dei trade guadagna circa 8 € in più **a puro caso**, il migliore di 1.000 circa 13 € (sezione 7 delle fonti). Il guadagno medio di un ramo quindi non basta mai come prova: ogni passo va confrontato con filtri casuali e contato nel registro.

## Una correzione prima di tutto: euro di oggi

Il DAX nel 2011 valeva circa 7.000 punti, oggi oltre 20.000, e l'escursione giornaliera in punti è cresciuta in proporzione. Il guadagno medio in euro calcolato su 2011-2023 mescola trade da 150 punti di escursione e trade da 300: sottostima quello che il sistema farebbe oggi. Il motore misura già tutto in escursioni medie; il filtro dei 20 € va applicato al **guadagno medio in escursioni moltiplicato per l'escursione media in punti dell'ultimo anno della scoperta** (2023), e si mostra accanto a quello storico. È un cambio di unità, non una scelta sul passato.

## Livelli

| Livello | Cosa si fa | Passa al livello dopo se | Prove |
|---|---|---|---|
| L0 ampiezza | logiche semplici su molti prodotti, come oggi | R² ≥ 0,85, anni positivi ≥ 70%, guadagno medio con t ≥ 2, lordo/costi ≥ 2, almeno 40 trade l'anno (serve margine da tagliare), guadagno medio a volatilità di oggi ≥ 5 €; al massimo 10 radici per esperimento, scelte in ordine di R² | migliaia |
| L1 radice | stessa regola senza filtri su prodotto gemello e speculare; dispersione per trade | il vantaggio c'è sul gemello (stesso segno) e in entrambe le metà del periodo | 2-3 |
| L2 ingressi | 1 o 2 condizioni da un elenco di ipotesi con meccanismo scritto prima, 2-3 soglie tonde ciascuna, direzione dichiarata | batte almeno il 95% di 1.000 filtri casuali che tolgono la stessa quota di trade; restano ≥ 12 trade l'anno e ≥ 100 in tutto; migliora in almeno 2 terzi su 3 del periodo; le soglie vicine danno risultati simili; il filtro va nella direzione dichiarata | 30-100 |
| L3 uscite | orario o durata, stop e target in escursioni, scelti guardando escursione massima a favore e contro dei trade (MAE/MFE), non il massimo del backtest | utile/drawdown migliore del genitore, spread della fascia d'uscita incluso | 8-15 |
| L4 verifica | nessuna ricerca: gemello, Monte Carlo a blocchi, costi doppi, DSR e PBO sull'albero intero, poi la prova finale una volta per albero | filtri di Andrea (20/30/50 € per durata, 12 trade l'anno, curva regolare) e fuori campione convincente | 0 |

Ogni nodo confronta sé stesso con il **genitore**, stessi costi e stessa taglia: un figlio vale se migliora il padre più di quanto farebbe il caso.

## Conto delle prove

- Un registro per albero: ogni nodo lanciato è una prova, anche se scartato subito, con il riferimento al genitore.
- DSR e PBO di una foglia si calcolano su tutte le prove dell'albero più la famiglia di L0 da cui viene la radice.
- Budget per albero fissato prima (indicativamente 150-200 prove). Finito il budget, il ramo si ferma.
- Prodotto gemello e prova finale si usano una volta per albero, non per ramo: guardati per più rami diventerebbero campione.

## Dove entra la logica

- **Prima del lancio** (io, in sessione): per ogni radice scrivo l'elenco delle ipotesi di L2 con il meccanismo in una riga e la direzione attesa. Le prendo da quello che sappiamo (`idee/idee-di-trading.md`, `moduli/lezioni.md`, i tratti dei sistemi eccellenti, le fonti accademiche) e non dalla curva.
- **Durante** (il software, da solo, anche per ore): esegue i livelli, applica le porte, usa il backtest al minuto dal livello L2 in poi.
- **Dopo** (io): commento sulle foglie che superano L4, con cosa preoccupa e cosa verificare su ProRealTime.

## Il primo albero: momento verso la chiusura del DAX

Radici: c01 (giorno in rialzo, 17:00 → 21:55), c03 (rialzo ≥ 0,25 escursioni, → 21:55), c02 (→ 17:30). Ipotesi di L2, con il meccanismo:
1. **Volatilità del giorno alta** (escursione di oggi rispetto alla media): le coperture del gamma muovono di più quando il mercato si muove di più, e il guadagno in euro scala con l'escursione.
2. **Volatilità implicita alta** (VIX, che abbiamo nei dati, come approssimazione dei giorni di gamma negativo): Baltussen et al. 2021 trovano l'effetto più forte proprio lì.
3. **Scadenza delle opzioni** (terzo venerdì del mese): i flussi di copertura sono massimi.
4. **Conferma americana**: l'S&P dall'apertura delle 15:30 va nella stessa direzione del DAX alle 17:00, quindi il movimento è globale e non locale.
5. **Fine mese e ribilanciamenti**: flussi di fine periodo documentati.

Le ipotesi 2 e 4 richiedono condizioni su un secondo prodotto: è una funzione nuova del motore.

## Cosa serve nel software

1. Euro a volatilità di oggi nelle misure e nei filtri.
2. Condizioni su un secondo prodotto (VIX, S&P) allineate per orario.
3. Test contro filtri casuali (permutazione) e confronto con il genitore.
4. File d'esperimento di tipo `albero`: radici, elenco di ipotesi per livello, budget; esecuzione dei livelli in sequenza con le porte.
5. Pagina **Albero** nel cruscotto: radice e rami con mini-curva, guadagno medio, trade l'anno e porta superata o no a ogni passo, così si vede cosa ha cambiato ogni aggiunta.
