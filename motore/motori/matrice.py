"""Motore a matrice: decine di migliaia di regole a ora fissa in pochi secondi (forza bruta della ricerca a cicli).

Una regola della forza bruta è: alle `hh:mm` (chiusura della barra), se tutte le condizioni sono vere, compra
all'apertura della barra dopo ed esci secondo l'uscita a tempo. Per ogni coppia (ora, uscita) il risultato di ogni
giorno non dipende dalle condizioni: si calcola una volta (`Matrice`), e una regola è la somma dei giorni in cui le sue
condizioni sono vere. Con le condizioni come colonne booleane, le somme per anno di migliaia di regole sono un
prodotto di matrici.

Differenza dichiarata dal motore degli eventi: qui ogni giorno è indipendente (nessun vincolo "una posizione alla
volta"). Con uscite entro la mattina dopo i due motori coincidono; con uscite di più giorni la matrice conta anche i
trade sovrapposti. I sistemi scelti si ricalcolano sempre con il motore degli eventi e poi al minuto.
"""
from __future__ import annotations

import math
from itertools import combinations

import numpy as np
import polars as pl
from numba import njit
from scipy.stats import norm

from .. import catalogo, condizioni, giudizio
from .eventi import _min

SOGLIE_ORE = np.array([s[0] for s in giudizio.SOGLIE_GUADAGNO])
SOGLIE_EURO = np.array([s[1] for s in giudizio.SOGLIE_GUADAGNO])


@njit(cache=True)
def _uscite(cand, tod, giorno, dn, barre, ora, ven, giorni):
    """Indice della barra d'uscita (eseguita alla sua apertura) per ogni barra di decisione; -1 se i dati finiscono."""
    n = len(tod)
    out = np.full(len(cand), -1, np.int64)
    for k in range(len(cand)):
        e = cand[k] + 1
        if e >= n:
            continue
        cambi = 0
        for j in range(e, n):
            if j > e and dn[j] != dn[j - 1]:
                cambi += 1
            esci = (barre >= 0 and j - e > barre) or (ora >= 0 and tod[j] == ora) \
                or (ven >= 0 and giorno[j] == 5 and tod[j] == ven) or (giorni > 0 and cambi >= giorni)
            if esci:
                if j + 1 < n:
                    out[k] = j + 1
                break
    return out


def orari(da: str, a: str, passo: int) -> list[str]:
    m0, m1 = _min(da), _min(a)
    return [f"{m // 60:02d}:{m % 60:02d}" for m in range(m0, m1 + 1, passo)]


class Matrice:
    """Risultati giorno per giorno di ogni coppia (ora, uscita) e valori delle condizioni alle barre di decisione.

    `ctx` è un `albero.Contesto` (tabella della scoperta, date, euro di oggi). `condizioni_` è la lista delle condizioni
    della libreria (`[grandezza, op, soglia]`), `uscite` la lista dei dict d'uscita (`{"barre": 4}`, `{"ora": "21:55"}`...).
    """

    def __init__(self, ctx, orari_: list[str], uscite: list[dict], condizioni_: list[list], lato: int = 1):
        tab = ctx.tab
        self.ctx, self.orari, self.uscite, self.condizioni, self.lato = ctx, orari_, uscite, condizioni_, lato
        self.n_anni = ctx.n_anni
        self.anni = np.array(ctx.anni)
        o = tab["o"].to_numpy()
        esc = tab["esc"].to_numpy()
        tod, giorno, dn = (tab[c].to_numpy().astype(np.int64) for c in ("tod", "giorno", "dn"))
        ore_ing = tab["ore"].to_numpy()
        anno = tab["data"].dt.year().to_numpy()
        valori = tab.select(*[condizioni.condizione(c, lato).fill_null(False).alias(f"p{k}")
                              for k, c in enumerate(condizioni_)]).to_numpy().astype(bool)
        valida = np.nan_to_num(esc) > 0
        prod = catalogo.prodotto(ctx.prodotto)
        apre_us = tab["apre"].dt.epoch("us").to_numpy()
        giorno_data = np.searchsorted(ctx.date, tab["data"].to_numpy().astype("datetime64[D]"))
        self.maschere: dict[str, np.ndarray] = {}
        self.trade: dict[tuple[str, int], dict] = {}
        for t in orari_:
            cand = np.flatnonzero((tod == _min(t)) & valida).astype(np.int64)
            self.maschere[t] = valori[cand]
            for k, u in enumerate(uscite):
                ui = _uscite(cand, tod, giorno, dn, -1 if u.get("barre") is None else int(u["barre"]), _min(u.get("ora")),
                             _min(u.get("venerdi")), int(u.get("giorni") or 0))
                ok = ui >= 0
                i, e, x = cand[ok], cand[ok] + 1, ui[ok]
                lordo = lato * (o[x] - o[e]) / esc[i]
                costo = prod.costo(ore_ing[e], o[e], dn[x] - dn[e])
                netto = lordo - (0 if costo is None else costo) / esc[i]
                a = anno[x] - ctx.anni[0]
                dentro = (a >= 0) & (a < self.n_anni)
                righe = np.flatnonzero(ok)[dentro]
                self.trade[(t, k)] = {
                    "righe": righe, "netto": netto[dentro], "lordo": lordo[dentro],
                    "ore": (apre_us[x] - apre_us[e])[dentro] / 3.6e9, "anno": a[dentro],
                    "giorno": giorno_data[x][dentro]}

    # ---- aggregati per anno
    def aggregati(self, t: str, k: int, m: np.ndarray) -> dict:
        """Somme per anno di `m` (giorni di decisione × regole, booleana, righe come `maschere[t]`): numero di trade,
        somma, somma dei quadrati del netto, ore totali."""
        tr = self.trade[(t, k)]
        mm = m[tr["righe"]].astype(np.float64)
        y = np.zeros((len(tr["anno"]), self.n_anni))
        y[np.arange(len(tr["anno"])), tr["anno"]] = 1.0
        x = tr["netto"][:, None]
        return {"n": y.T @ mm, "s": (y * x).T @ mm, "q": (y * x * x).T @ mm, "h": tr["ore"] @ mm,
                "l": tr["lordo"] @ mm}

    def serie(self, t: str, k: int, m: np.ndarray) -> np.ndarray:
        """Serie giornaliera del netto (escursioni) di una regola, sui giorni della scoperta."""
        tr = self.trade[(t, k)]
        sel = m[tr["righe"]]
        return np.bincount(tr["giorno"][sel], weights=tr["netto"][sel], minlength=len(self.ctx.date))


