"""Controlli della mappa su dati finti dal risultato noto. Uso: python -m motore.test_mappa"""
import tempfile
from datetime import datetime
from pathlib import Path

import polars as pl

from . import dati
from .motori import mappa


def _finte(nome, minuti, cache=True):
    # prezzo = ore di orologio dall'inizio, quindi il rendimento di una cella è la sua durata in ore;
    # escursione giornaliera costante 10; barre solo dal lunedì al venerdì
    ore = pl.datetime_range(datetime(2014, 1, 6), datetime(2015, 12, 31, 23), "1h",
                            time_zone="Europe/Rome", eager=True)
    df = pl.DataFrame({"apre": ore}).filter(pl.col("apre").dt.weekday() <= 5)
    df = df.with_columns(((pl.col("apre").dt.replace_time_zone(None) - datetime(2014, 1, 6))
                          .dt.total_hours().cast(pl.Float64)).alias("o"))
    if minuti == 1440:
        df = df.filter(pl.col("apre").dt.hour() == 0)
        return df.with_columns(pl.col("o").alias("l"), (pl.col("o") + 10).alias("h"))
    return df


def test_mappa_su_dati_finti():
    vero, cartella = dati.barre, mappa.CARTELLA
    dati.barre, mappa.CARTELLA = _finte, Path(tempfile.mkdtemp())
    try:
        mappa.calcola("KW", 60, 72)  # KW non ha costi nel catalogo: rendimento lordo
        c = mappa.cella("KW", 60, "lun", "03:00", 67)
        assert abs(c["long"]["media_esc"] - 6.7) < 1e-9, c
        assert abs(c["short"]["media_esc"] + 6.7) < 1e-9, c
        assert c["long"]["anni"] == 2 and c["long"]["n"] >= 95, c
        assert "errore" in mappa.cella("KW", 60, "ven", "20:00", 48)  # uscita di domenica
        assert "errore" in mappa.cella("KW", 60, "ven", "20:00", 48.5)
    finally:
        dati.barre, mappa.CARTELLA = vero, cartella


if __name__ == "__main__":
    test_mappa_su_dati_finti()
    print("ok test_mappa_su_dati_finti")
