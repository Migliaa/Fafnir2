# Progetto del software di ricerca

Scritto il 2026-11-22. Sostituisce il passaggio da ProRealTime per la ricerca: ProRealTime resta solo per la verifica finale di Andrea, sui CFD IG e sul periodo che il software non vede. I cantieri di `piano.md` diventano parti del software (tabella in fondo).

## Dati

Cartella `Dati/1m-20261121T225950Z-1-001/1m/`: 42 futures continui a 1 minuto, un file parquet per anno, colonne `contract, ts (UTC), open, high, low, close, volume`, tutti fino al 30 maggio 2025.

| Gruppo | Simboli | Da |
|---|---|---|
| Indici USA | ES, NQ, YM, RTY | 2006-2010 |
| Indici europei | FDAX, FESX | 2008, 2010 |
| Tassi | TY, US, FGBL (Bund) | 2008-2010 |
| Valute contro dollaro | AD, BP, CD, EC, JY, SF, NE1 | 2008 (NE1 2013) |
| Metalli | GC, SI, PL, HG | 2008-2010 |
| Energia | CL, HO, RB, NG | 2010 |
| Agricoli | C, S, SM, BO, W, KW, CC, KC, SB, CT, OJ, RR | 2010 |
| Bestiame | FC, LC, LH | 2008 |
| Volatilità, cripto | VX, BTC, MBT | 2010, 2017, 2021 |

**Caratteristiche che decidono il progetto**
- **Prezzi rettificati ai rinnovi.** L'ES del 2015 ha il minimo a 2.270 contro circa 1.830 del prezzo reale, l'oro 1.606 contro circa 1.050: le differenze di prezzo sono giuste, i livelli no. Ne segue che nessuna grandezza va calcolata in percentuale del prezzo (sugli anni vecchi sarebbe sbagliata del 20-50%): tutto in punti o in escursioni medie, che è anche il tratto 5 dei sistemi eccellenti. Gli stop in % dei sistemi ProRealTime si ricavano alla fine, dal prezzo IG.
- **I cross si costruiscono.** AUDJPY = AD / JY, GBPJPY = BP / JY, EURJPY = EC / JY e così via. Con prezzi rettificati il rapporto è leggermente distorto; per le valute le rettifiche sono piccole, va misurato quanto, confrontando con le esportazioni a 15 minuti di Andrea dove ci sono (GBP/USD).
- **Orari.** I dati sono in UTC; tutto il software ragiona in ora italiana (`Europe/Rome`), come i sistemi di Andrea. L'FDAX ha barre dalle 08:00 alle 22:00 (nel 2015), mentre il Germany 40 di IG quota quasi 24 ore: le logiche notturne sul DAX si studiano su ES e FESX o si rimandano a ProRealTime.
- **Differenze con IG.** Futures e CFD differiscono per base, orari, spread e finanziamento; per questo il software usa costi prudenti e la verifica finale è comunque su ProRealTime.

## Il fuori campione di Andrea

Andrea verifica i sistemi trovati su ProRealTime, con i CFD IG, sull'ultimo anno prima di oggi (dal 21 novembre 2025): quel periodo non entra mai nel software. I futures attuali finiscono il 30 maggio 2025, quindi si usano tutti, e tra la fine dei dati e l'inizio del suo fuori campione restano sei mesi (giugno-novembre 2025) che vede solo ProRealTime.

- Il taglio è la costante `TAGLIO` in `motore/config.py`, applicata dal lettore già alla lettura dei file: le righe successive non arrivano mai in memoria, e `controlla_taglio` lo verifica su ogni serie. Si sposta solo su indicazione di Andrea.
- I cinque sistemi eccellenti sono stati scelti su backtest che arrivano a oggi, quindi per le loro logiche nemmeno l'ultimo anno è un fuori campione pulito; lo è per i sistemi nuovi.

### Schema in-sample / out-of-sample interno

