"""Libreria di pattern per la ricerca a cicli (`motore/ricerca.py`), ricostruita dalle librerie di Andrea.

Fonti: `G:\\My Drive\\Andrea\\ProRealTime\\Pattern` (Unger Daily 139, MIG Estesi 215, MIG Speculari 45, MIG Indicatori,
Andy 10 minuti e BB/RSI/ADX, DAN 155); revisione ed errori in `ricerca/librerie-pattern.md`. Come lì proposto:
- ogni pattern è una **grandezza** di `motore/condizioni.py` con una **soglia tonda**, `[grandezza, operatore, soglia]`,
  così le soglie vicine si vedono come la stessa domanda e non come pattern diversi;
- soglie in **escursioni medie giornaliere** (o in rapporti senza unità), mai in % del prezzo: valgono nel 2014 e oggi;
- le grandezze sui giorni usano le funzioni giornaliere (`DHigh(1)`, `DClose(2)`), quindi non cambiano significato con il
  timeframe (l'errore di `ptn39`/`40`/`79`/`80` e degli indici `[1]` usati come "ieri");
- i pattern sempre falsi o con il segno invertito delle vecchie librerie (`ptn191`-`205`, `ptn41`, `uptn011`-`024`,
  `uptn132`) qui sono riscritti nella forma corretta della domanda che volevano fare.

Ogni pattern ha uno **strato**, cioè il ciclo della ricerca in cui entra:
1. struttura del prezzo (ieri, i giorni prima, l'apertura, la giornata fin qui): entra nella forza bruta, insieme all'ora
   d'ingresso e all'uscita;
2. indicatori e candele sulle barre del grafico: entrano nella prima moltiplicazione, come seconda condizione insieme a
   tutti quelli dello strato 1;
3. regime di volatilità e calendario: entrano nella seconda moltiplicazione, come filtro finale.
Per ora i pattern sono scritti per il long; il lato short usa la versione speculare della stessa grandezza
(`condizioni.specchia`).
"""
from __future__ import annotations

