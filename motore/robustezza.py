"""Controlli di robustezza di un candidato già lanciato (cruscotto, `ricerca/spec-cruscotto.md`, A1).

Sono prove diagnostiche sullo stesso periodo della scoperta (`config.SCOPERTA`), non tentativi di
selezione: non scrivono nel registro e il registro si legge solo per i parametri vicini.
Tutto in escursioni medie giornaliere al netto dei costi IG, salvo i campi `punti` ed `euro`.
"""
from __future__ import annotations

import copy

import numpy as np
import polars as pl

from . import catalogo, condizioni, dati, metriche, validazione
from .config import SCOPERTA
from .motori import backtest, eventi

SPOSTAMENTO_MINUTI = 15
BARRE_MAX_SPOSTAMENTO = 15
CAMPI_CORTI = ("n", "media_esc", "lorda_esc", "pf", "sharpe", "anni_positivi", "media_recente_esc")


def _hhmm(minuti: int) -> str:
    minuti %= 1440
    return f"{minuti // 60:02d}:{minuti % 60:02d}"


def _sposta(regola: dict, minuti: int) -> dict:
    r = copy.deepcopy(regola)
    for k in ("da", "a"):
        if r.get(k) is not None:
            r[k] = _hhmm(eventi._min(r[k]) + minuti)
    return r


def _corto(r: dict) -> dict:
    return {k: r.get(k) for k in CAMPI_CORTI}


def _carica(prod: str, barre: int, ctx: dict):
    chiave = (prod, barre)
    if chiave not in ctx:
        ctx[chiave] = (eventi.base(prod, barre), dati.minuti(prod))
    return ctx[chiave]


def _sim(prod: str, barre: int, regola: dict, ctx: dict, molt: float = 1.0):
    tab, m1 = _carica(prod, barre, ctx)
    return backtest.simula(prod, barre, regola, tab, m1, molt_costi=molt)


def giornaliera(trade: pl.DataFrame, date: pl.Series, colonna: str = "netto") -> np.ndarray:
    """Somma di `colonna` per giorno di borsa (zeri compresi), attribuita al giorno d'uscita."""
    return (pl.DataFrame({"data": date}).join(
        trade.group_by(pl.col("uscita").dt.date().alias("data")).agg(pl.col(colonna).sum()),
        on="data", how="left").fill_null(0.0)[colonna].to_numpy())


def _media(x: pl.Series):
    return float(x.mean()) if x.len() else None


def regimi(trade: pl.DataFrame, tab: pl.DataFrame) -> dict:
    """Media per trade e numero di trade con l'escursione media sopra e sotto la mediana della scoperta."""
    esc_g = tab.group_by("data").agg(pl.col("esc").first())["esc"].drop_nulls()
    med = float(esc_g.median())
    j = trade.join(tab.select("apre", "esc"), left_on="ingresso", right_on="apre", how="left")
    alto, basso = j.filter(pl.col("esc") > med)["netto"], j.filter(pl.col("esc") <= med)["netto"]
    return {"mediana_esc": med, "sopra": {"n": alto.len(), "media": _media(alto)},
            "sotto": {"n": basso.len(), "media": _media(basso)}}


def finestre_12_mesi(trade: pl.DataFrame) -> list[dict]:
    """Profitto netto e numero di trade per ogni finestra di 12 mesi con passo di 3 mesi (per data d'uscita)."""
    mesi = (trade["uscita"].dt.year().cast(pl.Int64) * 12 + trade["uscita"].dt.month().cast(pl.Int64) - 1).to_numpy()
    netto = trade["netto"].to_numpy()
    primo, fine = SCOPERTA[0] * 12, (SCOPERTA[1] + 1) * 12
    out = []
    for s in range(primo, fine - 11, 3):
        dentro = (mesi >= s) & (mesi < s + 12)
        a = s + 11
        out.append({"da": f"{s // 12}-{s % 12 + 1:02d}", "a": f"{a // 12}-{a % 12 + 1:02d}",
                    "profitto": float(netto[dentro].sum()), "n": int(dentro.sum())})
    return out


def calendario(trade: pl.DataFrame) -> dict:
    """Profitto netto per anno e mese d'uscita: {anno: {mese: profitto}}."""
    out: dict = {}
    for a, m, s in trade.group_by(pl.col("uscita").dt.year().alias("a"), pl.col("uscita").dt.month().alias("m")) \
            .agg(pl.col("netto").sum()).sort("a", "m").iter_rows():
        out.setdefault(str(a), {})[str(m)] = float(s)
    return out