Deciso il 2026-11-22 sulla ricerca in `fonti/paper/validazione-e-metriche.md` (sezione A10, con una modifica sulle date).

**Aggiornamento del 2026-11-22 sera, su richiesta di Andrea**: la scoperta è **2014-2023** (10 blocchi, 45 combinazioni della CPCV; con 10 anni 10.000 prove richiedono uno Sharpe di 1,36). 2011-2013 e prima del 2011 diventano fuori campione all'indietro con peso minore del 2024-2025: scartano solo se il sistema perde (2011-2013) o va in modo disastroso. La tabella sotto resta come storia della decisione; i periodi in uso sono in `motore/config.py` e in `ricerca/protocollo-albero.md`.

| Periodo | Ruolo | Come si usa |
|---|---|---|
| inizio dati → 2010 | holdout interno all'indietro | una volta sola, sui finalisti; contiene la crisi 2008 per i prodotti che partono dal 2006-2008, solo il 2010 per gli altri |
| 2011 → 2023 (13 anni) | scoperta e selezione | CPCV a blocchi annuali (13 blocchi, 2 di test, 78 combinazioni) con purging ed embargo; PBO per famiglia di varianti; DSR |
| 2024 → maggio 2025 (17 mesi) | holdout interno in avanti | una volta sola, insieme a quello all'indietro |
| giugno → novembre 2025 | non disponibile | |
| novembre 2025 → novembre 2026 | fuori campione di Andrea su ProRealTime | con l'intervallo atteso (5°-95° percentile di profitto e drawdown) fissato prima con il bootstrap stazionario |

- **Perché non in-sample 2019-2024 come proponeva Andrea.** Con 6 anni il numero di varianti che si possono provare senza trovare uno Sharpe buono per caso è minuscolo: per certificare uno Sharpe annuo di 0,7 la Minimum Backtest Length (Bailey et al. 2014) ammette circa 4 prove indipendenti con 6 anni e circa 24 con 13; per uno Sharpe di 1, circa 20 contro 660. In più il 2019-2024 è dominato da due regimi particolari (2020 e 2022). L'idea che conta della proposta resta: nella selezione si riporta a parte il sottoperiodo 2019-2023, e un candidato deve essere positivo anche lì, perché è il regime più vicino a oggi.
- **CPCV invece di un solo taglio.** La cross-validation combinatoria con purging (López de Prado 2018) dà una distribuzione degli Sharpe fuori campione invece di un numero solo, e contiene già tagli "all'indietro" e "in avanti". Il purging toglie dal training i trade che si sovrappongono al blocco di test; l'embargo è la durata massima del trade più la finestra degli indicatori.
- **Walk-forward** (4 anni in-sample, 1 anno out-of-sample, a finestra mobile) solo nella ricerca in verticale, quando un parametro va davvero riottimizzato nel tempo; si guarda la walk-forward efficiency (Sharpe out-of-sample / Sharpe in-sample ≥ 0,5, regola di practitioner) calcolata anche senza i 5 trade migliori.
- **Registro dei tentativi unico** per tutta la ricerca: ogni variante provata, anche scartata, con il numero di prove indipendenti stimato raggruppando le curve correlate. È il dato che serve a DSR, PBO e MinBTL; senza, nessuna delle tre vale.
- **Prova a vuoto**: periodicamente l'intera procedura gira su dati rimescolati a blocchi (stessa volatilità, nessun effetto d'orario). Se "trova" sistemi validati, le soglie sono troppo larghe.

## Le parti del software