# (nome leggibile, categoria, strato, condizione)
PATTERN: list[tuple[str, str, int, list]] = [
    # ---- ieri (Unger 03-10, 69-82, 116-117, 129-139; MIG 13-16, 25, 46, 85-88, 129-144)
    ("ieri verde", "ieri", 1, ["ieri_verde", ">=", 0]),
    ("ieri rosso", "ieri", 1, ["ieri_verde", "<=", 0]),
    ("ieri su di almeno mezza escursione", "ieri", 1, ["var_ieri", ">=", 0.5]),
    ("ieri giù di almeno mezza escursione", "ieri", 1, ["var_ieri", "<=", -0.5]),
    ("ieri corpo piccolo (indecisione)", "ieri", 1, ["corpo_ieri", "<=", 0.25]),
    ("ieri corpo pieno", "ieri", 1, ["corpo_ieri", ">=", 0.75]),
    ("ieri chiusura nel 20% alto", "ieri", 1, ["pos_chiusura_ieri", ">=", 0.8]),
    ("ieri chiusura nel 20% basso", "ieri", 1, ["pos_chiusura_ieri", "<=", 0.2]),
    ("ieri giornata interna", "ieri", 1, ["interna_ieri", ">=", 1]),
    ("ieri giornata esterna", "ieri", 1, ["esterna_ieri", ">=", 1]),
    ("ieri massimo e minimo più alti", "ieri", 1, ["massimi_crescenti", ">=", 1]),
    ("ieri escursione più stretta di 4 giorni (NR4)", "ieri", 1, ["nr4", ">=", 1]),
    ("ieri escursione più stretta di 7 giorni (NR7)", "ieri", 1, ["nr7", ">=", 1]),
    ("ieri giornata stretta (< 0,7 escursioni)", "ieri", 1, ["escursione_ieri", "<=", 0.7]),
    ("ieri giornata ampia (> 1,3 escursioni)", "ieri", 1, ["escursione_ieri", ">=", 1.3]),
    # ---- i giorni prima (Unger 49-54, 95-96, 108-115; MIG 7, 19-22, 79-82)
    ("3 chiusure in rialzo di fila", "giorni prima", 1, ["chiusure_in_rialzo", ">=", 3]),
    ("3 chiusure in ribasso di fila", "giorni prima", 1, ["chiusure_in_rialzo", "<=", 0]),
    ("massimo di ieri sopra quello di 5 giorni fa", "giorni prima", 1, ["massimo_ieri_su:5", ">=", 0]),
    ("minimo di ieri sotto quello di 5 giorni fa", "giorni prima", 1, ["minimo_ieri_su:5", "<=", 0]),
    ("vicino al massimo di 20 giorni (entro 0,5 escursioni)", "giorni prima", 1, ["dal_massimo_20g", ">=", -0.5]),
    ("lontano dal massimo di 20 giorni (oltre 3 escursioni)", "giorni prima", 1, ["dal_massimo_20g", "<=", -3]),
    ("sopra la media di 50 giorni", "giorni prima", 1, ["media_50g", ">=", 0]),
    ("sotto la media di 50 giorni", "giorni prima", 1, ["media_50g", "<=", 0]),
    ("sopra la media di 200 giorni", "giorni prima", 1, ["media_200g", ">=", 0]),
    ("sotto la media di 200 giorni", "giorni prima", 1, ["media_200g", "<=", 0]),
    # ---- apertura di oggi (Unger 118-128; MIG 34, 49-52; DAN gap)
    ("gap in su di almeno 0,25 escursioni", "apertura", 1, ["gap", ">=", 0.25]),
    ("gap in su di almeno 0,5 escursioni", "apertura", 1, ["gap", ">=", 0.5]),
    ("gap in giù di almeno 0,25 escursioni", "apertura", 1, ["gap", "<=", -0.25]),
    ("gap in giù di almeno 0,5 escursioni", "apertura", 1, ["gap", "<=", -0.5]),
    ("apre sopra il massimo di ieri", "apertura", 1, ["apertura_in_ieri", ">=", 1]),
    ("apre sotto il minimo di ieri", "apertura", 1, ["apertura_in_ieri", "<=", 0]),
    ("apre sotto la metà di ieri", "apertura", 1, ["apertura_in_ieri", "<=", 0.5]),
    # ---- la giornata fin qui (Unger 33-48, 83-107, 137-139; MIG 4, 31, 120-126, 159-219 in escursioni)
    ("sopra la chiusura di ieri", "oggi fin qui", 1, ["dal_close_ieri", ">=", 0]),
    ("su di almeno 0,5 escursioni da ieri", "oggi fin qui", 1, ["dal_close_ieri", ">=", 0.5]),
    ("giù di almeno 0,5 escursioni da ieri", "oggi fin qui", 1, ["dal_close_ieri", "<=", -0.5]),
    ("giù di almeno 1 escursione da ieri", "oggi fin qui", 1, ["dal_close_ieri", "<=", -1]),
    ("su di almeno 0,3 escursioni dall'apertura", "oggi fin qui", 1, ["dall_apertura", ">=", 0.3]),
    ("giù di almeno 0,3 escursioni dall'apertura", "oggi fin qui", 1, ["dall_apertura", "<=", -0.3]),
    ("nel quarto alto della giornata", "oggi fin qui", 1, ["pos_oggi", ">=", 0.75]),
    ("nel quarto basso della giornata", "oggi fin qui", 1, ["pos_oggi", "<=", 0.25]),
    ("ha superato il massimo di ieri", "oggi fin qui", 1, ["massimo_oggi_su_ieri", ">=", 0]),
    ("ha rotto il minimo di ieri", "oggi fin qui", 1, ["minimo_oggi_su_ieri", "<=", 0]),
    ("sopra il minimo di ieri", "oggi fin qui", 1, ["dal_minimo_ieri", ">=", 0]),
    ("sceso di 0,5 escursioni dal massimo di oggi", "oggi fin qui", 1, ["dal_massimo_seduta", "<=", -0.5]),
    ("risalito di 0,5 escursioni dal minimo di oggi", "oggi fin qui", 1, ["dal_minimo_seduta", ">=", 0.5]),
    ("giornata già ampia (> 1 escursione)", "oggi fin qui", 1, ["escursione_oggi", ">=", 1]),
    ("giornata ancora stretta (< 0,5 escursioni)", "oggi fin qui", 1, ["escursione_oggi", "<=", 0.5]),
    ("su di 0,2 escursioni dalle 15:30", "oggi fin qui", 1, ["dal_1530", ">=", 0.2]),
    ("giù di 0,2 escursioni dalle 15:30", "oggi fin qui", 1, ["dal_1530", "<=", -0.2]),
    # ---- indicatori sulle barre (MIG Indicatori e Speculari 3-45; Andy 10 minuti e BB/RSI/ADX)
    ("RSI 2 sotto 10", "indicatori", 2, ["rsi:2", "<=", 10]),
    ("RSI 2 sopra 90", "indicatori", 2, ["rsi:2", ">=", 90]),
    ("RSI 14 sotto 30", "indicatori", 2, ["rsi:14", "<=", 30]),
    ("RSI 14 sopra 70", "indicatori", 2, ["rsi:14", ">=", 70]),
    ("sotto la banda bassa di Bollinger 20", "indicatori", 2, ["bollinger:20", "<=", 0]),
    ("sopra la banda alta di Bollinger 20", "indicatori", 2, ["bollinger:20", ">=", 1]),
    ("nuovo massimo di 20 barre (Donchian)", "indicatori", 2, ["donchian:20", ">=", 0]),
    ("sopra la media esponenziale di 20 barre", "indicatori", 2, ["dist_media:20", ">=", 0]),
    ("sotto la media esponenziale di 20 barre", "indicatori", 2, ["dist_media:20", "<=", 0]),
    ("sopra la media esponenziale di 100 barre", "indicatori", 2, ["dist_media:100", ">=", 0]),
    ("sotto la media esponenziale di 100 barre", "indicatori", 2, ["dist_media:100", "<=", 0]),
    ("MACD sopra zero", "indicatori", 2, ["macd", ">=", 0]),
    ("MACD sotto zero", "indicatori", 2, ["macd", "<=", 0]),
    ("ADX 14 sopra 25 (tendenza)", "indicatori", 2, ["adx:14", ">=", 25]),
    ("ADX 14 sotto 20 (laterale)", "indicatori", 2, ["adx:14", "<=", 20]),
    ("volatilità delle ultime 2 barre doppia di quella di 20", "indicatori", 2, ["atr_rapporto:2:20", ">=", 2]),
    ("volatilità delle ultime 2 barre metà di quella di 20", "indicatori", 2, ["atr_rapporto:2:20", "<=", 0.5]),
    # ---- candele sulle barre (MIG 30-31, 67, 94-100; candlestick 024)
    ("barra verde", "candele", 2, ["candela", ">=", 0]),
    ("barra rossa", "candele", 2, ["candela", "<=", 0]),
    ("barra avvolgente rialzista", "candele", 2, ["avvolgente", ">=", 1]),
    ("barra doppia della media", "candele", 2, ["barra_ampia", ">=", 2]),
    ("barra che fa un nuovo massimo sulla precedente", "candele", 2, ["rottura_barra", ">", 0]),
    # ---- regime di volatilità (modulo filtro-regime-volatilita; Andy avgtr)
    ("periodo agitato (escursione 20 giorni > 1,2 volte quella di 100)", "regime", 3, ["vol_relativa", ">=", 1.2]),
    ("periodo calmo (escursione 20 giorni < 0,8 volte quella di 100)", "regime", 3, ["vol_relativa", "<=", 0.8]),
    # ---- calendario
    ("lunedì", "calendario", 3, ["giorno_settimana", "==", 1]),
    ("martedì", "calendario", 3, ["giorno_settimana", "==", 2]),
    ("mercoledì", "calendario", 3, ["giorno_settimana", "==", 3]),
    ("giovedì", "calendario", 3, ["giorno_settimana", "==", 4]),
    ("venerdì", "calendario", 3, ["giorno_settimana", "==", 5]),
    ("non lunedì", "calendario", 3, ["giorno_settimana", ">=", 2]),
    ("non venerdì", "calendario", 3, ["giorno_settimana", "<=", 4]),
    ("fine mese (dal 24)", "calendario", 3, ["giorno_mese", ">=", 24]),
    ("inizio mese (fino al 5)", "calendario", 3, ["giorno_mese", "<=", 5]),
    ("terzo venerdì (scadenza opzioni)", "calendario", 3, ["terzo_venerdi", ">=", 1]),
]

