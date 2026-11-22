"""Motore degli eventi: prova una regola d'ingresso e d'uscita su tutte le barre della scoperta.

Una regola è un dict (lo stesso formato dei file d'esperimento):
    {"lato": -1, "giorni": [2, 3, 4, 5], "da": "12:30", "a": "12:30",
     "cond": [["dist_media:25", ">", 0], ["minimo_ieri_su:5", "<=", 0, "grezza"]],
     "uscita": {"barre": 12, "ora": null, "venerdi": null, "giorni": null},
     "stop": null, "target": null, "max_al_giorno": 1}

Convenzioni di ProRealTime, perché la traduzione sia letterale:
- `da`/`a` e `uscita.ora` sono l'ora di CHIUSURA della barra (`Time`); l'ordine parte alla
  chiusura ed è eseguito all'apertura della barra successiva;
- `uscita.barre = N` equivale a `barindex - tradeindex > N`; `giorni = N` a "N cambi di giornata
  in posizione"; `venerdi = "21:00"` a `dayofweek = 5 and time = 210000`;
- `stop` e `target` in escursioni medie giornaliere dal prezzo d'ingresso, attivi dalla barra
  d'ingresso; se in una barra sono toccati entrambi, vince lo stop (prudente);
- una posizione alla volta, al massimo `max_al_giorno` ingressi per giornata.

Risultati in escursioni medie giornaliere, al netto dei costi del catalogo; solo anni della
scoperta (`config.SCOPERTA`), come la mappa.
"""
from __future__ import annotations

import numpy as np
import polars as pl
from numba import njit

from .. import catalogo, condizioni, dati, metriche
from ..config import RECENTE, SCOPERTA

GIORNI_NOMI = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]


