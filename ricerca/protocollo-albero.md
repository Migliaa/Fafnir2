# Protocollo di ricerca in profondità (albero)

Scritto il 2026-11-22. Fonti e ragionamenti in `fonti/paper/ricerca-in-profondita.md` (attendibilità dichiarata riga per riga: molti practitioner letti solo da sintesi). Qui le decisioni.

## Perché un albero e non 10.000 sistemi

Andrea ha indicato tre sistemi del primo esperimento DAX con curve belle e guadagno medio piccolo (4,4 €, 5,1 € e circa 2 € a trade). Per portarli sopra 20 € servono ingressi più selettivi, uscite diverse o condizioni di volatilità: è lavoro in profondità su una radice, non nuove radici. Il rischio è noto: con circa 1.700 trade e una dispersione di circa 100 € a trade, il migliore di 20 filtri che tengono un quarto dei trade guadagna circa 8 € in più **a puro caso**, il migliore di 1.000 circa 13 € (sezione 7 delle fonti). Il guadagno medio di un ramo quindi non basta mai come prova: ogni passo va confrontato con filtri casuali e contato nel registro.

## Una correzione prima di tutto: euro di oggi

L'escursione giornaliera del DAX in punti cambia molto da un anno all'altro (nella scoperta da 115 punti nel 2017 a 295 nel 2020 e nel 2022, 190 nel 2023). Il guadagno medio in euro calcolato sull'intero periodo mescola trade da 115 punti di escursione e trade da 300, e non dice quello che il sistema farebbe oggi. Il motore misura già tutto in escursioni medie; il filtro dei 20 € va applicato al **guadagno medio in escursioni moltiplicato per l'escursione media in punti dell'ultimo anno della scoperta** (2023), e si mostra accanto a quello storico. È un cambio di unità, non una scelta sul passato.

## Livelli

| Livello | Cosa si fa | Passa al livello dopo se | Prove |
|---|---|---|---|
| L0 ampiezza | logiche semplici su molti prodotti, come oggi | porte di L0 (sotto, "Porte come funzioni"): o è già **pronto** (guadagno sufficiente per la sua durata) e salta a L3, o ha **margine** per essere approfondito; in entrambi i casi la mediana fuori campione della CPCV è positiva; al massimo 10 radici per esperimento | migliaia |
| L1 radice | stessa regola senza filtri su prodotto gemello e speculare; dispersione per trade; **strato differenziale** (sotto) | il vantaggio c'è sul gemello (stesso segno), in entrambe le metà del periodo, e il segnale differenziale è positivo | 2-3 |
| L2 ingressi | 1 o 2 condizioni da un elenco di ipotesi con meccanismo scritto prima, 2-3 soglie tonde ciascuna, direzione dichiarata | batte almeno il 95% di 1.000 filtri casuali che tolgono la stessa quota di trade; restano ≥ 12 trade l'anno e ≥ 100 in tutto; migliora in almeno 2 terzi su 3 del periodo; le soglie vicine danno risultati simili; il filtro va nella direzione dichiarata | 30-100 |
| L3 uscite | orario o durata, stop e target in escursioni, scelti guardando escursione massima a favore e contro dei trade (MAE/MFE), non il massimo del backtest | utile/drawdown migliore del genitore, spread della fascia d'uscita incluso | 8-15 |
| L4 verifica | nessuna ricerca: gemello, Monte Carlo a blocchi, costi doppi, DSR e PBO sull'albero intero, poi la prova finale una volta per albero | filtri di Andrea (20/30/50 € per durata, 12 trade l'anno, curva regolare) e fuori campione convincente | 0 |

Ogni nodo confronta sé stesso con il **genitore**, stessi costi e stessa taglia: un figlio vale se migliora il padre più di quanto farebbe il caso. Lo strato differenziale si ricalcola a ogni livello: una condizione che alza il guadagno solo scegliendo i giorni in cui il DAX sale comunque non passa.

## Strato differenziale: il segnale meno l'andamento del sottostante