NOMI = {tuple(p[3][:3]): p[0] for p in PATTERN}


def dello_strato(strato: int) -> list[tuple]:
    return [p for p in PATTERN if p[2] == strato]


_SCAMBI = [("in su", "in giù"), ("su di", "giù di"), ("rialzista", "ribassista"), ("rialzo", "ribasso"), ("sopra", "sotto"),
           ("massimi", "minimi"), ("massimo", "minimo"), ("alti", "bassi"), ("alto", "basso"), ("alta", "bassa"),
           ("barra verde", "barra rossa"), ("verde", "rosso"), ("risalito", "sceso"), ("superato", "rotto")]
_MAPPA = {**{a: b for a, b in _SCAMBI}, **{b: a for a, b in _SCAMBI}}
_RE = None


def _specchia_testo(t: str) -> str:
    """Scambia le parole di direzione (sopra/sotto, massimo/minimo, rialzo/ribasso...) in un solo passaggio."""
    import re
    global _RE
    if _RE is None:
        _RE = re.compile("|".join(sorted((re.escape(k) for k in _MAPPA), key=len, reverse=True)))
    return _RE.sub(lambda m: _MAPPA[m.group(0)], t)


def nome(cond: list, lato: int = 1) -> str:
    """Nome leggibile di una condizione della libreria (o la condizione scritta per esteso). Per lo short la condizione
    usa la grandezza speculare: il nome si scrive di conseguenza (le grandezze uguali per i due lati non cambiano)."""
    base = NOMI.get(tuple(cond[:3]), f"{cond[0]} {cond[1]} {cond[2]}")
    if lato > 0:
        return base
    from . import condizioni
    fam = famiglia(cond)
    f = condizioni.FAMIGLIE.get(fam)
    if f is None or f[0] is f[1]:
        return base
    if fam == "rsi":
        n = cond[0].split(":")[1] if ":" in cond[0] else "2"
        return f"RSI {n} {'sopra' if cond[1] in ('<', '<=') else 'sotto'} {100 - cond[2]:g}"
    return _specchia_testo(base)


def famiglia(cond: list) -> str:
    return cond[0].split(":")[0]
