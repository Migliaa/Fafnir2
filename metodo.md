# Metodo di lavoro

Come si è lavorato su 128 BIAS HOUR e 165 DAX (novembre 2026), da ripetere sui prossimi.

## Il ciclo

1. **Andrea incolla il codice** di un sistema attivo su ProRealTime (conto IG). Va salvato in `sistemi/<nome>/originale.txt` e non si tocca più.
2. **Analisi del codice** in `sistemi/<nome>/analisi.md`: cosa fa, errori (unità, valute, formule della taglia), da dove sembra venire il vantaggio.
2b. **Ricerca sul prodotto**, fatta prima di scrivere le proposte e salvata in `fonti/prodotti/<prodotto>.md` per riusarla. Riguarda:
   - chi muove il prezzo e quando: banche centrali e date delle riunioni, fixing, sessioni, flussi ricorrenti;
   - legami con altri mercati;
   - regimi storici e crolli;
   - effetti di calendario già documentati;
   - costi reali presso IG.
   Ogni informazione va registrata con il tipo di fonte: studio accademico, dati ufficiali, banca o broker, testimonianza di trader. Le testimonianze e i blog servono solo a generare ipotesi, mai a sostenerle. Un'informazione diventa proposta solo se ha un meccanismo economico preciso e una direzione dichiarata prima del test. Non va inseguita ogni curiosità trovata: si scelgono le poche ipotesi più solide, e le altre restano nel file per i tentativi successivi. Esempio completo: `fonti/prodotti/dax.md` (orari, spread IG per fascia oraria, finanziamento, letteratura, ipotesi con esito).
3. **Proposte a tornate.** Prima tornata di 4-5 moduli indipendenti; le tornate successive di 2-4, scritte sopra l'ultima versione combinata, con almeno un'uscita o una logica nuova. Ogni modulo è un file completo in `proposte/`, pronto da incollare, con:
   - l'intestazione standard di gestione del capitale (`moduli/intestazione-capitale.txt`) con i valori del test;
   - un interruttore `UsaMx` che con 0 riproduce esattamente la versione su cui è scritto, da lanciare come riferimento;
   - un commento in testa con ipotesi, fonte e come giudicarlo;
   - parametri tondi scelti a priori, con le 2-3 varianti da provare indicate nel commento;
   - righe `GRAPH` di controllo dove servono, da togliere prima del reale.
4. **Andrea fa il backtest** e manda screenshot del "Rapporto dettagliato" di ProRealTime (spesso filtrato su posizioni long o short, due versioni affiancate) o delle curve dei profitti. Dagli screenshot si ricavano i numeri e si scrivono in `registro-test.md`.
5. **Si interpreta ogni risultato**, anche i fallimenti: perché è andato così, che cosa dice sul sistema. Le lezioni generali vanno in `moduli/lezioni.md`.
6. **I moduli promossi** vanno in `moduli/` in forma generica se servono ad altri sistemi, e si combinano in `sistemi/<nome>/versioni/` (C1, C2… poi `DEFINITIVO-produzione.txt`). La versione per il reale ha l'intestazione standard e niente `GRAPH`.
7. **A fine sistema** si aggiornano `idee/idee-di-trading.md` (logiche con grado di prova e principi trasversali), `moduli/lezioni.md`, la tabella dei sistemi in `README.md`.

## Come usare i risultati dei sistemi precedenti

Moduli, lezioni e idee sono stati misurati su un sistema e un prodotto precisi; su un sistema nuovo sono ipotesi da ritestare, non impostazioni da applicare.

- **Partire dal codice nuovo**, non dalla libreria: prima l'analisi e la ricerca sul prodotto, poi si guarda se qualche modulo già validato è pertinente.
- **Un modulo validato si propone su un nuovo sistema solo se c'è lo stesso meccanismo** che lo faceva funzionare. Per esempio, la taglia legata alla volatilità serve solo su gambe con uscita a tempo e stop lontano. Anche così entra come tentativo, con l'interruttore e il confronto con l'originale, mai già incluso.
- **Le lezioni dicono cosa controllare, non cosa aspettarsi**: valuta di `StrategyProfit`, lettura del report, confronto a parità di esposizione.
- **Le idee smentite** valgono per il prodotto e il sistema su cui sono state smentite. Su un altro prodotto si possono riprovare, se c'è un motivo per pensare che lì il meccanismo sia diverso.
- **Ogni tornata deve avere almeno un'idea che non viene dalla libreria.**

## Cosa conta per Andrea

- Obiettivi dichiarati: gestione del reinvestimento, gestione della volatilità, guadagno medio per trade più alto, anche con meno trade.
- Scarta un modulo che alza il profitto ma fa salire molto il drawdown (M7), o che porta un vantaggio troppo piccolo rispetto a spread e commissioni (M9).
- Guarda la regolarità della curva e il profitto totale insieme al guadagno medio. Ha scartato un filtro che alzava il guadagno medio ma lasciava lo stesso drawdown con metà del profitto (165 DAX, M5 sul long), e ha accettato meno profitto quando il drawdown si dimezzava, perché poi si può aumentare la taglia (M5 sullo short; 3251 FDAX, M2). Non vuole filtri che tolgono molti trade a sistemi che ne hanno già pochi: su 3251 FDAX ha scartato un filtro che portava profitto / drawdown da 7,2 a 8,7 lasciando 207 trade in 14 anni su 370 (M1).
- Per confrontare un modulo, se non gli si dice altro, usa l'originale a 1 contratto senza reinvestimento: ogni proposta deve dire nel messaggio quale riferimento lanciare (di solito lo stesso file con `UsaMx = 0`).
- Le uscite dei suoi sistemi sono tutte a tempo, a orario, a stop o a target: le ha indicate come campo da esplorare (novembre 2026).
- Non mostra la curva dei rendimenti prima dei test, per evitare che le proposte si adattino al passato: le idee devono venire dalla teoria e dalla logica del codice, non dai dati.
- Vuole sapere prima di ogni ingresso quanto rischia: le leve diverse su capitale e profitti, con tetti che cambiano, sono troppo complicate da testare e gestire (185 NQ, novembre 2026). Su 185 NQ la console chiede solo capitale versato, profitti precedenti, % di capitale persa allo stop per lato e reinvestimento sì/no.
- Vuole poter fermare e riavviare il sistema riportando a mano il profitto realizzato, attivare o spegnere il reinvestimento e pesare long e short con due moltiplicatori: tutto nell'intestazione standard `moduli/intestazione-capitale.txt`, in cima a ogni codice. Tara i pesi per rendere uguali i drawdown massimi dei due lati.

## Contesto tecnico

- Conto IG in euro; i backtest ProRealTime sono nella valuta dello strumento (AUD/JPY Mini: 800.000 ¥ di capitale iniziale; DAX: 5.000 €, dal 2015). 165 DAX in reale con 6.000 € più 1.600 € di profitti precedenti.
- Su AUD/JPY Mini la formula di taglia originale porta a una perdita a stop di circa 15.000 ¥ per il long.
- 185 oro (Spot Gold E1, 1 € per punto) in reale con 7.200 €. Sull'aggressività Andrea dice di non voler essere troppo conservativo: la sceglie lui leggendo il drawdown massimo in percentuale (`moduli/controllo-drawdown.txt`), e vuole che il sistema entri sempre almeno con il minimo di contratti, qualunque sia il capitale.
- Note pratiche su ProRealCode e sul report in `fonti/prorealtime/sintassi-verificata.md`.
