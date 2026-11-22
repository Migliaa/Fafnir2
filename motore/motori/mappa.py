"""Mappa oraria: rendimento medio per (giorno d'ingresso, ora d'ingresso, durata), anno per anno.

Ogni cella è un sistema senza condizioni: entra all'apertura della barra delle `ora` del giorno
`giorno` (come un ordine ProRealTime dato alla chiusura della barra precedente) ed esce
all'apertura della barra che inizia `durata` minuti dopo, in ora italiana di orologio. Le celle
la cui uscita cade in un orario senza barre (fine settimana, festivi) restano vuote.

Rendimento in escursioni medie giornaliere (media di massimo-minimo dei 20 giorni precedenti),
netto dei costi del catalogo, separatamente per long e short. Si calcola solo sugli anni della
scoperta: barre, uscite ed escursioni fuori da quegli anni non vengono nemmeno lette, quindi la
mappa non può guardare i due holdout.
"""
from __future__ import annotations

import math

import numpy as np
import polars as pl

from .. import catalogo, dati
from ..config import RECENTE, RISULTATI, SCOPERTA

GIORNI = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
CARTELLA = RISULTATI / "mappa"


def _file(nome: str, minuti: int):
    return CARTELLA / f"{nome}_{minuti}m.parquet"


def _anni(df: pl.DataFrame, col: str = "apre") -> pl.DataFrame:
    return df.filter(pl.col(col).dt.year().is_between(*SCOPERTA))


