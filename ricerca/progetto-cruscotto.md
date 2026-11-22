# Progetto del cruscotto: l'applicazione locale per Andrea

Scritto il 2026-11-22 dopo aver guardato il pannello di AlphaMining (copia in sola lettura su vercel). Sostituisce la fase 9 di `progetto-software.md`: il cruscotto non è più un insieme di pagine statiche ma un'applicazione che gira sul PC e si apre nel browser a `localhost`, con cui Andrea naviga, filtra, legge e segna le sue decisioni.

## Che cosa tenere di AlphaMining

L'impianto è quello giusto e va ripreso quasi tutto:
- **elenco dei sistemi** con filtri per tipo di logica, timeframe, giro, prodotto, stato (da guardare, da approfondire, live, scartati) e colonne ordinabili, con i numeri del future e quelli di 1 CFD IG al netto dello spread affiancati;
- **scheda del sistema** a schede: riepilogo, curva, controlli, robustezza, calendario, trade, codice;
- **tabella dei controlli** con valore, soglia ed esito, prima i non superati;
- **come si è costruita la strategia**: una riga per ogni pezzo aggiunto (motore, filtri, uscite) con il prima e dopo;
- **sensitività dei parametri vicini** come mappa a colori, **finestre mobili di 12 mesi** come caselle verdi e rosse, **calendario mensile**, **MAE contro risultato**;
- **codice PRT** scaricabile con la verifica "stessi trade del motore";
- pagine **portafogli** e **rotazione**, registro dei giri.

## Che cosa va sistemato (dal confronto con i nostri metodi)

1. **Il Deflated Sharpe non blocca la promozione.** Il 3332 FDAX ha DSR 0,55 su 82.939 prove (2.751 effettive) ed è promosso; nella nostra regola è un no. Con decine di migliaia di prove per prodotto, la lista dei promossi è in gran parte quello che il caso produce: DSR, PBO e budget di prove dalla MinBTL diventano cancelli, non avvisi.
2. **La prova finale diventa un filtro.** "Prova finale superata 103 su 114" vuol dire che la lista si sceglie anche su quel periodo, che così smette di essere fuori campione. Nel nostro schema i due holdout si guardano una volta, dopo la selezione, e un sistema che li fallisce si chiude, non si scarta in silenzio mentre gli altri restano.
3. **Selezione a passi sull'in-sample.** Filtri e uscite scelti come "la curva più regolare che migliora il punteggio" moltiplicano le prove senza che il PBO della famiglia le misuri. Da noi ogni passo è una griglia registrata e il PBO si calcola sulla famiglia intera.
4. **Monte Carlo a rimescolamento semplice.** Sottostima il drawdown quando le perdite sono a grappoli (la tua obiezione): da noi bootstrap a blocchi e per regime, con il confronto con il rimescolamento.
5. **Numeri lordi come numeri principali.** Utile, curva e controlli sono al lordo (il costo del future "non sottratto"), il CFD è una colonna a parte e gli interessi overnight non sono contati. Da noi tutto è netto dei costi IG (spread per fascia oraria e costo notturno), e il lordo è il dettaglio.
6. **Grandezze in % del prezzo** (R², trade medio) su futures rettificati ai rinnovi: negli anni vecchi sono sbagliate del 20-50%. Da noi punti, escursioni medie ed euro di 1 CFD.
7. **Prodotti che non reggono il trading.** 36 sistemi sul riso (RR), molti agricoli e bestiame "che non reggono lo spread ×3": da noi il catalogo li tiene come gemelli e non li porta in lista.
8. **Manca il "perché".** Nessun campo per meccanismo, fonte e direzione attesa, quindi nessun modo di distinguere un vantaggio con una ragione da una coincidenza. Da noi ogni sistema eredita l'ipotesi dal suo esperimento.

## Come è fatta l'applicazione