def statistiche(ag: dict, euro_esc: float | None, n_anni: int, maschera_anni: np.ndarray | None = None) -> dict:
    """Misure vettoriali di molte regole dagli aggregati per anno, sugli anni della maschera (tutti se None).

    Restituisce array lunghi quanto le regole: n, media, t, trade l'anno, ore medie, guadagno di oggi G, margine M,
    mediana fuori campione della CPCV (2 anni di prova, tutte le combinazioni degli anni della maschera), le due metà
    e i tre terzi del periodo (media a trade)."""
    mk = np.ones(ag["n"].shape[0], bool) if maschera_anni is None else maschera_anni
    na = int(mk.sum())
    N, S, Q = ag["n"][mk], ag["s"][mk], ag["q"][mk]
    n, s, q = N.sum(0), S.sum(0), Q.sum(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        media = s / n
        var = np.maximum(q - n * media * media, 0) / (n - 1)
        sd = np.sqrt(var)
        t = np.where(sd > 0, media / sd * np.sqrt(n), np.nan)
        ore = ag["h"] / np.maximum(ag["n"].sum(0), 1)
        lordo = ag["l"] / np.maximum(ag["n"].sum(0), 1)
        richiesto = SOGLIE_EURO[np.minimum(np.searchsorted(SOGLIE_ORE, ore, side="left"), len(SOGLIE_EURO) - 1)]
        G = media * (euro_esc or 0) / richiesto
        ta = n / na
        M = G * ta / 12
        idx = np.flatnonzero(mk)
        oos = []
        for test in combinations(range(len(idx)), 2):
            tt = list(test)
            nn, ss = N[tt].sum(0), S[tt].sum(0)
            oos.append(np.where(nn > 0, ss / np.where(nn > 0, nn, 1), np.nan))
        cpcv = np.nanmedian(np.array(oos), axis=0) if oos else np.full(len(n), np.nan)
        meta = na // 2
        m1 = S[:meta].sum(0) / N[:meta].sum(0)
        m2 = S[meta:].sum(0) / N[meta:].sum(0)
        terzi = [S[p].sum(0) / N[p].sum(0) for p in np.array_split(np.arange(na), 3)]
    return {"n": n, "s": s, "media": media, "sd": sd, "var": var, "t": t, "trade_anno": ta, "ore": ore, "lordo": lordo,
            "richiesto": richiesto, "G": G, "M": M, "cpcv": cpcv, "meta1": m1, "meta2": m2, "terzi": np.array(terzi)}


def quantile_filtro(n_figlio, media_figlio, n_padre, media_padre, var_padre) -> np.ndarray:
    """Dove sta la media del figlio fra le medie di sottoinsiemi casuali del padre della stessa ampiezza (senza
    reimmissione): approssimazione normale del test con 1.000 filtri casuali dell'albero."""
    with np.errstate(divide="ignore", invalid="ignore"):
        k, N = n_figlio, n_padre
        se = np.sqrt(var_padre * (N - 1) / N * (N - k) / (k * (N - 1)))
        z = (media_figlio - media_padre) / se
    return np.where(np.isfinite(z), norm.cdf(z), np.where(k >= N, 0.5, np.nan))


def r2(serie: np.ndarray) -> float:
    c = np.cumsum(serie)
    x = np.arange(len(c), dtype=float)
    if c.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, c)[0, 1] ** 2)


def sharpe(serie: np.ndarray) -> float:
    sd = serie.std(ddof=1)
    return float(serie.mean() / sd * math.sqrt(252)) if sd > 0 else float("nan")
