"""Controlli del lettore. Uso: python -m motore.test_dati (dalla cartella del progetto)."""
from datetime import datetime, timedelta, timezone

import polars as pl

from . import dati
from .config import TAGLIO


def test_taglio_finto():
    # il controllo deve scattare su una serie che supera il taglio
    df = pl.DataFrame({"apre": [TAGLIO + timedelta(minutes=1)]})
    try:
        dati.controlla_taglio(df)
    except RuntimeError:
        return
    raise AssertionError("il controllo del taglio non scatta")


def test_lettura_e_barre():
    m1 = dati.carica_1m("FDAX")
    assert m1["apre"].max().astimezone(timezone.utc) < TAGLIO
    assert m1["apre"].is_sorted() and m1["apre"].n_unique() == m1.height
    h1 = dati.aggrega(m1, 60)
    # coerenza OHLC e ora italiana: fino al 2015 l'FDAX apriva alle 08:00 italiane
    # (la sessione notturna Eurex dall'01:10 c'è dalla fine del 2018)
    assert (h1["h"] >= h1[["o", "c"]].max_horizontal()).all()
    assert (h1["l"] <= h1[["o", "c"]].min_horizontal()).all()
    vecchi = h1.filter(pl.col("apre").dt.year().is_between(2010, 2015))
    assert vecchi["apre"].dt.hour().min() == 8, vecchi["apre"].dt.hour().min()
    assert (h1["apre"].dt.minute() == 0).all()
    g = dati.aggrega(m1, 1440)
    assert (g["apre"].dt.hour() == 0).all()


def test_cross():
    x = dati.aggrega(dati.cross("AD", "JY", 100.0).filter(
        pl.col("apre").dt.year() == 2012), 1440)
    # AUDJPY nel 2012 stava tra circa 72 e 91 (prezzi rettificati: tolleranza larga)
    assert 55 < x["c"].median() < 110, x["c"].median()


if __name__ == "__main__":
    for f in (test_taglio_finto, test_lettura_e_barre, test_cross):
        f()
        print("ok", f.__name__)
