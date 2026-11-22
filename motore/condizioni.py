"""Libreria di condizioni a famiglie (cantiere 1, `ricerca/librerie-pattern.md`).

Ogni famiglia è una grandezza continua calcolata alla chiusura della barra, con solo le
informazioni disponibili in quel momento; una condizione è `[grandezza, operatore, soglia]`,
per esempio `["dist_apertura:20", ">=", 4]` (4 true range medi a favore del lato). La soglia è in unità di volatilità, mai in % del
prezzo. Il nome porta i parametri dopo i due punti (`rsi:2`, `incrocio:5:10`).

Ogni famiglia ha la sua versione specchiata per l'altro lato (`specchia`): la stessa regola
scritta per il long diventa quella dello short senza riscriverla, come chiede il blocco 4
della scheda (simmetria long/short).

Colonne attese nella tabella di base (`motori/eventi.base`): o h l c della barra, `dopen`,
`dmax` `dmin` (massimo e minimo della giornata fino a questa barra), `o1..`, `h1..h5`,
`l1..l5`, `c1` (giorni precedenti), `esc` (escursione media giornaliera dei 20 giorni prima).
"""
from __future__ import annotations

import polars as pl

c, o, h, l = pl.col("c"), pl.col("o"), pl.col("h"), pl.col("l")
ESC = pl.col("esc")


def _tr() -> pl.Expr:
    return pl.max_horizontal(h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs())


def atr(n: int) -> pl.Expr:
    """True range medio come AverageTrueRange di ProRealTime (media di Wilder)."""
    return _tr().ewm_mean(alpha=1 / n, adjust=False, min_samples=n)


def ema(n: int) -> pl.Expr:
    return c.ewm_mean(span=n, adjust=False, min_samples=n)


def rsi(n: int) -> pl.Expr:
    d = c.diff()
    su = d.clip(lower_bound=0).ewm_mean(alpha=1 / n, adjust=False, min_samples=n)
    giu = (-d).clip(lower_bound=0).ewm_mean(alpha=1 / n, adjust=False, min_samples=n)
    return 100 - 100 / (1 + su / giu)


def adx(n: int) -> pl.Expr:
    """ADX di Wilder come ADX[n] di ProRealTime."""
    su, giu = h - h.shift(1), l.shift(1) - l
    pdm = pl.when((su > giu) & (su > 0)).then(su).otherwise(0.0)
    mdm = pl.when((giu > su) & (giu > 0)).then(giu).otherwise(0.0)
    a_ = atr(n)
    pdi = 100 * pdm.ewm_mean(alpha=1 / n, adjust=False, min_samples=n) / a_
    mdi = 100 * mdm.ewm_mean(alpha=1 / n, adjust=False, min_samples=n) / a_
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    return dx.ewm_mean(alpha=1 / n, adjust=False, min_samples=n)


def bollinger_b(n: int) -> pl.Expr:
    """%B di Bollinger a 2 deviazioni standard: 0 sulla banda bassa, 1 su quella alta."""
    m, sd = c.rolling_mean(n), c.rolling_std(n, ddof=0)
    return (c - (m - 2 * sd)) / (4 * sd)


def _d(x: str, k: int) -> pl.Expr:
    return pl.col(f"{x}{k}")


def _nr(k: int) -> pl.Expr:
    """Escursione di ieri la più piccola degli ultimi k giorni: 1 o 0."""
    r1 = _d("h", 1) - _d("l", 1)
    return (r1 <= pl.min_horizontal(*[_d("h", j) - _d("l", j) for j in range(2, k + 1)])).cast(pl.Float64)


def _incrocio(a: pl.Expr, b: pl.Expr) -> pl.Expr:
    return ((a > b) & (a.shift(1) <= b.shift(1))).cast(pl.Float64)