def _anni(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(pl.col("apre").dt.year().is_between(*SCOPERTA))


def base(nome: str, minuti: int) -> pl.DataFrame:
    """Barre della scoperta con il contesto giornaliero che serve alle condizioni."""
    g = _anni(dati.barre(nome, 1440)).sort("apre")
    g = g.with_columns(
        pl.col("apre").dt.date().alias("data"),
        pl.col("o").alias("dopen"),
        (pl.col("h") - pl.col("l")).rolling_mean(20).shift(1).alias("esc"),
        *[pl.col(x).shift(k).alias(f"{x}{k}") for x in "ohlc" for k in range(1, 6)],
    ).drop("apre", "chiude", "o", "h", "l", "c", "v", "minuti")
    b = _anni(dati.barre(nome, minuti)).sort("apre").with_columns(pl.col("apre").dt.date().alias("data"))
    b = b.join(g, on="data", how="left").with_columns(
        pl.col("h").cum_max().over("data").alias("dmax"),
        pl.col("l").cum_min().over("data").alias("dmin"),
    )
    return b.with_columns(
        pl.col("chiude").dt.weekday().alias("giorno"),
        (pl.col("chiude").dt.hour().cast(pl.Int32) * 60 + pl.col("chiude").dt.minute().cast(pl.Int32)).alias("tod"),
        (pl.col("data").cast(pl.Int32)).alias("dn"),
    )


def _min(hhmm: str | None) -> int:
    if hhmm is None:
        return -1
    a, b = hhmm.split(":")
    return int(a) * 60 + int(b)


@njit(cache=True)
def _simula(cand, o, h, l, esc, tod, giorno, dn, lato, barre, ora, ven, giorni, stop, target, max_g):
    n = len(o)
    ent = np.full(len(cand), -1, np.int64)
    usc = np.full(len(cand), -1, np.int64)
    px = np.zeros(len(cand))
    k = 0
    libero = 0          # primo indice in cui si può rientrare
    giorno_ult, quanti = -1, 0
    for i in cand:
        e = i + 1
        if e >= n or e < libero:
            continue
        if dn[i] != giorno_ult:
            giorno_ult, quanti = dn[i], 0
        if quanti >= max_g:
            continue
        p0 = o[e]
        sl = p0 - lato * stop * esc[i] if stop > 0 else np.nan
        tp = p0 + lato * target * esc[i] if target > 0 else np.nan
        cambi = 0
        uscita, prezzo = -1, 0.0
        for j in range(e, n):
            if j > e and dn[j] != dn[j - 1]:
                cambi += 1
            # stop e target dentro la barra j
            if stop > 0 and ((lato > 0 and l[j] <= sl) or (lato < 0 and h[j] >= sl)):
                uscita = j
                prezzo = sl if (lato > 0 and o[j] > sl) or (lato < 0 and o[j] < sl) or j == e else o[j]
                break
            if target > 0 and ((lato > 0 and h[j] >= tp) or (lato < 0 and l[j] <= tp)):
                uscita = j
                prezzo = tp if (lato > 0 and o[j] < tp) or (lato < 0 and o[j] > tp) or j == e else o[j]
                break
            # uscite a tempo: decise alla chiusura di j, eseguite all'apertura di j+1
            esci = (barre >= 0 and j - e > barre) or (ora >= 0 and tod[j] == ora) \
                or (ven >= 0 and giorno[j] == 5 and tod[j] == ven) or (giorni > 0 and cambi >= giorni)
            if esci:
                if j + 1 < n:
                    uscita, prezzo = j + 1, o[j + 1]
                break
        if uscita < 0:
            break       # fine dei dati in posizione: il trade non si conta
        ent[k], usc[k], px[k] = e, uscita, prezzo
        k += 1
        quanti += 1
        libero = uscita
    return ent[:k], usc[:k], px[:k]


def candidati(tabella: pl.DataFrame, regola: dict) -> np.ndarray:
    """Indici delle barre di decisione (righe della tabella) in cui la regola d'ingresso è vera."""
    lato = int(regola["lato"])
    filtro = pl.col("esc").is_not_null() & (pl.col("esc") > 0)
    if regola.get("giorni"):
        filtro &= pl.col("giorno").is_in(regola["giorni"])
    da, a = _min(regola.get("da")), _min(regola.get("a"))
    if da >= 0:
        filtro &= pl.col("tod").is_between(da, a) if da <= a else ~pl.col("tod").is_between(a + 1, da - 1)
    for cond in regola.get("cond", []):
        filtro &= condizioni.condizione(cond, lato).fill_null(False)
    return tabella.with_row_index("i").filter(filtro)["i"].to_numpy().astype(np.int64)


def prova(nome: str, minuti: int, regola: dict, tabella: pl.DataFrame | None = None,
          molt_costi: float = 1.0) -> dict:
    """Restituisce (riassunto JSON, tabella dei trade). `molt_costi` moltiplica i costi del catalogo
    (2.0 = costi doppi); la colonna `punti` è il netto in punti di prezzo."""
    b = base(nome, minuti) if tabella is None else tabella
    lato = int(regola["lato"])
    cand = candidati(b, regola)

    u = regola.get("uscita", {})
    arr = {x: b[x].to_numpy() for x in ("o", "h", "l", "esc")}
    tod, giorno, dn = (b[x].to_numpy().astype(np.int64) for x in ("tod", "giorno", "dn"))
    ent, usc, px = _simula(cand, arr["o"], arr["h"], arr["l"], np.nan_to_num(arr["esc"]), tod, giorno, dn, lato,
                           -1 if u.get("barre") is None else int(u["barre"]), _min(u.get("ora")),
                           _min(u.get("venerdi")), int(u.get("giorni") or 0),
                           float(regola.get("stop") or 0), float(regola.get("target") or 0),
                           int(regola.get("max_al_giorno", 1)))
    dec = ent - 1                                   # barra della decisione
    esc = arr["esc"][dec]
    lordo = lato * (px - arr["o"][ent]) / esc
    prod = catalogo.prodotto(nome)
    ore = b["apre"].dt.hour().to_numpy()[ent] + b["apre"].dt.minute().to_numpy()[ent] / 60
    costo = prod.costo(ore, arr["o"][ent], dn[usc] - dn[ent])
    costo_p = 0.0 if costo is None else molt_costi * costo
    netto = lordo - costo_p / esc
    punti = lato * (px - arr["o"][ent]) - costo_p
    trade = pl.DataFrame({"ingresso": b["apre"].gather(ent), "uscita": b["apre"].gather(usc),
                          "barre": usc - ent, "lordo": lordo, "netto": netto, "punti": punti})
    return _riassunto(nome, minuti, regola, trade, b, costo is not None), trade


def _riassunto(nome, minuti, regola, trade, b, con_costi) -> dict:
    out = {"prodotto": nome, "barre": minuti, "lato": "long" if regola["lato"] > 0 else "short",
           "anni": list(SCOPERTA), "costi": con_costi, "n": trade.height}
    if trade.height < 5:
        return out
    x = trade["netto"].to_numpy()
    date = b["data"].unique().sort()
    giorn = (pl.DataFrame({"data": date}).join(
        trade.group_by(pl.col("uscita").dt.date().alias("data")).agg(pl.col("netto").sum()), on="data", how="left")
        .fill_null(0.0)["netto"].to_numpy())
    anno = trade.group_by(pl.col("uscita").dt.year().alias("anno")).agg(pl.col("netto").sum().alias("s")).sort("anno")
    rec = trade.filter(pl.col("uscita").dt.year().is_between(*RECENTE))["netto"]
    vinti, persi = x[x > 0].sum(), -x[x < 0].sum()
    out.update({
        "media_esc": x.mean(), "lorda_esc": trade["lordo"].mean(),
        "t": x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if x.std() > 0 else None,
        "pf": vinti / persi if persi > 0 else None, "vincenti": (x > 0).mean(),
        "sharpe": metriche.sharpe(giorn), "dd_max_esc": metriche.drawdown(giorn)["massimo"],
        "anni_positivi": (anno["s"] > 0).mean(), "media_recente_esc": rec.mean() if rec.len() else None,
        "in_mercato": float(trade["barre"].sum() / b.height),
        "z_ww": metriche.z_wald_wolfowitz(x)["z"],
        "per_anno": {int(a): round(s, 2) for a, s in anno.iter_rows()},
    })
    return metriche.pulisci(out)
