"""Protocollo ad albero: porte come rapporti, strato differenziale, filtri casuali, scelta fra fratelli, walk-forward,
budget e lancio una volta sola. Uso: python -m motore.test_albero"""
import json
import math
from datetime import datetime, timedelta

import numpy as np
import polars as pl

from . import albero as A
from . import validazione
from .config import SCOPERTA
from .test_esperimento import _Ambiente


def _ctx(euro_esc=100.0, ep=1.0):
    """Contesto senza dati: 10 anni di giorni feriali, nessuna deriva."""
    c = A.Contesto.__new__(A.Contesto)
    c.anni = list(range(SCOPERTA[0], SCOPERTA[1] + 1))
    c.n_anni = len(c.anni)
    c.date = np.array([d for d in np.arange(np.datetime64(f"{SCOPERTA[0]}-01-01"), np.datetime64(f"{SCOPERTA[1] + 1}-01-01"))
                       if d.astype(datetime).weekday() < 5])
    c.ep, c.euro_esc, c.esc_oggi = ep, euro_esc, euro_esc / ep
    c.ret_giorno = np.zeros(len(c.date))
    c.deriva_ora = 0.0
    c.rng = np.random.default_rng(0)
    c._rif = {}
    return c


def _trade(netti, giorni, ore=4.0, lordo=None):
    """Tabella di trade: uno per giorno della lista, ingresso alle 10:00, durata `ore`."""
    ing = [datetime.combine(d.astype(datetime), datetime.min.time()) + timedelta(hours=10) for d in giorni]
    netti = np.asarray(netti, float)
    return pl.DataFrame({"ingresso": ing, "uscita": [i + timedelta(hours=ore) for i in ing], "barre": [1] * len(ing),
                         "lordo": netti + 0.01 if lordo is None else lordo, "netto": netti, "punti": netti * 100.0,
                         "costo": [1.0] * len(ing)})


def test_porte_come_rapporti():
    c = _ctx(euro_esc=100.0)
    giorni = c.date[::10]                     # circa 26 trade l'anno
    n = len(giorni)
    x = np.where(np.arange(n) % 2 == 0, 0.5, -0.1)   # media 0,2 escursioni = 20 € di oggi, durata 4 ore
    m = A.misure(c, _trade(x, giorni))
    assert abs(m["euro_oggi"] - 100.0 * x.mean()) < 1e-9 and m["richiesto"] == 20.0
    assert abs(m["G"] - m["euro_oggi"] / 20.0) < 1e-12
    assert abs(m["M"] - m["euro_oggi"] * m["trade_anno"] / (12 * 20.0)) < 1e-12
    # trade necessari perché t >= 2: (2 sd / media)^2
    assert m["n_necessari"] == math.ceil((2 * x.std(ddof=1) / x.mean()) ** 2)
    # durata oltre 36 ore: la soglia sale a 30 € e G scende
    m2 = A.misure(c, _trade(x, giorni, ore=40.0))
    assert m2["richiesto"] == 30.0 and m2["G"] < m["G"]
    # pronto o con margine: un sistema da 4 € a trade e 26 trade l'anno ha M < 1,5 e viene scartato
    p = A.porte_radice({"G": 0.2, "M": 0.43, "t": 3.0, "trade_anno": 26}, {"mediana": 0.1})
    assert p[0]["esito"] == "rosso" and A._passa(p) is False
    assert A._passa(A.porte_radice({"G": 0.5, "M": 1.6, "t": 3.0, "trade_anno": 26}, {"mediana": 0.1}))
    assert A._passa(A.porte_radice({"G": 1.1, "M": 1.0, "t": 2.0, "trade_anno": 6}, {"mediana": 0.1}))     # pronto con pochi trade
    assert not A._passa(A.porte_radice({"G": 1.1, "M": 1.0, "t": 1.9, "trade_anno": 6}, {"mediana": 0.1}))
    assert not A._passa(A.porte_radice({"G": 1.1, "M": 1.0, "t": 3.0, "trade_anno": 5.9}, {"mediana": 0.1}))