```
motore/
  dati/          lettura con il taglio, ora italiana, barre 5m-15m-30m-1h-giorno, cross sintetici, sessioni
  catalogo/      scheda di ogni prodotto: orari, gruppo, prodotti gemelli, costi IG per fascia oraria, se IG lo quota
  condizioni/    la libreria a famiglie (cantiere 1): ogni famiglia è una funzione (barre, soglia) → vero/falso, con lo specchio per lo short
  modelli/       modelli di sistema parametrici: finestra di calendario (famiglia 128), spostamento dall'apertura tenuto per giorni (famiglia 185), orario con decisione e ingresso separati (3251)
  motori/
    mappa        rendimento medio per (giorno, ora d'ingresso, ora d'uscita), in escursioni medie, netto dei costi, anno per anno
    eventi       tabella degli eventi: per ogni ingresso possibile, le caratteristiche al momento della decisione e il percorso dopo (rendimento a vari orizzonti, massimo contro, massimo a favore)
    backtest     simulazione completa sulle barre da 1 minuto: stop, target, pareggio, uscite a tempo, un ordine alla volta come ProRealTime
  validazione/   statistiche e controlli contro il sovra-adattamento
  portafoglio/   unione delle liste dei trade, calendario dell'esposizione, drawdown comuni (cantiere 4)
  uscita/        traduzione in ProRealCode con la console e gli interruttori standard
  cli            comandi per l'IA: controlla e lancia un esperimento, riassunto JSON
cruscotto/       pagine HTML locali per Andrea: rapporto del mattino, elenco filtrabile dei candidati, schede e curve
esperimenti/     un file per ogni idea: ipotesi, meccanismo, fonte, direzione attesa, scritto prima di lanciare; i risultati si aggiungono sotto
risultati/       uscite degli esperimenti (fuori da git se pesanti): JSON per l'IA, curve e trade per il cruscotto
```

### Perché tre motori

La maggior parte delle domande non ha bisogno di un backtest completo: "quanto rende lo short del DAX dalle 15:00 alle 16:35 il giovedì dopo un calo dello 0,5 escursioni dal massimo" è una media su una tabella di eventi. La **mappa** e la **tabella degli eventi** si calcolano una volta per prodotto e poi rispondono in millisecondi a migliaia di varianti, compresi i filtri della libreria (un filtro è una selezione di righe). Il **backtest** completo, lento perché segue il percorso minuto per minuto, si usa solo quando entrano stop, target e pareggio, cioè per i candidati finali e per la taratura degli stop.

### Linguaggio

Python con polars e numpy per dati, mappe e tabelle degli eventi; numba 0.68 (installato, compila in codice macchina i cicli Python) per il backtest minuto per minuto e per i ricampionamenti delle statistiche. Rispetto al C la velocità è simile e il codice resta uno solo, senza compilatore da installare. Il PC ha un i7 a 12 thread e 24 GB: si lavora un prodotto alla volta e le barre aggregate restano in cache (`Dati/_cache`); le barre orarie del Nasdaq su 19 anni si costruiscono in meno di un secondo.

### Due modi di cercare

- **In ampiezza (prototipo)**: una logica codificata in forma leggera, con pochi parametri tondi, gira su tutti i 42 prodotti e i cross sintetici per vedere dove funziona. Serve per i trapianti, il setaccio e le idee dei paper.
- **In verticale**: un prodotto scelto per il portafoglio (per esempio un long sul DAX o qualcosa di scorrelato) e su quello si provano più logiche, la libreria di condizioni e le uscite, con le regole di validazione più severe perché le prove sono molte.

Il motore è lo stesso; cambia il file dell'esperimento, che dichiara il modo e quindi quanto severa è la correzione per il numero di prove.

### Chi usa il software

Il software lo usa l'IA; Andrea guarda i risultati. Il flusso:
1. Andrea propone in chat un'idea o una ricerca mirata ("long sul DAX", "questa logica su tutti i prodotti").
2. Insieme si precisa l'idea; l'IA scrive il file dell'esperimento (ipotesi, meccanismo, prodotti, griglia, modo in ampiezza o in verticale, budget di prove dalla MinBTL) e lo mette in coda.
3. Il PC lavora tutta la notte senza l'IA collegata.
4. Al mattino Andrea trova i **10 migliori sistemi già filtrati** dalle regole di validazione, ciascuno con la scheda, la curva e il codice ProRealCode pronto per la sua verifica.