def vicini(famiglia: str, prodotto: str, parametri: dict, sharpe_candidato: float | None) -> dict | None:
    """Combinazioni del registro della stessa famiglia e prodotto che differiscono di un solo passo di griglia.

    L'ordine dei valori di ogni chiave è quello di prima apparizione nel registro, che è l'ordine della
    griglia. `rapporto` = mediana degli Sharpe dei vicini / Sharpe del candidato; zona stabile se >= 0,7.
    """
    righe = [r for r in validazione._righe() if r["famiglia"] == famiglia and r["prodotto"] == prodotto]
    if not parametri or not righe:
        return None
    valori: dict = {k: [] for k in parametri}
    for r in righe:
        for k in parametri:
            v = r["parametri"].get(k)
            if v not in valori[k]:
                valori[k].append(v)
    for r in righe:
        if r["parametri"] == parametri and r["sharpe"] is not None:
            sharpe_candidato = r["sharpe"]
    out = []
    for r in righe:
        p = r["parametri"]
        diverse = [k for k in parametri if p.get(k) != parametri[k]]
        if len(diverse) == 1 and r["sharpe"] is not None:
            k = diverse[0]
            if abs(valori[k].index(p[k]) - valori[k].index(parametri[k])) == 1:
                out.append({"parametri": p, "sharpe": r["sharpe"]})
    if not out:
        return None
    med = float(np.median([v["sharpe"] for v in out]))
    rapporto = med / sharpe_candidato if sharpe_candidato and sharpe_candidato > 0 else None
    return {"n": len(out), "sharpe_candidato": sharpe_candidato, "vicini": out, "mediana": med,
            "rapporto": rapporto, "stabile": bool(rapporto is not None and rapporto >= 0.7)}


def euro(trade: pl.DataFrame, date: pl.Series, prodotto: str) -> dict:
    """Profitto, drawdown massimo e trade medio per 1 CFD IG in euro; None se il valore del punto non è noto."""
    ep = catalogo.prodotto(prodotto).euro_punto
    out = {"euro_punto": ep, "n": trade.height, "profitto": None, "drawdown": None, "trade_medio": None}
    if ep is None or not trade.height or "punti" not in trade.columns:
        return out
    g = giornaliera(trade, date, "punti") * ep
    out.update({"profitto": float(g.sum()), "drawdown": metriche.drawdown(g)["massimo"],
                "trade_medio": float(trade["punti"].mean() * ep)})
    return out


def _gemello(prodotto: str) -> list[str]:
    return [g for g in catalogo.prodotto(prodotto).gemelli
            if g in catalogo.CATALOGO and catalogo.prodotto(g).spread is not None]


def calcola(regola: dict, prodotto: str, barre: int, *, famiglia: str | None = None,
            parametri: dict | None = None, ctx: dict | None = None):
    """Restituisce (dict di robustezza, tabella dei trade del candidato con la colonna `punti`)."""
    ctx = {} if ctx is None else ctx
    base, trade = _sim(prodotto, barre, regola, ctx)
    tab, _ = _carica(prodotto, barre, ctx)
    date = tab["data"].unique().sort()
    out: dict = {"base": base}
    out["costi_doppi"] = _sim(prodotto, barre, regola, ctx, 2.0)[0]

    out["ingresso_spostato"] = None
    if barre <= BARRE_MAX_SPOSTAMENTO:
        out["ingresso_spostato"] = {
            nome: _corto(_sim(prodotto, barre, _sposta(regola, d), ctx)[0])
            for nome, d in (("meno_15", -SPOSTAMENTO_MINUTI), ("piu_15", SPOSTAMENTO_MINUTI))}

    out["specchio"] = _corto(_sim(prodotto, barre, condizioni.specchia(regola), ctx)[0])

    out["gemello"] = None
    for g in _gemello(prodotto):
        try:
            out["gemello"] = {"prodotto": g, **_corto(_sim(g, barre, regola, ctx)[0])}
            break
        except (FileNotFoundError, KeyError, ValueError):
            continue

    out["regimi"] = regimi(trade, tab) if trade.height else None
    out["finestre_12_mesi"] = finestre_12_mesi(trade) if trade.height else []
    out["calendario"] = calendario(trade) if trade.height else {}
    out["vicini"] = vicini(famiglia, prodotto, parametri or {}, base.get("sharpe")) if famiglia else None
    out["euro"] = euro(trade, date, prodotto)
    return metriche.pulisci(out), trade


def robustezza(regola: dict, prodotto: str, barre: int, **kw) -> dict:
    """Dict JSON dei controlli di robustezza (`calcola` restituisce anche i trade)."""
    return calcola(regola, prodotto, barre, **kw)[0]