def test_strato_differenziale():
    c = _ctx()
    rng = np.random.default_rng(1)
    giorni = c.date
    r = rng.normal(0.02, 0.3, len(giorni))           # la finestra guadagna 0,02 in tutti i giorni
    finestra = _trade(r, giorni, lordo=r)
    regola = {"lato": 1, "cond": [["x", ">", 0]]}
    c._rif[json.dumps({"lato": 1}, sort_keys=True)] = finestra
    # sottoinsieme casuale: nessun segnale isolato
    casuale = finestra.sample(n=500, seed=3).sort("ingresso")
    d = A.differenziale(c, regola, casuale, 1)
    assert abs(d["D2"]) < 3 * 0.3 / math.sqrt(500) and abs(d["t_D2"]) < 3 and 0.01 < d["D3_quantile"] < 0.99, d
    # sottoinsieme dei giorni migliori: segnale isolato grande, oltre tutti i sottoinsiemi casuali
    buoni = finestra.filter(pl.col("lordo") > 0.2)
    d = A.differenziale(c, regola, buoni, 1)
    assert d["D2"] > 0.3 and d["t_D2"] > 10 and d["D3_quantile"] == 1.0 and d["quota_D2"] > 0.5, d
    assert A._passa(A.porte_differenziale(d))
    # il sistema guadagna solo quanto la finestra: D2 vicino a zero, la porta non passa
    d = A.differenziale(c, regola, casuale.with_columns(pl.lit(0.02).alias("lordo")), 1)
    assert not A._passa(A.porte_differenziale(d))
    # il sistema è la finestra intera: D2 è zero per costruzione e la porta passa a D1 (deriva)
    d = A.differenziale(c, regola, finestra, 1)
    assert d["D2"] == 0 and d["D3_quantile"] is None
    p = A.porte_differenziale(d)
    assert p[0]["nome"].startswith("Segnale meno la deriva") and A._passa(p)        # deriva nulla: tutto è segnale
    c.deriva_ora = 0.004                       # 4 ore di deriva valgono 0,016 dei 0,02 del lordo: resta meno di metà
    assert not A._passa(A.porte_differenziale(A.differenziale(c, regola, finestra, 1)))
    c.deriva_ora = 0.0
    # deriva: con 0,005 escursioni l'ora un trade di 4 ore deve 0,02 alla deriva
    c.deriva_ora = 0.005
    d = A.differenziale(c, regola, casuale, 1)
    assert abs(d["D1"] - (casuale["lordo"].mean() - 0.02)) < 1e-9


def test_filtri_casuali_e_resto():
    c = _ctx()
    rng = np.random.default_rng(2)
    padre = _trade(rng.normal(0.0, 1.0, 1000), c.date[:1000])
    migliori = padre.sort("netto").tail(300).sort("ingresso")
    fc = A.filtri_casuali(c, migliori, padre)
    assert fc["quantile"] == 1.0 and fc["resto_media"] < migliori["netto"].mean() and abs(fc["quota_tenuta"] - 0.3) < 1e-9
    a_caso = [A.filtri_casuali(c, padre.sample(n=300, seed=s).sort("ingresso"), padre)["quantile"] for s in range(40)]
    assert 0.2 < np.mean(a_caso) < 0.8, a_caso                       # un filtro a caso sta in mezzo


def test_scelta_fra_fratelli_e_walk_forward_senza_futuro():
    c = _ctx()
    anni = np.array(c.anni)
    # A buono in tutti gli anni, B buono solo dal 2019 in poi, C cattivo
    def ann(medie, n=50, sd=0.5):
        return np.array([[n, m * n, n * (sd ** 2 + m * m)] for m in medie])
    a = ann([0.1] * 10)
    b = ann([-0.1] * 5 + [0.5] * 5)
    cc = ann([-0.1] * 10)
    s = A.scelta_fratelli(c, [a, b, cc])
    assert s["n"] == 45 and s["scelte"][2] == 0 and sum(s["scelte"]) == 45, s
    # walk-forward: la procedura per l'anno y vede solo gli anni prima di y
    al = A.Albero.__new__(A.Albero)
    al.ctx = c
    rad = {"id": "r", "genitore": None, "livello": "L0", "etichetta": "radice"}
    fa = {"id": "fa", "genitore": "r", "livello": "L2", "etichetta": "A"}
    fb = {"id": "fb", "genitore": "r", "livello": "L2", "etichetta": "B"}
    al.nodi = [rad, fa, fb]
    al._ann = {"r": ann([0.0] * 10), "fa": a, "fb": b}
    wf = al.walkforward(rad)
    scelti = {r["anno"]: r["etichetta"] for r in wf["anni"]}
    assert min(scelti) == 2017 and scelti[2017] == "A" and scelti[2019] == "A", scelti   # B non si vede prima del 2019
    assert scelti[2023] == "B", scelti                                                 # con abbastanza anni buoni nel passato B supera A
    # un ramo che guadagna tantissimo solo nel 2020: nel 2020 la procedura non può sceglierlo, dal 2021 sì
    fc = {"id": "fc", "genitore": "r", "livello": "L2", "etichetta": "C"}
    al.nodi = [rad, fa, fc]
    al._ann = {"r": ann([0.0] * 10), "fa": a, "fc": ann([-0.05] * 6 + [2.0] + [-0.05] * 3)}
    scelti_c = {r["anno"]: r["etichetta"] for r in al.walkforward(rad)["anni"]}
    assert scelti_c[2020] == "A" and scelti_c[2021] == "C", scelti_c
    al.nodi, al._ann = [rad, fa, fb], {"r": ann([0.0] * 10), "fa": a, "fb": b}
    # il risultato di ogni anno è quello del nodo scelto in quell'anno
    assert all(abs(r["media_esc"] - (0.1 if r["etichetta"] == "A" else (0.5 if r["anno"] >= 2019 else -0.1))) < 1e-9 for r in wf["anni"])