Richiesta di Andrea (2026-11-22): come un amplificatore differenziale, sottrarre al sistema l'andamento del prodotto, perché un long sul DAX guadagna anche solo perché il DAX nel lungo periodo sale. Se la differenza è positiva, il vantaggio è del sistema.

**Normalizzazione.** Le due grandezze si rendono confrontabili in due passi, già disponibili nel motore:
1. *per volatilità*: ogni rendimento, del sistema e del sottostante, è diviso per l'escursione media giornaliera del giorno d'ingresso (unità "escursioni"), così il 2011 a 150 punti e il 2023 a 300 pesano uguale;
2. *per esposizione*: il sottostante si misura sugli stessi intervalli di tempo in cui il sistema è in posizione, con lo stesso lato. Si confrontano trade con trade, non una curva di 13 anni con un'altra.

**Tre riferimenti, dal più grezzo al più fine** (ognuno toglie una spiegazione alternativa):

| Differenza | Riferimento sottratto | Spiega via |
|---|---|---|
| D1 deriva | il rendimento medio del sottostante per ora di esposizione, sull'intero periodo, moltiplicato per la durata del trade | "il DAX sale sempre" |
| D2 orario | la stessa finestra (stessi giorni della settimana, stesso orario d'ingresso e d'uscita) in tutti i giorni, senza le condizioni | "a quell'ora il DAX sale di suo" |
| D3 selezione | 1.000 sottoinsiemi casuali della finestra con lo stesso numero di trade | "ho scelto i giorni giusti per caso" |

Il segnale isolato è la differenza per trade, in escursioni, con il suo t (errore standard dalle differenze trade per trade). In alternativa, equivalente e utile come controllo, la regressione dei rendimenti giornalieri del sistema su quelli del sottostante nei giorni in posizione: la pendenza misura quanto il sistema è "DAX travestito", l'intercetta è il segnale (come l'alfa contro il mercato).