def calcola(nome: str, minuti: int = 60, ore_max: int = 72) -> dict:
    prod = catalogo.prodotto(nome)
    b = _anni(dati.barre(nome, minuti)).select("apre", "o")
    g = (_anni(dati.barre(nome, 1440))
         .with_columns((pl.col("h") - pl.col("l")).rolling_mean(20).shift(1).alias("esc"))
         .select(pl.col("apre").dt.date().alias("data"), "esc"))
    b = (b.with_columns(pl.col("apre").dt.date().alias("data"))
         .join(g, on="data", how="left").filter(pl.col("esc") > 0))

    # minuti di orologio italiano (senza fuso), per misurare la durata come la vede ProRealTime
    t = (b["apre"].dt.replace_time_zone(None).cast(pl.Int64) // 60_000_000).to_numpy()
    o = b["o"].to_numpy()
    esc = b["esc"].to_numpy()
    giorno = b["apre"].dt.weekday().to_numpy() - 1
    ora = b["apre"].dt.hour().to_numpy().astype(np.int32)
    ora_min = ora * 60 + b["apre"].dt.minute().to_numpy().astype(np.int32)
    anno = b["apre"].dt.year().to_numpy()
    giorno_n = t // 1440
    n = len(t)

    pezzi = []
    for durata in range(minuti, ore_max * 60 + 1, minuti):
        j = np.searchsorted(t, t + durata)
        ok = j < n
        ok[ok] = t[j[ok]] == t[ok] + durata
        i = np.nonzero(ok)[0]
        if not len(i):
            continue
        jj = j[i]
        r = (o[jj] - o[i]) / esc[i]
        if prod.spread is None:
            c = np.zeros(len(i))
        else:
            notti = giorno_n[jj] - giorno_n[i]
            a, z = prod.ore_principali
            s = np.where((ora[i] >= a) & (ora[i] < z), prod.spread, prod.spread_fuori or prod.spread)
            c = (s + np.abs(o[i]) * prod.finanziamento / 365.0 * notti) / esc[i]
        df = pl.DataFrame({"giorno": giorno[i], "ora": ora_min[i], "anno": anno[i],
                           "L": r - c, "S": -r - c})
        agg = df.group_by("giorno", "ora", "anno").agg(
            pl.len().alias("n"),
            *[e for lato in "LS" for e in (
                pl.col(lato).sum().alias(f"{lato}_som"),
                (pl.col(lato) ** 2).sum().alias(f"{lato}_q"),
                pl.col(lato).clip(lower_bound=0).sum().alias(f"{lato}_vinti"),
                (-pl.col(lato)).clip(lower_bound=0).sum().alias(f"{lato}_persi"),
            )],
        ).with_columns(pl.lit(durata, pl.Int32).alias("durata"))
        pezzi.append(agg)

    out = pl.concat(pezzi).sort("giorno", "ora", "durata", "anno")
    CARTELLA.mkdir(parents=True, exist_ok=True)
    out.write_parquet(_file(nome, minuti))
    return {"prodotto": nome, "barre": minuti, "ore_max": ore_max, "anni": list(SCOPERTA),
            "costi": prod.spread is not None, "righe": out.height,
            "celle": out.select("giorno", "ora", "durata").n_unique(), "file": str(_file(nome, minuti))}


def _carica(nome: str, minuti: int) -> pl.DataFrame:
    f = _file(nome, minuti)
    if not f.exists():
        calcola(nome, minuti)
    return pl.read_parquet(f)


def _statistiche(df: pl.DataFrame, lato: str) -> pl.DataFrame:
    """Statistiche per cella su tutti gli anni presenti in `df` (sempre e solo la scoperta)."""
    chiave = ["giorno", "ora", "durata"]
    anni = df.with_columns((pl.col(f"{lato}_som") / pl.col("n")).alias("m_anno"))
    rec = anni.filter(pl.col("anno").is_between(*RECENTE))
    return (anni.group_by(chiave).agg(
        pl.col("n").sum(), pl.col(f"{lato}_som").sum().alias("som"), pl.col(f"{lato}_q").sum().alias("q"),
        pl.col(f"{lato}_vinti").sum().alias("vinti"), pl.col(f"{lato}_persi").sum().alias("persi"),
        (pl.col("m_anno") > 0).mean().alias("anni_positivi"), pl.len().alias("anni"))
        .join(rec.group_by(chiave).agg((pl.col(f"{lato}_som").sum() / pl.col("n").sum()).alias("media_recente")),
              on=chiave, how="left")
        .with_columns((pl.col("som") / pl.col("n")).alias("media"))
        .with_columns(
            ((pl.col("q") / pl.col("n") - pl.col("media") ** 2) * pl.col("n") / (pl.col("n") - 1))
            .sqrt().alias("dev"),
            (pl.col("vinti") / pl.col("persi")).alias("pf"))
        .with_columns((pl.col("media") / pl.col("dev") * pl.col("n").sqrt()).alias("t")))


def _descrivi(r: dict, lato: str) -> dict:
    h, m = divmod(int(r["ora"]), 60)
    return {"lato": lato, "giorno": GIORNI[r["giorno"]], "ora": f"{h:02d}:{m:02d}",
            "durata_ore": round(r["durata"] / 60, 2), "n": r["n"], "anni": r["anni"],
            "media_esc": round(r["media"], 4), "t": round(r["t"], 2), "pf": round(r["pf"], 2),
            "anni_positivi": round(r["anni_positivi"], 2),
            "media_recente_esc": None if r["media_recente"] is None else round(r["media_recente"], 4)}


def migliori(nome: str, minuti: int = 60, k: int = 10, lati: str = "LS", n_min: int = 200,
             vicinanza_ore: float = 3.0) -> dict:
    """Le k celle migliori per lato, ordinate per t, tenendo solo la migliore di ogni gruppo di celle
    vicine (stesso giorno, ingresso e uscita entro `vicinanza_ore`): le vicine sono lo stesso effetto."""
    df = _carica(nome, minuti)
    out = {"prodotto": nome, "barre": minuti, "anni": list(SCOPERTA)}
    for lato in lati:
        st = _statistiche(df, lato).filter(pl.col("n") >= n_min, pl.col("dev") > 0)
        celle = st.height
        presi: list[dict] = []
        v = vicinanza_ore * 60
        for r in st.sort("t", descending=True).iter_rows(named=True):
            if any(p["giorno"] == r["giorno"] and abs(p["ora"] - r["ora"]) <= v
                   and abs(p["ora"] + p["durata"] - r["ora"] - r["durata"]) <= v for p in presi):
                continue
            presi.append(r)
            if len(presi) == k:
                break
        out["long" if lato == "L" else "short"] = {
            "celle_provate": celle,
            # massimo atteso di |t| fra celle indipendenti senza nessun effetto: le celle vicine sono
            # correlate, quindi è una soglia prudente (le prove indipendenti sono molte meno)
            "soglia_t_caso": round(math.sqrt(2 * math.log(max(celle, 2))), 2),
            "celle": [_descrivi(r, "long" if lato == "L" else "short") for r in presi],
        }
    return out


def cella(nome: str, minuti: int, giorno: str, ora: str, durata_ore: float) -> dict:
    df = _carica(nome, minuti)
    hh, mm = (int(x) for x in ora.split(":"))
    sel = df.filter(pl.col("giorno") == GIORNI.index(giorno), pl.col("ora") == hh * 60 + mm,
                    pl.col("durata") == round(durata_ore * 60))
    if not sel.height:
        return {"errore": "cella vuota: uscita fuori orario o durata non multipla delle barre"}
    out = {"prodotto": nome, "barre": minuti}
    for lato in "LS":
        r = _statistiche(sel, lato).row(0, named=True)
        out["long" if lato == "L" else "short"] = {
            **_descrivi(r, "long" if lato == "L" else "short"),
            "per_anno": {a: round(s / n, 3) for a, s, n in
                         sel.select("anno", f"{lato}_som", "n").sort("anno").iter_rows()},
        }
    return out
