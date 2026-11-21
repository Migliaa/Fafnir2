"""Lettura dei futures a 1 minuto, con il taglio del fuori campione, e aggregazione in barre.

Convenzioni
- `apre` / `chiude`: inizio e fine della barra in ora italiana (tz-aware). ProRealTime chiama
  `Time` l'ora di chiusura della barra: per tradurre una logica si usa `chiude`.
- I prezzi sono futures continui rettificati ai rinnovi: differenze giuste, livelli no.
  Non calcolare mai grandezze in % del prezzo; usare punti o escursioni medie.
- Il giorno di trading è il giorno di calendario italiano (00:00-24:00), che per i futures CME
  coincide quasi con la sessione Globex (apre alle 00:00 italiane); il catalogo potrà cambiarlo.
"""
from __future__ import annotations

from pathlib import Path

import polars as pl

from .config import CACHE, DATI_1M, FUSO, TAGLIO

COLONNE = ["apre", "o", "h", "l", "c", "v"]


def simboli() -> list[str]:
    return sorted(p.name for p in DATI_1M.iterdir() if p.is_dir())


def _file_ammessi(simbolo: str) -> list[Path]:
    # i file sono per anno: quelli interamente oltre il taglio non si aprono nemmeno
    return sorted(p for p in (DATI_1M / simbolo).glob("*.parquet") if int(p.stem) <= TAGLIO.year)


def carica_1m(simbolo: str) -> pl.DataFrame:
    """Barre da 1 minuto in ora italiana, solo prima del taglio (filtro applicato in lettura)."""
    file = _file_ammessi(simbolo)
    if not file:
        raise FileNotFoundError(simbolo)
    df = (
        pl.scan_parquet(file)
        .filter(pl.col("ts") < TAGLIO)
        .select(
            pl.col("ts").dt.convert_time_zone(FUSO).alias("apre"),
            pl.col("open").alias("o"), pl.col("high").alias("h"),
            pl.col("low").alias("l"), pl.col("close").alias("c"),
            pl.col("volume").alias("v"),
        )
        .sort("apre")
        .unique(subset="apre", keep="last", maintain_order=True)
        .collect()
    )
    controlla_taglio(df)
    return df


def controlla_taglio(df: pl.DataFrame) -> None:
    if df.height and df["apre"].max().astimezone(TAGLIO.tzinfo) >= TAGLIO:
        raise RuntimeError("dati oltre il taglio del fuori campione")


def cross(num: str, den: str, scala: float = 1.0) -> pl.DataFrame:
    """Cross sintetico num/den (es. AUDJPY = AD / JY * 100) sui minuti presenti in entrambi.
    Massimo e minimo del rapporto sono approssimati tenendo il denominatore fermo nel minuto
    (vale al minuto; aggregando in barre più lunghe l'errore diventa trascurabile)."""
    a, b = carica_1m(num), carica_1m(den)
    j = a.join(b, on="apre", suffix="_d")
    o = pl.col("o") / pl.col("o_d") * scala
    c = pl.col("c") / pl.col("c_d") * scala
    alti = [o, c, pl.col("h") / pl.col("o_d") * scala, pl.col("h") / pl.col("c_d") * scala]
    bassi = [o, c, pl.col("l") / pl.col("o_d") * scala, pl.col("l") / pl.col("c_d") * scala]
    return j.select(
        "apre", o.alias("o"), pl.max_horizontal(alti).alias("h"),
        pl.min_horizontal(bassi).alias("l"), c.alias("c"), (pl.col("v") + pl.col("v_d")).alias("v"),
    )


CROSS = {  # nome: (numeratore, denominatore, scala)
    "AUDJPY": ("AD", "JY", 100.0), "GBPJPY": ("BP", "JY", 100.0), "EURJPY": ("EC", "JY", 100.0),
    "CADJPY": ("CD", "JY", 100.0), "NZDJPY": ("NE1", "JY", 100.0), "CHFJPY": ("SF", "JY", 100.0),
    "EURGBP": ("EC", "BP", 1.0), "EURCHF": ("EC", "SF", 1.0), "AUDUSD": ("AD", None, 1.0),
}


def _sorgente(nome: str) -> pl.DataFrame:
    if nome in CROSS and CROSS[nome][1] is not None:
        n, d, s = CROSS[nome]
        return cross(n, d, s)
    if nome in CROSS:
        return carica_1m(CROSS[nome][0])
    return carica_1m(nome)


def aggrega(df1m: pl.DataFrame, minuti: int) -> pl.DataFrame:
    """Barre da `minuti` allineate alla mezzanotte italiana; `minuti=1440` dà le barre giornaliere."""
    passo = "1d" if minuti >= 1440 else f"{minuti}m"
    out = (
        df1m.group_by_dynamic("apre", every=passo, closed="left", label="left")
        .agg(pl.col("o").first(), pl.col("h").max(), pl.col("l").min(),
             pl.col("c").last(), pl.col("v").sum(), pl.len().alias("minuti"))
    )
    return out.with_columns((pl.col("apre") + pl.duration(minutes=minuti)).alias("chiude"))


def barre(nome: str, minuti: int, cache: bool = True) -> pl.DataFrame:
    """Barre di un simbolo o di un cross sintetico, con cache su disco (Dati/_cache)."""
    file = CACHE / f"{nome}_{minuti}m_{TAGLIO:%Y%m%d}.parquet"
    if cache and file.exists():
        df = pl.read_parquet(file)
    else:
        df = aggrega(_sorgente(nome), minuti)
        if cache:
            CACHE.mkdir(parents=True, exist_ok=True)
            df.write_parquet(file)
    controlla_taglio(df)
    return df
