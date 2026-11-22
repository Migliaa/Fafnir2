# Prossima sessione: modelli 128 e 185, catalogo di modelli, prova sul rumore

Scritto il 2026-11-22 a fine sessione. Prima di cominciare: leggere `ricerca/fafnir2.md`, poi controllare l'esito della campagna `forex-cicli-1` (`risultati/campagne/forex-cicli-1/campagna.json`; se manca, `python -m motore.campagna riepilogo esperimenti/forex-cicli-1.json`) e riferirlo ad Andrea in poche righe.

Ogni modello nuovo segue la stessa regola: **prima la taratura**, cioè il motore deve ritrovare da solo, fra i primi della forza bruta, il sistema di Andrea da cui il modello è preso. Se non lo ritrova, il motore è sbagliato e non si cerca altro.

## 1. Modello 128: finestra settimanale

**Cos'è** (`sistemi/128-bias-hour-audjpy-1h/analisi.md`, `ricerca/cosa-distingue-i-sistemi.md`): un giorno e un'ora d'ingresso, un giorno e un'ora d'uscita nella stessa settimana; nessuna condizione richiesta, al più qualche esclusione; stop stretto sul long (circa mezza escursione giornaliera) o d'emergenza sullo short. AUD/JPY: long lunedì 03:00 → mercoledì 22:00, short giovedì 12:00 → venerdì 18:00.

