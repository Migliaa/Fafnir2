"""Controlli del backtest al minuto su mercati finti dal risultato noto. Uso: python -m motore.test_backtest"""
from datetime import datetime

import numpy as np
import polars as pl

from . import dati
from .motori import backtest, eventi

GIORNI = 4          # da lunedì 5 gennaio 2015
INGRESSO = 540      # minuto 09:00 del primo giorno: apertura della barra d'ingresso
REGOLA = {"lato": 1, "da": "09:00", "a": "09:00", "uscita": {"barre": 2}, "max_al_giorno": 1}


def _minuti(o, h, l, c):
    t = pl.datetime_range(datetime(2015, 1, 5), datetime(2015, 1, 5 + GIORNI), "1m",
                          time_zone="Europe/Rome", eager=True, closed="left")
    return pl.DataFrame({"apre": t, "o": o, "h": h, "l": l, "c": c, "v": np.ones(len(t))})


def _mercato(pista):
    """Prezzo fermo a 100; dal minuto d'ingresso del primo giorno i minuti `(o, h, l, c)` della pista,
    poi fermo all'ultima chiusura fino a fine giornata."""
    n = GIORNI * 1440
    o, h, l, c = (np.full(n, 100.0) for _ in range(4))
    for k, (a, b, d, e) in enumerate(pista):
        o[INGRESSO + k], h[INGRESSO + k], l[INGRESSO + k], c[INGRESSO + k] = a, b, d, e
    for x in (o, h, l, c):
        x[INGRESSO + len(pista):1440] = pista[-1][3]
    return _minuti(o, h, l, c)


def _pista(chiusure, prima=100.0):
    """Pista continua: ogni minuto apre alla chiusura del precedente."""
    out, p = [], prima
    for x in chiusure:
        out.append((p, max(p, x), min(p, x), x))
        p = x
    return out


def _tabella(m1):
    df = dati.aggrega(m1, 60).with_columns(pl.lit(10.0).alias("esc"), pl.col("apre").dt.date().alias("data"))
    return df.with_columns(
        pl.col("chiude").dt.weekday().alias("giorno"),
        (pl.col("chiude").dt.hour().cast(pl.Int32) * 60 + pl.col("chiude").dt.minute().cast(pl.Int32)).alias("tod"),
        pl.col("data").cast(pl.Int32).alias("dn"))


def _primo(regola, m1, nome="KW"):
    _, tr = backtest.simula(nome, 60, regola, _tabella(m1), m1)
    return tr.row(0, named=True)


def test_senza_stop_stessi_trade_di_eventi():
    rng = np.random.default_rng(3)
    n = 10 * 1440
    c = 100 + np.cumsum(rng.normal(0, 0.3, n))
    o = np.concatenate([[100.0], c[:-1]])
    t = pl.datetime_range(datetime(2015, 1, 5), datetime(2015, 1, 15), "1m", time_zone="Europe/Rome",
                          eager=True, closed="left")
    m1 = pl.DataFrame({"apre": t, "o": o, "h": np.maximum(o, c) + 0.1, "l": np.minimum(o, c) - 0.1,
                       "c": c, "v": np.ones(n)})
    b = _tabella(m1)
    for lato in (1, -1):
        regola = {"lato": lato, "da": "07:00", "a": "15:00", "uscita": {"barre": 3, "ora": "21:00"}, "max_al_giorno": 2}
        r1, t1 = eventi.prova("FDAX", 60, regola, b)
        r2, t2 = backtest.simula("FDAX", 60, regola, b, m1)
        assert t1.height > 8, t1.height
        for col in ("ingresso", "uscita", "barre", "lordo", "netto"):
            assert t1[col].to_list() == t2[col].to_list(), col
        assert set(t2["motivo"]) == {"tempo"}
        assert r1 == r2