def test_stop_dalla_escursione_contraria():
    c = _ctx()
    # tabella finta: per ogni trade l'ingresso a 100, il minimo a 100 - mae, esc = 10
    n = 40
    mae = np.r_[np.full(30, 2.0), np.full(10, 9.0)]                   # vincenti fino a 0,2 escursioni contro
    apre = [datetime(2020, 1, 1) + timedelta(hours=i) for i in range(3 * n + 1)]
    o = np.full(len(apre), 100.0)
    l, h = o.copy(), o.copy()
    for k in range(n):
        l[3 * k + 1] = 100 - mae[k]
    c.tab = pl.DataFrame({"apre": apre, "o": o, "h": h, "l": l, "esc": np.full(len(apre), 10.0)})
    tr = pl.DataFrame({"ingresso": [apre[3 * k + 1] for k in range(n)], "uscita": [apre[3 * k + 3] for k in range(n)],
                       "lordo": np.r_[np.full(30, 0.1), np.full(10, -0.5)]})
    m, _ = A.escursioni_trade(c, tr, 1)
    assert np.allclose(m, mae / 10)
    assert A.stop_da_mae(c, tr, 1) == 0.25             # 90° percentile dei vincenti 0,2 -> primo valore tondo 0,25


SPEC = {"tipo": "albero", "nome": "prova-albero", "ipotesi": "rialzo fra le 09 e le 10", "prodotto": "KW", "barre": 60,
        "budget": 6, "max_condizioni": 2, "rami_per_livello": 2, "foglie_per_radice": 1,
        "radici": [{"nome": "r1", "regola": {"lato": 1, "da": "09:00", "a": "09:00", "uscita": {"barre": 0}, "max_al_giorno": 1}}],
        "ingressi": [{"nome": "gap", "grandezza": "gap", "op": ">=", "soglie": [0, 0.1, 0.2], "meccanismo": "m", "direzione": "d"},
                     {"nome": "rsi", "grandezza": "rsi:2", "op": ">=", "soglie": [50, 70], "meccanismo": "m", "direzione": "d"}],
        "uscite": [{"nome": "due barre", "uscita": {"barre": 1}}]}


def test_lancio_rispetta_il_budget_registra_e_non_si_ripete():
    with _Ambiente() as tmp:
        A.CARTELLA = tmp / "alberi"
        vecchi = (A.M_MIN, A.D2_QUOTA_LORDO, A.SCOPERTA)
        A.M_MIN, A.D2_QUOTA_LORDO = 0.0, -1e9            # dati finti: tre anni (2014-2016), vantaggio piccolo
        A.SCOPERTA = (2014, 2016)
        try:
            f = tmp / "a.json"
            f.write_text(json.dumps(SPEC), encoding="utf-8")
            assert A.controlla(f)["ok"]
            r = A.lancia(f, log=lambda *a: None)
            assert r["prove"] <= 6 and r["budget_esaurito"], (r["prove"], r["budget_esaurito"])
            assert len(r["nodi"]) == r["prove"]
            fam = [x for x in validazione._righe() if x["famiglia"] == "albero:prova-albero"]
            assert len(fam) == r["prove"]
            salvato = json.loads((tmp / "alberi" / "prova-albero" / "albero.json").read_text(encoding="utf-8"))
            assert salvato["nodi"][0]["livello"] == "L0" and all(n["registro"] for n in salvato["nodi"])
            try:
                A.lancia(f, log=lambda *a: None)
            except ValueError as ex:
                assert "già lanciato" in str(ex)
            else:
                raise AssertionError("albero rilanciato")
            bad = dict(SPEC, tipo="esperimento", ingressi=[{"nome": "x", "grandezza": "boh", "op": ">", "soglie": [1]}])
            f.write_text(json.dumps(bad), encoding="utf-8")
            r = A.controlla(f)
            assert not r["ok"] and any("tipo" in e for e in r["errori"]) and any("boh" in e for e in r["errori"]), r
        finally:
            A.M_MIN, A.D2_QUOTA_LORDO, A.SCOPERTA = vecchi


if __name__ == "__main__":
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            fn()
            print("ok", nome)