**Da fare nel motore:**
1. Uscita nuova `{"giorno": 3, "ora": "22:00"}` (esce il primo mercoledì alle 22:00 dopo l'ingresso) in `motori/eventi._simula`, `motori/backtest._percorso`, `motori/matrice._uscite` e `uscita.traduci` (`dayofweek = 3 AND time = 220000`); test che i tre motori diano gli stessi trade.
2. Ingresso solo in un giorno della settimana: nella griglia della forza bruta il giorno d'ingresso diventa una dimensione (`"giorni_ingresso": [1,2,3,4,5]`), non un filtro dello strato 3.
3. Griglia del modello (`"modello": "settimanale"` nel file): 5 giorni × 24 ore d'ingresso (barre da 60 minuti) × uscite = stesso giorno o 1-4 giorni dopo a 6-8 ore tonde (00, 03, 06, 09, 12, 15, 18, 21, 22) → circa 120 × 30 = 3.600 finestre per lato.
4. **Esclusioni**: nella moltiplicazione 1 aggiungere anche i pattern negati (`["grandezza", "op", soglia, "non"]` in `condizioni.condizione`), perché il 128 usa solo esclusioni; il filtro 2 per un'esclusione chiede che tolga pochi trade (al massimo un terzo) e che quelli tolti perdano.
5. Stop: nel ricalcolo esatto provare 0,25, 0,5, 1 escursione e "nessuno" (lo stop del 128 long è il cuore dell'asimmetria: perdenti a stop pieno, vincenti 2,75 volte lo stop).

**Taratura su AUD/JPY 1 ora:** la forza bruta senza pattern deve mettere lunedì 03:00 → mercoledì 22:00 long e giovedì 12:00 → venerdì 18:00 short fra le prime 20 finestre del loro lato (in-sample 2014-2023). Poi lo stesso su GBP/JPY (già confermato a mano, `analisi.md` del 128).

**AUD/JPY va usato solo per la taratura, non come prodotto da cercare:** Andrea lo ha già in reale, un altro sistema su AUD/JPY non diversifica. La ricerca vera del modello 128 va sugli altri cambi (prima gli yen: GBP/JPY, EUR/JPY, CAD/JPY, NZD/JPY, CHF/JPY, che hanno lo stesso meccanismo, ciclo settimanale dello yen; poi i sei della campagna forex) e sugli indici, scartando le finestre correlate con il 128 (serve la lista dei trade del 128 in produzione o il suo backtest dal motore).

## 2. Modello 185: spostamento forte dall'apertura, tenuto giorni

**Cos'è** (`sistemi/185-top-ua-342-gc-1h/analisi.md`, `sistemi/185-top-ua-342-nq-1h/analisi.md`): in una finestra di ore (11:00-22:00 sull'oro), il primo momento in cui il prezzo è a più di X escursioni orarie medie dall'apertura del giorno e fa un nuovo massimo, si entra e si tiene 3-4 giorni (o 60-100 barre), stop a circa 3 escursioni medie. Oro long X = 2,5, short X = 5,5; Nasdaq short X = 4 più chiusura forte ieri.

**Da fare nel motore:**
1. Motore a **finestra**: per ogni giorno e per ogni condizione, la prima barra della finestra `[da, a]` in cui la condizione è vera è l'ingresso (una decisione al giorno). L'ingresso dipende dalla condizione, quindi non si riusa la matrice a ora fissa: un'altra funzione numba che, per ogni pattern, trova la prima barra di ogni giorno e calcola il risultato per ogni uscita (pattern × uscite × giorni, sempre veloce).
2. Pattern dello strato 185: `dist_apertura:20` (escursioni orarie, già in `condizioni.py`) >= 1,5, 2, 2,5, 3, 4, 5, 6, da soli e insieme a "nuovo massimo di 20 barre" o "barra che fa un nuovo massimo"; per lo short gli stessi speculari.
3. Uscite: 30, 60, 90 barre; 2, 3, 4, 5 giorni; venerdì 21:00. Stop in **escursioni orarie** (aggiungere `stop_unita: "barre"` accanto alle escursioni giornaliere in eventi e backtest): 2, 3, 4.
4. Finestre d'ingresso: tutto il giorno, 08-12, 11-22, 15:30-22.

**Taratura:** sull'oro a 1 ora deve ritrovare il long 11-22, >= 2,5 escursioni con nuovo massimo, tenuto 3-4 giorni; sul Nasdaq lo short >= 4 escursioni dopo una chiusura forte. Poi ricerca sugli altri prodotti (indici, petrolio, argento, cambi), entrambi i lati, soglie asimmetriche ammesse (tratto 6: lo short sui prodotti che salgono aspetta un evento raro).

## 3. Catalogo di modelli da fonti (ricerche brevi, poi una griglia per modello)

Le ricerche costano minuti: si può aggiungere un modello per ogni idea con un meccanismo. Per ognuno, prima una scheda in `fonti/paper/modelli.md` (fonte, tipo di fonte, meccanismo in una riga, prodotti, direzione attesa), poi la griglia. Candidati da verificare con una ricerca sulle fonti (non ancora letti, solo da elencare e controllare):
- **momento dell'ultima mezz'ora** sugli indici (Gao, Han, Li, Zhou 2018): in parte già nella griglia oraria;
- **notte contro giorno** (Lou, Polk, Skouras 2019): rendimenti della notte e della seduta separati, long notturno sugli indici (il long del 165 DAX è già di questo tipo);
- **cambio di mese** (Lakonishok e Smidt 1988; McConnell e Xu 2008): ultimi e primi giorni del mese, finestra di più giorni → modello settimanale con il giorno del mese al posto della settimana;
- **giorni prima della Fed** (Lucca e Moench 2015): serve il calendario delle riunioni FOMC, date pubbliche da salvare in `Dati/`;
- **fixing di Londra delle 16:00 e di Tokyo delle 9:55** sui cambi (Evans 2018; per Tokyo `fonti/prodotti/audjpy.md`): finestre attorno al fixing e fine mese;
- **rottura del range d'apertura** (opening range breakout) sugli indici: primi 15-30 minuti, rottura, uscita a fine giornata;
- **range della sessione asiatica** sui cambi europei: rottura all'apertura di Londra;
- **ritorno verso la media dopo giornate estreme** (RSI a 2 giorni su indici, Connors): già in parte nei pattern, da fare come modello giornaliero con uscita a più giorni.

**Indicatori nuovi su cui costruire pattern:** distanza dal VWAP della giornata (i dati hanno il volume), range della sessione asiatica, escursione rimasta rispetto alla media (quanto manca a fare la giornata media), percentile della volatilità della giornata fino a quell'ora, rendimento della notte. Ognuno va in `condizioni.py` con la traduzione ProRealCode.

## 4. Prova sul rumore nella pipeline standard

Decisione: **sì, resta**, ed è già parte di ogni ricerca (`RUMORE_PREDEFINITO = 50` in `motore/ricerca.py`; un file può metterla a 0 solo per le prove del software). È l'unica prova che misura direttamente quanto di bello esce dalla selezione per caso, e costa solo dove serve: parte solo se la ricerca ha dei finali, e rifà solo i cicli. Miglioramenti da fare:
- usare i risultati del rumore anche per **tarare le soglie** (quanto € a trade e quale R² produce il rumore per prodotto e timeframe), invece di soglie decise a tavolino;
- mostrare nella pagina della campagna, per ogni ricerca, il migliore vero contro il 95° percentile del rumore (c'è già il dato);
- nei modelli nuovi (settimanale, finestra) la prova sul rumore va adattata: per le finestre senza condizioni il rumore giusto è spostare i giorni della settimana (scambiare lunedì con giovedì), non le condizioni.

## Ordine consigliato

1. Riferire la campagna forex.
2. Modello 128 (uscita per giorno e ora, ingresso per giorno, esclusioni), taratura su AUD/JPY, poi ricerca su yen e indici.
3. Modello 185 (motore a finestra, stop in escursioni orarie), taratura su oro e Nasdaq, poi ricerca sugli altri prodotti.
4. Catalogo dei modelli da fonti e indicatori nuovi, una campagna notturna per gruppo di modelli.