- **Tecnica**: un server Python locale (libreria standard o FastAPI, senza servizi esterni) che legge `risultati/` e il registro, e una pagina web con grafici interattivi (libreria salvata in locale, funziona senza internet). Si avvia con un comando o un collegamento sul desktop e si apre a `http://localhost:8765`. I dati dei test restano sul PC.
- **Pagine**:
  1. *Esperimenti*: ogni idea con ipotesi, meccanismo, fonte, direzione, prove usate sul budget, PBO della famiglia, esito; il resoconto scritto.
  2. *Sistemi*: l'elenco filtrabile alla AlphaMining, con il giudizio a colori per gruppo (sotto) come colonne.
  3. *Scheda*: le schede di AlphaMining più le nostre (sotto).
  4. *Portafoglio*: i sistemi in produzione e i candidati; sovrapposizione dei drawdown, calendario dell'esposizione, contributo al CDaR.
  5. *Registro*: tutte le prove fatte, anche scartate, con il numero effettivo.
  6. *Verifiche ProRealTime*: dove Andrea segna l'esito del suo fuori campione per ogni sistema provato.
- **Azioni di Andrea** (le uniche scritture): stato del sistema (da guardare, da approfondire, in verifica, live, scartato), una nota, l'esito della verifica su ProRealTime. Lanciare ricerche resta fuori dall'applicazione.

## La scheda: giudizio a due livelli

**Giudizio calcolato, deterministico, uguale per tutti.** Le metriche della scheda sono raggruppate per significato, ogni gruppo ha un esito (verde, giallo, rosso) con le soglie scritte accanto:

| Gruppo | Domanda | Metriche |
|---|---|---|
| Caso o vantaggio | quanto è probabile che sia fortuna dopo tutte le prove fatte | DSR, PSR, PBO della famiglia, CPCV (mediana, 10° percentile), t, numero di prove effettive, haircut |
| Regolarità | la curva sale in modo costante | R², K-ratio, costanza della pendenza anno per anno, anni e trimestri positivi, Sharpe su 12 mesi mobili, tempo sott'acqua |
| Robustezza | regge se cambio qualcosa | zona stabile dei parametri, costi doppi, senza i 10 trade migliori, ingresso ±15 minuti, simmetria long/short, prodotto gemello, regimi, 2019-2023 |
| Rischio | quanto può far male | drawdown reale, Monte Carlo a blocchi contro rimescolato (5°-50°-95°), peggior serie di perdite, z di Wald-Wolfowitz, Ulcer |
| Costi e fattibilità | regge su IG | netto di 1 CFD, guadagno medio lordo / spread, costo notturno, tempo in mercato, margine |
| Portafoglio | aggiunge diversificazione | sovrapposizione dei drawdown e correlazione di coda con i sistemi in produzione, contributo al CDaR |

I gruppi "caso o vantaggio" e "costi" sono cancelli: un rosso lì e il sistema non è candidato, qualunque cosa dicano gli altri.

**Giudizio dell'IA, non deterministico, separato e firmato.** Solo per i sistemi che superano i cancelli (non tutti: sarebbe costoso e inutile sui peggiori). Un riquadro a parte, con data e modello, che dice: che tipo di vantaggio è e se il meccanismo dichiarato è credibile alla luce dei numeri, cosa preoccupa (per esempio "vive di due anni", "lo spread si mangia metà del lordo"), cosa guardare nella verifica su ProRealTime, e una raccomandazione. Lo scrivo io in sessione e resta salvato; non sostituisce il giudizio calcolato e non lo modifica.

## Ordine di lavoro

1. dati per l'applicazione: ogni esperimento scrive già i file dei candidati; servono in più le metriche di robustezza mancanti (costi doppi, ±15 minuti, gemello, regimi), le finestre mobili, il calendario e il codice ProRealCode (fase 8, uscita);
2. server e pagine *Sistemi* e *Scheda*, sul primo esperimento DAX;
3. *Esperimenti*, *Registro*, *Verifiche*; poi *Portafoglio* con le liste dei trade dei sistemi in produzione.