**Porta**: D2 > 0 con t ≥ 2 e D2 almeno metà del guadagno lordo del sistema (se più di metà viene dall'orario o dalla deriva, il sistema è il sottostante con un orologio). D1 e D3 si mostrano sempre; D3 coincide con il test contro i filtri casuali di L2. Un sistema senza condizioni (solo orario) coincide con la propria finestra e ha D2 = 0 per costruzione: in quel caso la stessa porta si applica a D1, perché l'unica spiegazione alternativa da togliere è la deriva.

Esempio sul primo esperimento (numeri già misurati): c02, giorno in rialzo 17:00 → 17:30, lordo +0,018 escursioni a trade; la stessa mezz'ora in tutti i giorni +0,009; D2 ≈ +0,009, cioè metà del lordo: sul filo della porta. Lo short speculare nei giorni in ribasso dà zero: il segnale c'è solo dal lato long, e lo strato lo rende visibile.

Nel cruscotto: nella prima vista un settimo numero, "segnale isolato" (D2 in euro a trade e in % del lordo), e nella curva una seconda linea sottile con la curva del riferimento D2 sugli stessi trade, così la distanza tra le due linee è il vantaggio.

## Porte come funzioni di altre metriche

Le soglie fisse scartano sistemi buoni (Andrea: un sistema con meno di 40 trade l'anno ma più di 20 € a trade è ottimo, ed è spesso il più affidabile perché più semplice). Le porte diventano rapporti:
- **copertura del guadagno**: `G = guadagno medio a volatilità di oggi / guadagno richiesto per la sua durata` (20 € fino a 36 ore, 30 € fino a 72, 50 € oltre). G ≥ 1: **pronto**.
- **margine per approfondire**: un filtro toglie trade e non ne aggiunge, quindi il massimo a cui un ramo può arrivare tenendo 12 trade l'anno è l'utile annuo diviso 12. `M = utile annuo / (12 × guadagno richiesto)`. M ≥ 1,5: c'è margine (c01: 567 € l'anno / 12 = 47 € contro 20, M ≈ 2,4). M < 1: nessun filtro lo porterà alla soglia, si scarta anche se la curva è bella.
- **numero di trade sufficiente**: invece di un minimo fisso, quello che serve perché il guadagno medio non sia caso, `t = guadagno medio / dispersione × √n ≥ 2` (più alto con molte prove, tramite DSR). Un sistema che guadagna molto rispetto alla dispersione ne richiede pochi; il pavimento pratico resta circa 6 trade l'anno (frequenza minima per avere un sistema utile), e 12 per i rami.
- **semplicità**: ogni condizione o parametro in più alza la soglia del miglioramento richiesto sul genitore (una condizione: batte il 95% dei filtri casuali; due condizioni: il 99%). A parità di risultato vince il nodo con meno condizioni.
- **ordine delle radici**: per `G × R² × min(1, t/3)`, con il drawdown in euro accanto.

## In-sample e fuori campione nell'albero

Andrea (2026-11-22) ha spostato l'in-sample a **2014-2023**: il mercato cambia, un sistema può iniziare a funzionare dall'oggi al domani, e un fuori campione nel futuro conta più di uno nel passato. Il passato resta, con meno peso.

| Periodo | Ruolo nell'albero | Peso |
|---|---|---|
| 2014-2023 (scoperta) | tutta la ricerca, L0-L3; ogni nodo è giudicato sulla **parte fuori campione della CPCV**, non sul periodo intero | |
| prodotto gemello (anni della scoperta) | fuori campione "trasversale": in L1 sulla radice e in L4 sulla foglia | scarta |
| 2024 → maggio 2025 | prova finale, una volta per albero, solo sulle foglie che hanno passato tutto | decide: utile positivo e guadagno medio almeno metà di quello in-sample |
| 2011-2013 | insieme alla prova finale | scarta se il sistema chiude in perdita o se è disastroso |
| prima del 2011 (per il DAX 2008-2010) | insieme alla prova finale | scarta solo se è disastroso |
| da novembre 2025 su ProRealTime | il fuori campione di Andrea, sul sistema finale | |

**Disastroso**, misurato in escursioni medie per confrontare anni con volatilità diverse (costanti `DISASTRO` in `motore/giudizio.py`): drawdown oltre 1,5 volte quello in-sample (2011-2013) o oltre 2 volte (prima del 2011), oppure perdita media a trade oltre metà del guadagno medio in-sample (2011-2013) o oltre il guadagno medio in-sample intero (prima del 2011). Un periodo senza dati, come prima del 2010 per l'Euro Stoxx, non scarta.

**Dentro la scoperta: CPCV a ogni livello e walk-forward della procedura.**
- *CPCV* (10 blocchi annuali, 2 di prova, 45 combinazioni, già nel motore): a ogni livello la scelta tra fratelli (quale filtro, quale soglia, quale uscita) si fa sui blocchi di training e si misura sui blocchi di prova. Il nodo vincente porta con sé la distribuzione di questi risultati fuori campione, ed è quella che passa le porte (mediana positiva, 10° percentile sopra lo zero per i rami). È l'equivalente di molte finestre scorrevoli, ma usa ogni anno sia come training sia come prova.
- *Walk-forward della procedura* (finestre ancorate dal 2014, passo un anno, primo anno di prova 2017): per le foglie finali si rifà l'intero percorso dell'albero (scelta del filtro, della soglia e dell'uscita) usando solo gli anni precedenti, e si registra l'anno successivo. Concatenando questi anni si ottiene una curva tutta fuori campione **della procedura**, non del sistema già scelto: risponde alla domanda "se avessi fatto questa ricerca nel 2018, cosa avrei guadagnato nel 2019?". È l'analisi più costosa (un albero rifatto 9 volte) e si fa solo sulle foglie di L4. La sua efficienza (guadagno fuori campione / guadagno in-sample) deve essere almeno 0,5, regola da practitioner.
- La finestra scorrevole a lunghezza fissa (4 anni di ricerca, 1 di prova) si usa solo quando un parametro va davvero riottimizzato nel tempo; per regole fisse la CPCV usa meglio i 13 anni.

**Nel cruscotto** la curva della foglia mostra: holdout all'indietro, scoperta con gli anni del walk-forward evidenziati come fuori campione della procedura, holdout in avanti. Così in-sample e fuori campione si vedono a colpo d'occhio, e si distingue il fuori campione "della procedura" da quello "mai toccato".

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

Radici: c01 (giorno in rialzo, 17:00 → 21:55), c03 (rialzo ≥ 0,25 escursioni, → 21:55), c02 (→ 17:30). Ipotesi di L2, con il meccanismo, in `esperimenti/alberi/dax-momento-chiusura.json`:
1. **Giornata ampia** (escursione di oggi rispetto alla media): le coperture del gamma muovono di più quando il mercato si muove di più, e il guadagno in euro scala con l'escursione.
2. **Volatilità del periodo alta**: Baltussen et al. 2021 trovano l'effetto più forte nei giorni di gamma negativo.
3. **Scadenza delle opzioni** (terzo venerdì del mese): i flussi di copertura sono massimi.
4. **Conferma americana**: il DAX sale anche dall'apertura di Wall Street (15:30), quindi il movimento è globale e non locale.
5. **Fine mese e ribilanciamenti**: flussi di fine periodo documentati.

Le ipotesi 2 e 4 nel progetto usavano il VIX e l'S&P. Una strategia ProRealTime sul DAX non può leggere un altro strumento, quindi un sistema con quelle condizioni non sarebbe eseguibile: le due ipotesi sono misurate sullo stesso DAX, con l'escursione media di 20 giorni divisa per quella di 100 al posto del VIX e il movimento del DAX dalla barra delle 15:30 al posto dell'S&P. Nelle tre settimane l'anno in cui l'ora legale americana ed europea non coincidono Wall Street apre alle 14:30 italiane e la barra delle 15:30 è un'ora dopo l'apertura.

**Risultato (2026-11-22, 3 prove).** Le tre radici si fermano tutte al primo livello sul nuovo in-sample 2014-2023, e nessuna prova finale è stata consumata:

| Radice | € a trade (volatilità 2023) | Trade l'anno | Margine M | t | Motivo |
|---|---|---|---|---|---|
| c01 | 3,8 | 131 | 2,06 | 2,7 | sull'Euro Stoxx, stessa regola e stessi anni, perde (−0,016 escursioni a trade) |
| c03 | 3,8 | 80 | 1,29 | 2,1 | margine sotto 1,5: nessun filtro la porta a 20 € tenendo un trade al mese |
| c02 | 2,3 | 131 | 1,24 | 3,6 | margine sotto 1,5 |

Per c01 il guadagno a trade in euro di oggi (3,8 €) è più basso di quello storico sugli stessi anni (4,1 €): il sistema ha guadagnato soprattutto nel 2020 e nel 2022, quando l'escursione media era di 295 punti contro i 190 del 2023. Un collaudo con le porte allentate (gemello tolto, margine 1, non registrato) mostra che c01 non migliora comunque: nessuna delle 11 condizioni batte il 95% dei filtri casuali (la migliore, conferma americana ≥ 0,2, arriva al 93% e 7,4 € a trade).

## Nel software

- `motore/albero.py`: `python -m motore.albero controlla|lancia <file>`; risultati in `risultati/alberi/<nome>/albero.json`; un albero già lanciato non si rilancia (la prova finale si usa una volta). Test in `motore/test_albero.py`.
- Condizioni nuove in `motore/condizioni.py`, tradotte in ProRealCode da `motore/uscita.py`: `vol_relativa`, `dal_1530`, `terzo_venerdi`, `giorno_mese`.
- Prova finale a tre periodi e regola del disastroso: `motore/prova_finale.py`, `motore/giudizio.py`.
- Cruscotto: pagina **Alberi** con i rami (mini-curva, euro di oggi, G, trade l'anno, t, R², drawdown, segnale isolato, prima porta non superata; clic per tutte le porte) e le foglie verificate (curva quadrata con il riferimento D2 tratteggiato, anni del walk-forward, sette numeri).
- Limite dichiarato del walk-forward: la procedura rifatta anno per anno sceglie solo fra i nodi già valutati sul periodo intero; un ramo che l'albero non ha approfondito non entra nella scelta.
