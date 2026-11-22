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