# famiglia: (long, short) -> funzione dei parametri che dà l'espressione
FAMIGLIE = {
    # distanza dall'apertura della giornata in true range medi delle barre (185 NQ e oro)
    "dist_apertura": (lambda n=20: (c - pl.col("dopen")) / atr(n),
                      lambda n=20: (pl.col("dopen") - c) / atr(n)),
    # distanza dalla media esponenziale in escursioni giornaliere (165 DAX)
    "dist_media": (lambda n=25: (c - ema(n)) / ESC, lambda n=25: (ema(n) - c) / ESC),
    "rsi": (lambda n=2: rsi(n), lambda n=2: 100 - rsi(n)),
    # posizione della chiusura di ieri nel suo intervallo, 0 = sul minimo, 1 = sul massimo
    "pos_chiusura_ieri": (lambda: (pl.col("c1") - pl.col("l1")) / (pl.col("h1") - pl.col("l1")),
                          lambda: (pl.col("h1") - pl.col("c1")) / (pl.col("h1") - pl.col("l1"))),
    # minimo di ieri rispetto a quello di k giorni fa (165 DAX short: <= 0)
    "minimo_ieri_su": (lambda k=5: (pl.col("l1") - pl.col(f"l{k}")) / ESC,
                       lambda k=5: (pl.col(f"h{k}") - pl.col("h1")) / ESC),
    # distanza dal massimo della seduta fino a qui (3251: <= -0,5% ~ in escursioni)
    "dal_massimo_seduta": (lambda: (c - pl.col("dmax")) / ESC, lambda: (pl.col("dmin") - c) / ESC),
    # distanza dal minimo di ieri (3251: non sotto il minimo di ieri, >= 0)
    "dal_minimo_ieri": (lambda: (c - pl.col("l1")) / ESC, lambda: (pl.col("h1") - c) / ESC),
    # rendimento dalla chiusura di ieri in escursioni (momento intraday, Baltussen et al. 2021)
    "dal_close_ieri": (lambda: (c - pl.col("c1")) / ESC, lambda: (pl.col("c1") - c) / ESC),
    "gap": (lambda: (pl.col("dopen") - pl.col("c1")) / ESC, lambda: (pl.col("c1") - pl.col("dopen")) / ESC),
    # massimo della barra sopra quello della barra prima (185 oro: +0,5% ~ 0,4 escursioni)
    "rottura_barra": (lambda: (h - h.shift(1)) / ESC, lambda: (l.shift(1) - l) / ESC),
    "escursione_oggi": (lambda: (pl.col("dmax") - pl.col("dmin")) / ESC,) * 2,
    # media semplice di a barre che incrocia sopra quella di b (185 NQ long)
    "incrocio": (lambda a=5, b=10: _incrocio(c.rolling_mean(a), c.rolling_mean(b)),
                 lambda a=5, b=10: _incrocio(-c.rolling_mean(a), -c.rolling_mean(b))),
    # minimo di oggi sopra quello di ieri di x escursioni (esclusione del long dell'oro)
    "minimo_oggi_su_ieri": (lambda: (pl.col("dmin") - pl.col("l1")) / ESC,
                            lambda: (pl.col("h1") - pl.col("dmax")) / ESC),
    # giorno di ieri ribassista dopo uno rialzista (esclusione dello short dell'oro): 1 o 0
    "inversione_ieri": (lambda: ((pl.col("c1") < pl.col("o1")) & (pl.col("c2") > pl.col("o2"))).cast(pl.Float64),
                        lambda: ((pl.col("c1") > pl.col("o1")) & (pl.col("c2") < pl.col("o2"))).cast(pl.Float64)),
    # --- protocollo ad albero (2026-11-22): ipotesi calcolabili sullo stesso strumento, quindi traducibili in ProRealTime
    # volatilità del periodo: escursione media di 20 giorni su quella di 100 (al posto del VIX, che ProRealTime non
    # può leggere dentro una strategia sul DAX)
    "vol_relativa": (lambda: ESC / pl.col("esc_lunga"),) * 2,
    # movimento dall'apertura di Wall Street (barra delle 15:30) in escursioni: conferma americana senza l'S&P
    "dal_1530": (lambda: (c - pl.col("o1530")) / ESC, lambda: (pl.col("o1530") - c) / ESC),
    # terzo venerdì del mese (scadenza delle opzioni): 1 o 0
    "terzo_venerdi": (lambda: ((pl.col("data").dt.weekday() == 5) & pl.col("giorno_mese").is_between(15, 21)).cast(pl.Float64),) * 2,
    # giorno del mese di calendario (fine mese: >= 25)
    "giorno_mese": (lambda: pl.col("giorno_mese").cast(pl.Float64),) * 2,
    # --- libreria riordinata (2026-11-22, `motore/pattern.py`): dalle librerie di Andrea, soglie in escursioni
    # ieri e i giorni prima (funzioni giornaliere, il significato non cambia con il timeframe)
    "corpo_ieri": (lambda: (_d("c", 1) - _d("o", 1)).abs() / (_d("h", 1) - _d("l", 1)),) * 2,
    "var_ieri": (lambda: (_d("c", 1) - _d("c", 2)) / ESC, lambda: (_d("c", 2) - _d("c", 1)) / ESC),
    "ieri_verde": (lambda: (_d("c", 1) - _d("o", 1)) / ESC, lambda: (_d("o", 1) - _d("c", 1)) / ESC),
    "chiusure_in_rialzo": (lambda: sum((_d("c", k) > _d("c", k + 1)).cast(pl.Float64) for k in (1, 2, 3)),
                           lambda: sum((_d("c", k) < _d("c", k + 1)).cast(pl.Float64) for k in (1, 2, 3))),
    "massimo_ieri_su": (lambda k=5: (_d("h", 1) - _d("h", k)) / ESC, lambda k=5: (_d("l", k) - _d("l", 1)) / ESC),
    "interna_ieri": (lambda: ((_d("h", 1) < _d("h", 2)) & (_d("l", 1) > _d("l", 2))).cast(pl.Float64),) * 2,
    "esterna_ieri": (lambda: ((_d("h", 1) > _d("h", 2)) & (_d("l", 1) < _d("l", 2))).cast(pl.Float64),) * 2,
    "massimi_crescenti": (lambda: ((_d("h", 1) > _d("h", 2)) & (_d("l", 1) > _d("l", 2))).cast(pl.Float64),
                          lambda: ((_d("h", 1) < _d("h", 2)) & (_d("l", 1) < _d("l", 2))).cast(pl.Float64)),
    "nr4": (lambda: _nr(4),) * 2,
    "nr7": (lambda: _nr(7),) * 2,
    "escursione_ieri": (lambda: (_d("h", 1) - _d("l", 1)) / ESC,) * 2,
    "dal_massimo_20g": (lambda: (c - pl.col("h20g")) / ESC, lambda: (pl.col("l20g") - c) / ESC),
    "media_50g": (lambda: (c - pl.col("m50g")) / ESC, lambda: (pl.col("m50g") - c) / ESC),
    "media_200g": (lambda: (c - pl.col("m200g")) / ESC, lambda: (pl.col("m200g") - c) / ESC),
    # oggi fino a questa barra
    "apertura_in_ieri": (lambda: (pl.col("dopen") - _d("l", 1)) / (_d("h", 1) - _d("l", 1)),
                         lambda: (_d("h", 1) - pl.col("dopen")) / (_d("h", 1) - _d("l", 1))),
    "dall_apertura": (lambda: (c - pl.col("dopen")) / ESC, lambda: (pl.col("dopen") - c) / ESC),
    "pos_oggi": (lambda: (c - pl.col("dmin")) / (pl.col("dmax") - pl.col("dmin")),
                 lambda: (pl.col("dmax") - c) / (pl.col("dmax") - pl.col("dmin"))),
    "massimo_oggi_su_ieri": (lambda: (pl.col("dmax") - _d("h", 1)) / ESC, lambda: (_d("l", 1) - pl.col("dmin")) / ESC),
    "dal_minimo_seduta": (lambda: (c - pl.col("dmin")) / ESC, lambda: (pl.col("dmax") - c) / ESC),
    # indicatori e candele sulle barre del grafico
    "bollinger": (lambda n=20: bollinger_b(n), lambda n=20: 1 - bollinger_b(n)),
    "donchian": (lambda n=20: (c - h.rolling_max(n).shift(1)) / atr(n), lambda n=20: (l.rolling_min(n).shift(1) - c) / atr(n)),
    "macd": (lambda: (ema(12) - ema(26)) / ESC, lambda: (ema(26) - ema(12)) / ESC),
    "adx": (lambda n=14: adx(n),) * 2,
    "atr_rapporto": (lambda a=2, b=20: atr(a) / atr(b),) * 2,
    "candela": (lambda: (c - o) / ESC, lambda: (o - c) / ESC),
    "avvolgente": (lambda: ((c > o) & (c.shift(1) < o.shift(1)) & (c >= o.shift(1)) & (o <= c.shift(1))).cast(pl.Float64),
                   lambda: ((c < o) & (c.shift(1) > o.shift(1)) & (c <= o.shift(1)) & (o >= c.shift(1))).cast(pl.Float64)),
    "barra_ampia": (lambda: (h - l) / atr(20),) * 2,
    # calendario
    "giorno_settimana": (lambda: pl.col("giorno").cast(pl.Float64),) * 2,
}