def test_stop_nel_primo_minuto_con_target_alla_chiusura():
    # il primo minuto scende fino a 98,9 (stop a 99), poi la barra sale oltre il target (102)
    pista = [(100.0, 100.2, 98.9, 100.1)] + _pista([101, 102.5, 102.5], 100.1)
    t = _primo({**REGOLA, "stop": 0.1, "target": 0.2}, _mercato(pista))
    assert t["motivo"] == "stop" and abs(t["lordo"] + 0.1) < 1e-9, t


def test_target_prima_dello_stop_nella_stessa_barra():
    # nella barra oraria toccati entrambi: prima sale a 101,5 (target a 101), poi scende a 98 (stop a 98,5)
    sale = [100 + 0.1 * k for k in range(1, 16)]
    scende = [101.5 - 0.1 * k for k in range(1, 36)]
    m1 = _mercato(_pista(sale + scende))
    regola = {**REGOLA, "stop": 0.15, "target": 0.1}
    t = _primo(regola, m1)
    assert t["motivo"] == "target" and abs(t["lordo"] - 0.1) < 1e-9, t
    _, tr = eventi.prova("KW", 60, regola, _tabella(m1))
    assert abs(tr["lordo"][0] + 0.15) < 1e-9          # sulle sole barre vince lo stop


def test_pareggio():
    # guadagno di 1 punto (attiva 0,1), poi ritorno sotto l'ingresso: esce a ingresso + 0,2 punti
    sale = [100 + 0.1 * k for k in range(1, 16)]
    scende = [101.5 - 0.1 * k for k in range(1, 31)]
    m1 = _mercato(_pista(sale + scende))
    t = _primo({**REGOLA, "pareggio": {"attiva": 0.1, "a": 0.02}}, m1)
    assert t["motivo"] == "pareggio" and abs(t["lordo"] - 0.02) < 1e-9, t
    # senza pareggio il trade resta aperto fino all'uscita a tempo, in perdita
    t = _primo(REGOLA, m1)
    assert t["motivo"] == "tempo" and t["lordo"] < -0.1, t
    # lato short: specchio esatto
    m_s = _mercato(_pista([100 - 0.1 * k for k in range(1, 16)] + [98.5 + 0.1 * k for k in range(1, 31)]))
    t = _primo({**REGOLA, "lato": -1, "pareggio": {"attiva": 0.1, "a": 0.02}}, m_s)
    assert t["motivo"] == "pareggio" and abs(t["lordo"] - 0.02) < 1e-9, t


def test_apertura_oltre_lo_stop():
    # il minuto 09:30 apre a 97, oltre lo stop (99): si esce all'apertura, non al livello
    pista = _pista([100.0] * 30) + [(97.0, 97.5, 96.5, 97.0)]
    t = _primo({**REGOLA, "stop": 0.1}, _mercato(pista))
    assert t["motivo"] == "stop" and abs(t["lordo"] + 0.3) < 1e-9, t
    assert t["uscita"].minute == 30 and t["uscita"].hour == 9
    # lo stesso per un target oltrepassato in apertura
    pista = _pista([100.0] * 30) + [(103.0, 103.5, 102.5, 103.0)]
    t = _primo({**REGOLA, "target": 0.1}, _mercato(pista))
    assert t["motivo"] == "target" and abs(t["lordo"] - 0.3) < 1e-9, t


def test_stop_e_target_nello_stesso_minuto():
    # un solo minuto tocca sia lo stop (99) sia il target (101): vince lo stop
    pista = _pista([100.0] * 10) + [(100.0, 101.5, 98.5, 100.0)]
    t = _primo({**REGOLA, "stop": 0.1, "target": 0.1}, _mercato(pista))
    assert t["motivo"] == "stop" and abs(t["lordo"] + 0.1) < 1e-9, t


if __name__ == "__main__":
    for f in (test_senza_stop_stessi_trade_di_eventi, test_stop_nel_primo_minuto_con_target_alla_chiusura,
              test_target_prima_dello_stop_nella_stessa_barra, test_pareggio, test_apertura_oltre_lo_stop,
              test_stop_e_target_nello_stesso_minuto):
        f()
        print("ok", f.__name__)
