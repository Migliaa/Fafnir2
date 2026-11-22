"""Controlli del motore degli eventi su barre finte dal risultato noto. Uso: python -m motore.test_eventi"""
from datetime import datetime, timedelta

import polars as pl

from .motori import eventi


def _tabella(giorni=25):
    # barre orarie 24 ore su 24; il prezzo sale di 1 a ogni barra; escursione giornaliera 10
    t = pl.datetime_range(datetime(2015, 1, 5), datetime(2015, 1, 5 + giorni), "1h",
                          time_zone="Europe/Rome", eager=True, closed="left")
    n = len(t)
    df = pl.DataFrame({"apre": t, "o": [float(i) for i in range(n)]}).with_columns(
        (pl.col("apre") + pl.duration(hours=1)).alias("chiude"),
        (pl.col("o") + 0.5).alias("h"), (pl.col("o") - 0.5).alias("l"), (pl.col("o") + 1).alias("c"),
        pl.lit(10.0).alias("esc"), pl.col("apre").dt.date().alias("data"))
    return df.with_columns(
        pl.col("chiude").dt.weekday().alias("giorno"),
        (pl.col("chiude").dt.hour().cast(pl.Int32) * 60 + pl.col("chiude").dt.minute().cast(pl.Int32)).alias("tod"),
        pl.col("data").cast(pl.Int32).alias("dn"))


def test_uscita_a_barre_e_una_posizione_alla_volta():
    b = _tabella()
    r, tr = eventi.prova("KW", 60, {"lato": 1, "uscita": {"barre": 2}, "max_al_giorno": 99}, b)
    # barindex - tradeindex > 2: si esce all'apertura della quarta barra dopo l'ingresso
    assert (tr["lordo"] - 0.4).abs().max() < 1e-12, tr.head()
    assert (tr["barre"] == 4).all()
    assert (tr["ingresso"].diff().drop_nulls() >= timedelta(hours=4)).all()  # mai sovrapposti
    r, tr = eventi.prova("KW", 60, {"lato": -1, "uscita": {"barre": 2}, "max_al_giorno": 99}, b)
    assert (tr["lordo"] + 0.4).abs().max() < 1e-12


def test_orari_giorni_e_uscita_a_ora():
    b = _tabella()
    regola = {"lato": 1, "giorni": [1], "da": "13:30", "a": "13:30", "uscita": {"ora": "08:00"}}
    _, tr = eventi.prova("KW", 60, regola, b)
    assert tr.height == 0  # nessuna barra oraria chiude alle 13:30
    regola.update(da="14:00", a="14:00")
    _, tr = eventi.prova("KW", 60, regola, b)
    assert (tr["ingresso"].dt.weekday() == 1).all() and (tr["ingresso"].dt.hour() == 14).all()
    # decisione alla chiusura delle 08:00 del martedì, uscita all'apertura delle 08:00
    assert (tr["uscita"].dt.hour() == 8).all() and (tr["uscita"].dt.weekday() == 2).all()
    assert (tr["lordo"] - 1.8).abs().max() < 1e-12


def test_stop_e_condizioni():
    b = _tabella()
    _, tr = eventi.prova("KW", 60, {"lato": -1, "da": "10:00", "a": "10:00", "stop": 0.1,
                                     "uscita": {"barre": 5}}, b)
    assert (tr["lordo"] + 0.1).abs().max() < 1e-12 and (tr["barre"] == 1).all()
    # prezzo sempre sopra la media: la condizione long passa, quella speculare dello short no
    lunga = {"lato": 1, "da": "10:00", "a": "10:00", "cond": [["dist_media:5", ">", 0]], "uscita": {"barre": 1}}
    assert eventi.prova("KW", 60, lunga, b)[1].height > 20
    assert eventi.prova("KW", 60, {**lunga, "lato": -1}, b)[1].height == 0


if __name__ == "__main__":
    for f in (test_uscita_a_barre_e_una_posizione_alla_volta, test_orari_giorni_e_uscita_a_ora, test_stop_e_condizioni):
        f()
        print("ok", f.__name__)