OPERATORI = {">": pl.Expr.gt, ">=": pl.Expr.ge, "<": pl.Expr.lt, "<=": pl.Expr.le, "==": pl.Expr.eq}


def grandezza(nome: str, lato: int = 1) -> pl.Expr:
    """Espressione della grandezza `nome` ("famiglia:p1:p2") per il lato (+1 long, -1 short)."""
    fam, *par = nome.split(":")
    if fam not in FAMIGLIE:
        raise KeyError(f"famiglia sconosciuta: {fam}")
    f = FAMIGLIE[fam][0 if lato > 0 else 1]
    return f(*(int(p) for p in par)).alias(nome)


def condizione(cond: list, lato: int = 1) -> pl.Expr:
    """`[nome, op, soglia]` nei termini del lato (si specchia con la regola); con un quarto
    elemento "grezza" usa la versione long anche sullo short, per tradurre alla lettera un codice
    che sullo short non è speculare (165 DAX: minimo di ieri sotto quello di 5 giorni fa)."""
    nome, op, soglia, *grezza = cond
    return OPERATORI[op](grandezza(nome, 1 if grezza else lato), soglia)


def specchia(regola: dict) -> dict:
    """La stessa regola per l'altro lato: cambia il lato, le grandezze si specchiano da sole."""
    return {**regola, "lato": -regola["lato"]}