Ne seguono due interfacce distinte.

**Interfaccia per l'IA** (`motore/cli` e file in `esperimenti/`), pensata per costare pochi token:
- comandi brevi: lancia o accoda un esperimento, stato della coda, riassunto di un esperimento, confronta candidati;
- ogni risultato esce in due forme: un riassunto compatto in JSON (poche righe di numeri, quello che l'IA legge) e i file completi per il cruscotto (curve, liste dei trade, tabelle), che l'IA non apre;
- le specifiche degli esperimenti sono file di testo validati dal software (campi obbligatori, budget di prove, date dello schema in-sample/out-of-sample fissate), così l'IA non può lanciare una ricerca che viola le regole di validazione o tocca il fuori campione.

**Coda notturna (fuori dal software, decisione di Andrea del 2026-11-22).** La coda e il rapporto del mattino si gestiscono a parte, in un modulo separato che chiama i comandi della `cli`; il software di ricerca non ne sa niente. Come era stata pensata: un programma esegue gli esperimenti in coda uno dopo l'altro, sfruttando i 12 thread, con salvataggi intermedi per riprendere dopo un'interruzione, il PC tenuto sveglio durante il lavoro e un registro degli errori. A fine coda scrive il **rapporto del mattino**: i 10 candidati migliori di tutta la notte, già passati dalle regole di selezione, ordinati secondo la scheda e con la sovrapposizione dei drawdown rispetto ai sistemi in produzione.

**Cruscotto per Andrea** (`cruscotto/`): pagine HTML locali generate dal software, che si aprono nel browser senza server e senza installare niente:
- il rapporto del mattino;
- un elenco di tutti i candidati di tutte le ricerche, filtrabile e ordinabile per prodotto, lato, tipo di vantaggio, esperimento, data e per ogni metrica della scheda;
- per ogni candidato la curva dei profitti (in-sample, holdout interni e Monte Carlo a bande), la scheda, la curva per anno e per regime, la lista dei trade, il confronto con i sistemi in produzione e il file ProRealCode da scaricare;
- un registro delle verifiche su ProRealTime, dove segnare l'esito del fuori campione di ogni candidato provato, che diventa un dato per tarare le soglie del software.

## Metriche oltre a quelle di ProRealTime

Formule e fonti in `fonti/paper/validazione-e-metriche.md`, parte B. ProRealTime non pubblica la formula dello z-score (lo staff lo dichiara sul forum) e calcola lo Sharpe dividendo il profitto del giorno per il numero di trade, solo sui giorni con trade e senza annualizzazione: nessuno dei due è confrontabile con le definizioni standard.

Ogni candidato esce dal software con una **scheda** fissa, in quest'ordine:
1. **Sharpe giornaliero** con i giorni senza posizione, annualizzato, e corretto per l'autocorrelazione dei rendimenti (Lo 2002); **DSR** con il numero di prove del registro.
2. **Distribuzione CPCV** (mediana, 10° percentile, % di percorsi con Sharpe positivo) e **PBO** della famiglia da cui viene.
3. **Regolarità della curva**: R² e K-ratio (Kestner 2003), **costanza della pendenza** (coefficiente di variazione delle pendenze anno per anno e quota di anni con pendenza positiva, misura chiesta da Andrea), Ulcer Index, tempo sott'acqua e durata massima del drawdown, % di trimestri positivi, Sharpe su finestre mobili di 12 mesi.
4. **Robustezza**: zona stabile dei parametri (mediana dei vicini ≥ 70% del valore scelto), **simmetria long/short** (stessa regola specchiata), profitto senza i 10 trade migliori, Sharpe con costi doppi, ingresso spostato di ±15 minuti, risultato per regime di volatilità e nel sottoperiodo 2019-2023.
5. **Z-score** di Wald-Wolfowitz sulle sequenze di vincenti e perdenti, con N, numero di sequenze e segno spiegato.
6. **Monte Carlo** del drawdown massimo e della serie di perdite (5°/50°/95° percentile), che diventano l'intervallo atteso per il fuori campione di Andrea. Le perdite reali arrivano a grappoli (stessi periodi agitati, stesso regime), quindi rimescolare i trade uno per uno sottostima il drawdown: si ricampionano **blocchi di giorni consecutivi** (bootstrap stazionario, Politis-Romano 1994) con lunghezza media scelta dall'autocorrelazione dei rendimenti e delle perdite del sistema, e in più si fa un ricampionamento **per regime** (blocchi presi dai periodi agitati e calmi nella proporzione storica). Il software confronta il drawdown del rimescolamento semplice con quello a blocchi: se il secondo è molto più grande, il sistema ha perdite raggruppate e la taglia va decisa sul secondo.
7. **Rispetto al portafoglio**: correlazione dei rendimenti giornalieri e di coda, **sovrapposizione dei drawdown** con ogni sistema in produzione (quota dei giorni in cui sono sott'acqua insieme, rispetto a quella attesa se fossero indipendenti), contributo marginale al Conditional Drawdown at Risk al 95%, effective number of bets del portafoglio con e senza il candidato.

Le metriche 1-4 servono alla selezione, la 5 e la 6 alla decisione, la 7 a scegliere che cosa aggiungere al portafoglio.

## Validazione: i concetti dei paper diventati regole del software

Ogni regola viene da un risultato già usato nel progetto (`fonti/paper/schede.md`, `moduli/lezioni.md`).

1. **Ipotesi scritta prima** (`metodo.md`, passo 2b). Il software non lancia un esperimento senza il file in `esperimenti/` con meccanismo, tipo di fonte e direzione attesa. Un risultato nella direzione opposta conta come rumore.
2. **Conteggio delle prove.** Ogni variante provata, anche scartata, finisce nel registro unico. La soglia per accettare un risultato cresce con il numero di prove: DSR sopra 0,95 (Bailey, López de Prado 2014), PBO di lavoro sotto 0,2 con obiettivo sotto 0,05 (Bailey et al. 2017), e per le famiglie di regole come le finestre orarie il test SPA di Hansen o lo stepdown di Romano-Wolf con bootstrap stazionario sull'intero gruppo provato (Sullivan, Timmermann, White 2001 per il problema). Prima di un esperimento si calcola quante varianti ammette la MinBTL; se sono troppe, si riduce la griglia.
3. **Probabilità di sovra-adattamento** sulle griglie di parametri: si divide la scoperta in blocchi, si sceglie il migliore su metà dei blocchi e si guarda dove si piazza sull'altra metà, per tutte le combinazioni di metà (Bailey et al. 2017). Se il migliore finisce spesso sotto la mediana, la griglia sta adattando il caso.
4. **Zone stabili.** Si tiene un parametro solo se i valori vicini danno risultati simili; il valore scelto è il centro della zona, non il massimo.
5. **Anni e regimi.** Il risultato va guardato per anno e per regime di volatilità; se dipende da due o tre anni, non è un vantaggio. È anche il test che distingue il tipo di vantaggio (principio 1 di `idee/idee-di-trading.md`).
6. **Prodotto gemello.** Un vantaggio con un meccanismo deve vedersi, più debole, sul prodotto che condivide il meccanismo (DAX ed Euro Stoxx, Nasdaq e S&P 500, AUDJPY e NZDJPY). Con 42 prodotti questa conferma è disponibile quasi sempre.
7. **Filtri**: un filtro vale se i trade scartati guadagnano meno dei tenuti di più dell'incertezza, stimata dalla dispersione dei trade (`moduli/lezioni.md`, "Filtri e uscite").
8. **Costi prudenti**: spread IG della fascia oraria più un margine; un vantaggio che sparisce raddoppiando i costi non va in produzione.
9. **Validazione interna una volta sola**: un'idea che fallisce sul periodo di verifica non si ritocca e si rilancia, si chiude e si scrive perché.

## La prima prova: ritrovare quello che sappiamo

Prima di cercare cose nuove, il software deve ritrovare da solo, su tutti i dati fino a maggio 2025, i vantaggi dei sistemi eccellenti: il ciclo settimanale di AUDJPY (da AD/JY), le due gambe di 165 DAX (FDAX), lo short di 3251 (FDAX), lo short di 185 NQ e le gambe di 185 oro. I numeri non saranno uguali a quelli di ProRealTime (futures invece di CFD, costi diversi, anni diversi), ma segno, ordine di grandezza del profit factor e forma della curva devono esserci. Se non ci sono, l'errore è nel software (orari, sessioni, costi), e va trovato prima di fidarsi di qualunque scoperta.

## Cantieri del piano dentro il software

| Cantiere di `piano.md` | Dove sta ora |
|---|---|
| 1. Librerie a famiglie | `condizioni/`, scritte una volta in Python; la traduzione in ProRealCode è automatica in `uscita/` |
| 2. Setaccio dei sistemi già scritti | i 128 BIAS e i 185 TOP UA sono `modelli/` con parametri: tutte le varianti del portafoglio 2025 si rilanciano senza pattern e sui prodotti gemelli, senza ProRealTime |
| 3. Trapianti a parametri fermi | stessi `modelli/` su tutti i 42 prodotti |
| 4. Portafoglio | `portafoglio/`, con le liste dei trade del software e quelle esportate da ProRealTime per i sistemi in produzione |
| 5. Macchina di ricerca | è il software |
| 6. Direzioni nuove | file in `esperimenti/`; con i dati nuovi si aggiungono Bund (FGBL), Treasury, agricoli, bestiame e VIX tra i candidati scorrelati |

## Fasi

Un modulo per sessione di lavoro, per non consumare tutti i token insieme. Il disegno dei moduli di validazione e le prove di taratura le faccio io; i moduli con una specifica chiusa e i test già scritti (statistiche, generatore ProRealCode, analisi del portafoglio) si possono delegare a un agente Sonnet, che costa meno, e io controllo i test.

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | `motore/dati`: lettura con il taglio, ora italiana, barre, cross sintetici, cache, test | fatta (2026-11-22) |
| 2 | schema in-sample/out-of-sample e metriche decisi dalla ricerca | fatta (2026-11-22) |
| 3 | `catalogo` (orari, costi, gemelli) e `motori/mappa`; taratura su AUDJPY e DAX | fatta (2026-11-22): AUDJPY ritrovato, DAX rimandato alla fase 5 |
| 4 | `metriche` e `validazione` (delegabile con specifica) | fatta (2026-11-22), specifica in `spec-fase-4.md` |
| 5 | `condizioni` (libreria a famiglie) e `motori/eventi`; taratura su 185 NQ e oro | fatta (2026-11-22): long di 165 DAX e short dell'oro ritrovati, gli altri tre deboli |
| 6 | `motori/backtest` con numba; `cli` e formato dei file d'esperimento | fatta (2026-11-22), specifica in `spec-fase-6.md` |
| 7 | primi esperimenti: long DAX a 5 minuti, poi setaccio e trapianti dei modelli 128 e 185 (coda e rapporto del mattino stanno fuori dal software) | in corso: primo esperimento DAX tutto scartato; ricerca ad albero (`protocollo-albero.md`, `motore/albero.py`) fatta, primo albero sul momento di chiusura del DAX fermo alle radici |
| 8 | `uscita` verso ProRealCode e `portafoglio` (delegabili) | |
| 9 | `cruscotto`: applicazione locale per Andrea (`progetto-cruscotto.md`, `spec-cruscotto.md`) | prima versione fatta (2026-11-22): `python -m cruscotto` |

Dalla fase 3 ogni modulo nuovo espone già le sue funzioni alla `cli` e scrive il riassunto JSON, così l'interfaccia per l'IA cresce insieme al motore invece di essere aggiunta alla fine.

**Note sui dati emerse nella fase 1**: l'FDAX ha la sessione notturna Eurex dalla fine del 2018 (prima apriva alle 08:00 italiane); i cross contro yen si costruiscono con scala 100 (JY è quotato in dollari per 100 yen).

**Taratura della fase 3** (mappa oraria senza condizioni, 2011-2023, rendimenti in escursioni medie giornaliere al netto di spread e costo amministrativo notturno presi dalle pagine ufficiali IG, `fonti/prodotti/costi-ig.md`):

- *AUDJPY*, long dal lunedì 03:00 al mercoledì 22:00 (la finestra di 128): +0,080 escursioni per trade al netto, profit factor 1,21 senza stop, 9 anni positivi su 13, +0,15 nel 2019-2023 (t 1,85). Il segno c'è, e le migliori celle long dell'intera mappa sono tutte finestre lunedì-mercoledì, cioè il ciclo settimanale dello yen. Nessuna cella però supera la soglia del caso per 5.800 celle provate (t 4,2): la mappa da sola non avrebbe fatto scoprire 128, che vale perché l'ipotesi viene da un meccanismo dichiarato prima e perché il sistema reale aggiunge lo stop e le esclusioni.
- *DAX (FDAX)*: le due gambe di 165 senza le loro condizioni non rendono (short 12:30 + 7 ore da martedì a venerdì tra −0,024 e +0,002 escursioni; long 13:30 → 09:00 da lunedì a giovedì tra −0,020 e +0,005). Il loro vantaggio sta nelle condizioni (media esponenziale, RSI, minimo di ieri), quindi la taratura del DAX si fa con la tabella degli eventi nella fase 5, non con la mappa.
- *Una trappola vista sul DAX*: le celle migliori (long da lunedì e giovedì alle 17:00 tenuti nella sera, t 3,7, tutti gli anni positivi) esistono solo dalla fine del 2018 perché prima la sessione chiudeva alle 22:00, quindi hanno 5-6 anni invece di 13. Il riassunto riporta per questo gli anni di ogni cella; le celle con meno anni non si confrontano con le altre come se fossero ugualmente attendibili.

Comandi: `python -m motore.cli mappa calcola|migliori|cella <prodotto> --barre 60`, `python -m motore.cli catalogo`; test in `motore/test_mappa.py` (dati finti dal risultato noto). La mappa legge solo gli anni della scoperta.

**Cosa hanno mostrato i test della fase 4** (dati finti, 21 test, ognuno visto fallire con un errore introdotto apposta):
- *Perdite a grappolo.* Una serie a media zero con soli periodi più agitati non ha drawdown molto diversi dal rimescolamento semplice (rapporto fra 0,8 e 1,4 secondo il seme). Il bootstrap a blocchi fa la differenza quando nei periodi agitati il sistema perde davvero (media negativa negli agitati e positiva nei calmi): lì il drawdown mediano a blocchi è 1,3-1,7 volte quello rimescolato. Il rapporto della scheda misura quindi proprio le perdite raggruppate chieste da Andrea, non la semplice volatilità variabile.
- *La CPCV da sola non basta contro la selezione.* Su 50 varianti di puro rumore la variante scelta sugli anni di training è quasi sempre la stessa (la migliore per caso sull'intero campione), e il suo Sharpe sugli anni di test resta positivo nel 94% delle combinazioni, perché i training si sovrappongono quasi del tutto. La distribuzione CPCV si legge quindi sempre insieme al PBO e al DSR, che su quello stesso rumore danno l'allarme (PBO 0,58).
- MinBTL controllata: 13 anni e Sharpe 0,7 ammettono 24 prove indipendenti, 6 anni e Sharpe 1 ne ammettono 20.

**Taratura della fase 5** (motore degli eventi, regole tradotte alla lettera in `esperimenti/taratura/`, futures 2011-2023, netto dei costi IG, senza stop né target salvo dove detto; "specchio" è la stessa regola sull'altro lato):

| Gamba | Trade | Media per trade (escursioni) | Profit factor | Anni positivi | 2019-2023 | Specchio |
|---|---|---|---|---|---|---|
| 165 DAX long | 590 | +0,075 | 1,24 | 10 su 13 | +0,058 | +0,019 |
| 165 DAX short | 536 | +0,022 | 1,11 | 8 su 13 | −0,024 | +0,007 |
| 185 NQ short | 105 | +0,017 (lorda +0,087) | 1,03 | 6 su 13 | +0,068 | −0,156 |
| 185 oro long | 257 | +0,040 (lorda +0,094) | 1,08 | 7 su 13 | +0,093 | −0,097 |
| 185 oro short | 96 | +0,286 | 1,73 | 9 su 13 | +0,274 | +0,063 |

- Il long di 165 DAX c'è, e senza le sue due condizioni la stessa finestra dava zero (taratura della fase 3): il vantaggio sta nelle condizioni, come atteso. Lo short dell'oro c'è con il profit factor più alto. Le due gambe valgono più dello specchio, quindi non sono andamento generale del prodotto.
- Le due gambe dell'oro includono la condizione della barra che rompe il massimo (o il minimo) della precedente di 0,5% (`ptnl25`/`ptns25`, tradotta come 0,4 escursioni): senza, il long rendeva +0,005 e lo short +0,193.
- Lo short di 165 DAX, lo short del Nasdaq e, in misura minore, il long dell'oro sui futures 2011-2023 sono deboli. Aggiungere stop e target convertiti in escursioni (circa 2 escursioni di stop, target come nel codice) non cambia il quadro. Il Nasdaq short vive di pochi anni (2020 e 2022) con 105 trade in 13 anni, e il costo di tenerlo fino a 4 giorni mangia quattro quinti del lordo.
- L'apertura della giornata non è la causa: sui grafici di Andrea (US Tech 100 continuo a mezzanotte, oro fermo dalle 23:00 alle 00:00) la giornata di ProRealTime comincia a mezzanotte italiana, come qui e come la pausa del Globex. Restano due spiegazioni: i sistemi sono stati scelti su backtest IG che arrivano al 2026 (il 2024-2025 qui non si guarda), e su quelle gambe il risultato dipende da pochi anni.

**Fase 6.** Il backtest al minuto dà gli stessi trade del motore degli eventi quando non ci sono stop e target (165 DAX long: 590 trade, stessa media), e se ci sono decide l'ordine fra stop e target dentro la barra guardando i minuti. Un file d'esperimento non parte se manca un campo, se la griglia sfora il numero di prove ammesso dalla MinBTL (dimezzato in verticale, contando quelle già nel registro per la stessa famiglia) o se è già stato lanciato. Il lancio registra ogni combinazione, calcola PBO, CPCV e DSR per famiglia e prodotto, passa i primi 10 al backtest al minuto con la scheda completa e scrive il riassunto in `risultati/esperimenti/<nome>/`.

Una nota dalla prova sull'oro: lo stop di 1,7 escursioni (il 2% del codice) porta lo short da +0,29 a +0,12 escursioni per trade; 13 trade su 98 escono in stop. Va guardato nel setaccio, perché su quella gamba lo stop toglie più di quanto protegge.

## Prodotti

Quali prodotti IG quota davvero (alcuni agricoli e il riso, RR, probabilmente no) va segnato nel catalogo: quelli non quotati servono solo come gemelli per le conferme.
