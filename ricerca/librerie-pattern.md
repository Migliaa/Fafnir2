# Librerie di pattern e indicatori

Revisione del 2026-11-21 dei cinque file in `G:\My Drive\Andrea\ProRealTime\Pattern`: `001_MIG_Pattern_Estesi` (215 pattern nel selettore), `001_MIG_Indicatori_Estesi` (122), `001_MIG_Pattern_Speculari45` (45 coppie long/short), `004_DAN_PtnUNMR_DD155` e `_MF155` (155 ciascuno, uno con le funzioni giornaliere, l'altro con le barre del grafico).

## Errori

Da correggere prima di qualunque nuova ricerca, perché un pattern sempre falso o con il segno sbagliato è stato comunque provato e scartato (o scelto) in tutte le ottimizzazioni passate.

**001_MIG_Pattern_Estesi**
- `ptn191`, `193`, `195`, `197` sono sempre falsi: chiedono `Close < DOpen(0)` e insieme `DOpen(0) - Close <= DOpen(0) * (-x)/100`, cioè una differenza positiva minore di un numero negativo. Va scritto `DOpen(0) - Close >= DOpen(0) * x/100`.
- `ptn199`, `201`, `203`, `205` hanno il segno invertito: `DLow(1) - DLow(1)*(-x)/100` è il minimo di ieri **più** x%, quindi chiedono una chiusura sotto un livello sopra il minimo di ieri, non sotto il minimo.
- `ptn41` dice "corpo rosso più grande del 50% dell'escursione", ma `(open[1]-close[1]) < 0.5*(high[1]-low[1])` è vero per tutte le candele verdi e per le rosse piccole: va scritto `>`.
- `ptn98` dice 50% e il codice usa il 10%.
- `ptn53` e `ptn54` confrontano la candela di ieri con `Range`, che è l'escursione della barra corrente.
- `ptn39`, `40`, `79`, `80` (`highest[5](Dclose(1))`) su un grafico orario prendono la chiusura di ieri ripetuta nelle ultime 5 o 20 barre, non il massimo delle ultime 5 o 20 chiusure giornaliere: il significato cambia con il timeframe.
- In generale gli indici `[1]`, `[2]` sono barre del grafico: su 1 ora "high[1]" è l'ora precedente, mentre i commenti parlano di ieri. La libreria va usata o solo sul giornaliero o riscritta con le funzioni `D...`, come fa la coppia DD/MF di DAN.
- `ptn216`-`219` sono definiti ma non sono nel selettore (si ferma a 215).

**001_MIG_Indicatori_Estesi**
- `MediaAVGTR14 = Average[3650](...)` è commentata "ultimi 10 anni", ma sono 3.650 barre: su 1 ora circa cinque mesi. Obbliga anche a caricare 3.650 barre prima del primo trade.
- Tutti i 122 indicatori, comprese le quattro chiamate `CALL` a indicatori esterni, si calcolano a ogni barra qualunque sia `patternID`: ogni lancio dell'ottimizzazione paga il calcolo di tutta la libreria. Le `CALL` sono la parte più lenta; Bollinger e Donchian si scrivono in due righe dentro il codice.
- I commenti di `iptn23` e `iptn24` sono invertiti (MACD sopra zero è tendenza al rialzo).

**004_DAN_PtnUNMR (DD e MF)**
- `uptn011`-`024` confrontano il corpo di 5 giorni con `highd5 - lowd1`, il massimo di 5 giorni fa meno il minimo di ieri, che è negativo quando il prezzo è salito: la stessa soglia vuol dire cose diverse a seconda della direzione. Probabilmente doveva essere `range5d`.
- `uptn132` divide la somma di due escursioni per 3: confronta l'escursione di ieri con due terzi della media, probabilmente doveva essere `/2`.

## Il problema di fondo: scale di soglie contate come pattern diversi

I 155 pattern di DAN sono circa 23 grandezze, ognuna con 2-16 soglie: rapporto corpo/escursione di ieri (8 soglie), corpo di 5 giorni (22), salita dall'apertura rispetto a ieri (9), discesa dall'apertura (7), escursione di oggi in % (14), variazione di ieri in % (10), massimo di oggi rispetto a ieri in % (12), minimo di oggi rispetto a ieri in % (11), gap in % (11), chiusura di oggi rispetto all'apertura in % (10), e così via. Lo stesso vale per circa 90 dei 215 pattern estesi.

Conseguenze:
- l'ottimizzazione su `patternID` è in parte l'ottimizzazione di una soglia continua travestita da scelta tra pattern, e ogni soglia conta come una prova in più: con 155 pattern per ciascuno dei quattro posti (sì/no, long/short) il migliore trovato è migliore per caso con alta probabilità (Bailey, López de Prado 2014; Sullivan, Timmermann, White 2001 in `fonti/paper/schede.md`);
- non si vede se la soglia scelta sta in una zona stabile, perché le soglie vicine sono pattern con un altro numero;
- le soglie in % non si trasferiscono tra prodotti né tra decenni (tratto 5 di `cosa-distingue-i-sistemi.md`).

## Come ricostruirle

Una libreria nuova, con lo stesso uso dentro ProRealTime (una variabile che sceglie il pattern), ma costruita così:

1. **Una famiglia = una domanda sul mercato**, con la soglia come seconda variabile decimale da ottimizzare: per esempio `Famiglia = 7` (gap d'apertura) e `Soglia = 0.5` vuol dire apertura di oggi sopra la chiusura di ieri di almeno 0,5 escursioni giornaliere medie. Con 12-15 famiglie e 6-8 soglie le combinazioni restano sotto le 120 per posto, e la stabilità si vede guardando le soglie vicine.
2. **Soglie in escursioni medie** (giornaliere per le grandezze giornaliere, orarie per quelle intraday), mai in % o in punti.
3. **Lato speculare automatico**, come in `Speculari45`: il long usa la condizione, lo short la sua immagine riflessa, con la stessa soglia. Una scelta in meno per ogni lato.
4. **Funzioni giornaliere esplicite** (`DHigh(1)`, `DClose(2)`) per tutto quello che riguarda i giorni, così il significato non cambia con il timeframe.
5. **Per ogni famiglia, la direzione attesa scritta prima** secondo il tipo di vantaggio della gamba (`idee/idee-di-trading.md`, principio 1): su una gamba di momento un filtro "ieri in forte calo" dovrebbe favorire lo short, su una di inversione il long. Un filtro che migliora il backtest nella direzione opposta a quella dichiarata va trattato come rumore finché un test su un altro prodotto non dice il contrario.
6. **Si calcola solo la famiglia scelta**, senza `CALL`.

Famiglie proposte, da completare con Andrea: posizione della chiusura di ieri nella sua escursione; corpo di ieri rispetto all'escursione; direzione delle ultime 1-4 chiusure; gap d'apertura; spostamento di oggi dall'apertura; massimo o minimo di oggi rispetto a ieri; giornata interna o esterna; escursione di ieri rispetto alla media (compressione); volatilità di 2 settimane rispetto a 5 mesi (regime, già in `moduli/filtro-regime-volatilita.txt`); distanza dalla media di 200 giorni; distanza dal massimo o minimo di 20 giorni; giorno del mese (fine mese).

**Regola d'uso**: un filtro entra in un sistema solo se le due soglie vicine danno lo stesso segno, se i trade scartati guadagnano in media meno di quelli tenuti di più dell'incertezza (`moduli/lezioni.md`, "Filtri e uscite"), e se il miglioramento c'è in entrambe le metà del periodo.
