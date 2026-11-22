"""Controlli delle metriche su dati finti dal risultato noto. Uso: python -m motore.test_metriche"""
import math

import numpy as np

from . import metriche as M


def _rumore(n, media=0.0, sd=1.0, seed=0):
    return np.random.default_rng(seed).normal(media, sd, n)


def _ar1(n, phi, media=0.05, seed=0):
    e = np.random.default_rng(seed).normal(0, 1, n)
    x = np.empty(n)
    x[0] = e[0]
    for t in range(1, n):
        x[t] = phi * x[t - 1] + e[t]
    return x + media


def test_sharpe_costante_piu_rumore():
    # serie alternata media +- 1: media e deviazione standard note
    g = np.tile([1.1, 0.9], 500)
    atteso = 1.0 / (0.1 * math.sqrt(1000 / 999)) * math.sqrt(252)
    assert abs(M.sharpe(g) - atteso) < 1e-9, M.sharpe(g)
    assert abs(M.sharpe(2 * g) - M.sharpe(g)) < 1e-9  # indipendente dalla scala
    assert M.sharpe(np.zeros(10)) != M.sharpe(np.zeros(10))  # nan, non zero né errore


def test_sharpe_lo():
    iid = _rumore(5000, 0.05, seed=3)
    r = M.sharpe_lo(iid) / M.sharpe(iid)
    assert abs(r - 1) < 0.08, r  # su rumore indipendente coincide con lo Sharpe semplice
    ar = _ar1(5000, 0.3)
    r = M.sharpe_lo(ar) / M.sharpe(ar)
    assert 0.65 < r < 0.85, r  # teoria: 1/sqrt(1 + 2*0.3/0.7) = 0.73
    assert abs(M.sharpe_lo(ar, q=0) - M.sharpe(ar)) < 1e-9


def test_psr_dsr():
    g = _rumore(2000, 0.08, seed=1)
    assert abs(M.psr(g, M.sharpe(g)) - 0.5) < 1e-9
    assert M.psr(g, 0.0) > 0.95 and M.psr(g, 5.0) < 0.05
    v = [M.dsr(g, n, 0.25) for n in (1, 2, 10, 100, 1000)]
    assert all(a > b for a, b in zip(v, v[1:])), v
    assert abs(v[0] - M.psr(g, 0.0)) < 1e-12  # una prova sola: nessuna deflazione
    assert M.sr_atteso_massimo(1, 1.0) == 0.0 and M.sr_atteso_massimo(100, 0.25) > M.sr_atteso_massimo(10, 0.25) > 0


def test_min_btl():
    assert abs(M.prove_ammesse(13, 0.7) - 24.2) < 0.1, M.prove_ammesse(13, 0.7)
    assert abs(M.prove_ammesse(6, 1.0) - 20.1) < 0.1, M.prove_ammesse(6, 1.0)
    assert abs(M.min_btl(M.prove_ammesse(13, 0.7), 0.7) - 13) < 1e-9  # una è l'inversa dell'altra


def test_regolarita_curva_a_mano():
    # curva 2,1,0,1,4,2,2,2,6: drawdown 0,-1,-2,-1,0,-2,-2,-2,0
    g = np.array([2, -1, -1, 1, 3, -2, 0, 0, 4], dtype=float)
    d = M.drawdown(g)
    assert d["massimo"] == 2 and d["durata_max"] == 3, d
    assert abs(d["quota_sott_acqua"] - 6 / 9) < 1e-12, d
    assert abs(M.ulcer(g) - math.sqrt(2)) < 1e-12, M.ulcer(g)
    # una retta ha R^2 = 1 e nessun drawdown
    retta = np.ones(100)
    assert abs(M.r2(retta) - 1) < 1e-12 and M.drawdown(retta)["massimo"] == 0
    # drawdown che parte subito, prima di qualunque massimo
    assert M.drawdown(np.array([-1.0, -1.0, 3.0]))["massimo"] == 2


def test_k_ratio_e_pendenze():
    rng = np.random.default_rng(2)
    liscia = 1 + rng.normal(0, 0.2, 1000)
    rumorosa = 1 + rng.normal(0, 10, 1000)
    assert M.k_ratio(liscia) > M.k_ratio(rumorosa) > 0
    assert M.r2(liscia) > 0.9 > M.r2(rumorosa)
    # due anni con la stessa pendenza e uno con pendenza negativa
    date = np.arange(np.datetime64("2020-01-01"), np.datetime64("2023-01-01"))
    n = [int(np.sum(date.astype("datetime64[Y]") == np.datetime64(y, "Y"))) for y in ("2020", "2021", "2022")]
    g = np.concatenate([np.ones(n[0]), np.ones(n[1]), -np.ones(n[2])])
    p = M.pendenze_annue(g, date)
    assert abs(p["pendenze"][2020] - 252) < 1e-6 and abs(p["pendenze"][2022] + 252) < 1e-6, p
    assert abs(p["quota_positivi"] - 2 / 3) < 1e-12
    uniformi = M.pendenze_annue(np.ones(len(date)), date)
    assert abs(uniformi["cv"]) < 1e-9 and uniformi["quota_positivi"] == 1.0, uniformi


def test_trimestri_e_sharpe_mobile():
    date = np.arange(np.datetime64("2020-01-01"), np.datetime64("2021-01-01"))  # 4 trimestri
    mese = date.astype("datetime64[M]").astype(int) % 12
    g = np.where(mese < 6, 1.0, -1.0)
    assert abs(M.trimestri_positivi(g, date) - 0.5) < 1e-12
    sm = M.sharpe_mobile(_rumore(1000, 0.1, seed=4))
    assert sm["minimo"] < sm["mediana"] and 0 <= sm["quota_positiva"] <= 1 and sm["n_finestre"] > 20
    assert M.sharpe_mobile(np.ones(10)) is None


def test_senza_migliori_e_simmetria():
    t = np.array([100.0, 50, 1, 1, 1, -2])
    assert M.senza_migliori(t, 2) == 1.0 and M.senza_migliori(t, 0) == 151.0
    a, b = _rumore(2000, 0.1, seed=5), _rumore(2000, 0.1, seed=6)
    s = M.simmetria(a, b)
    assert s["concordi"] and 0 < s["rapporto"] <= 1, s
    s = M.simmetria(a, -b)
    assert not s["concordi"] and s["rapporto"] < 0, s


def test_wald_wolfowitz():
    alt = M.z_wald_wolfowitz(np.tile([1.0, -1.0], 50))
    assert alt["sequenze"] == 100 and alt["z"] > 9 and "alternati" in alt["significato"], alt
    gr = M.z_wald_wolfowitz(np.r_[np.ones(50), -np.ones(50)])
    assert gr["sequenze"] == 2 and gr["z"] < -9 and "raggruppati" in gr["significato"], gr
    caso = M.z_wald_wolfowitz(_rumore(400, 0, seed=7))
    assert abs(caso["z"]) < 3 and abs(caso["attese"] - 201) < 3, caso
    assert M.z_wald_wolfowitz(np.ones(10))["z"] is None


def test_lunghezza_blocco():
    assert M.lunghezza_blocco(_rumore(2000, seed=8)) < 3
    assert M.lunghezza_blocco(_ar1(2000, 0.7, media=0)) > 5


def test_montecarlo_rumore_e_grappoli():
    r = M.montecarlo(_rumore(1500, 0.05, seed=1), n=2000, seed=0)
    assert abs(r["rapporto_dd"] - 1) < 0.15, r["rapporto_dd"]
    # 60 giorni calmi (media +0,6, vol 1) e 60 agitati (media -0,5, vol 3): perdite a grappolo
    vol = np.tile(np.r_[np.ones(60), 3 * np.ones(60)], 12)
    mu = np.tile(np.r_[0.6 * np.ones(60), -0.5 * np.ones(60)], 12)
    for seed in (0, 1, 3):
        g = np.random.default_rng(seed).normal(0, 1, 1440) * vol + mu
        r = M.montecarlo(g, trade=g[g != 0], regimi=(vol > 1).astype(int), n=2000, seed=0)
        assert r["rapporto_dd"] > 1.1, (seed, r["rapporto_dd"])
        assert r["rapporto_dd_regimi"] > 1.0, (seed, r["rapporto_dd_regimi"])
        assert r["blocchi"]["drawdown"]["p5"] < r["blocchi"]["drawdown"]["p50"] < r["blocchi"]["drawdown"]["p95"]
    assert "rimescolato_trade" in r and "regimi" in r
    # su una serie costante il profitto finale dei metodi coincide con la somma e non ci sono perdite
    c = M.montecarlo(np.ones(300), n=200)
    assert c["blocchi"]["profitto"]["p50"] == 300 and c["blocchi"]["serie_perdite"]["p95"] == 0


def test_portafoglio():
    a = _rumore(2500, 0.05, seed=10)
    # lo stesso sistema due volte: rapporto = 1 / quota sott'acqua
    s = M.sovrapposizione_dd(a, a)
    assert abs(s["rapporto"] - 1 / s["quota_a"]) < 1e-9, s
    # due sistemi indipendenti: in media circa 1
    rap = [M.sovrapposizione_dd(_rumore(2500, 0.1, seed=i), _rumore(2500, 0.1, seed=100 + i))["rapporto"]
           for i in range(20)]
    assert abs(np.mean(rap) - 1) < 0.15, np.mean(rap)
    b = _rumore(2500, 0.05, seed=11)
    m = np.column_stack([a, b, a + 0.1 * b])
    c = M.correlazioni(m)
    assert c["normale"].shape == (3, 3) and c["normale"][0, 2] > 0.9 and abs(c["normale"][0, 1]) < 0.1
    assert c["coda"][0, 2] > 0.8
    # CDaR: il massimo drawdown è il limite superiore, la media dei drawdown quello inferiore
    assert M.cdar(a, 0.95) <= M.drawdown(a)["massimo"] + 1e-9 and M.cdar(a, 0.95) > M.cdar(a, 0.5)
    # un sistema uguale al primo aggiunge rischio, uno opposto lo toglie
    base = np.column_stack([a, a])
    assert M.contributo_cdar(base, [1, 1], 1) > 0
    contro = np.column_stack([a, -a])
    assert M.contributo_cdar(contro, [1, 1], 1) < 0
    assert abs(M.enb(np.column_stack([a, a])) - 1) < 1e-6
    assert M.enb(_rumore((2500 * 5), seed=12).reshape(2500, 5)) > 4.8


def test_scheda_json():
    import json
    rng = np.random.default_rng(13)
    date = np.arange(np.datetime64("2015-01-01"), np.datetime64("2015-01-01") + 1500)
    g = rng.normal(0.05, 1, 1500)
    trade = rng.normal(0.2, 2, 300)
    sch = M.scheda(g, date, trade, n_prove=10, var_sr_prove=0.25, giorn_long=g, giorn_short=-g,
                   matrice_portafoglio=rng.normal(0, 1, (1500, 2)), n_mc=300)
    testo = json.dumps(sch)  # niente NaN né tipi numpy: deve serializzare
    assert "NaN" not in testo and sch["1_sharpe"]["dsr"] is not None and sch["2_cpcv"] is None
    assert sch["7_portafoglio"]["enb_con"] is not None and sch["5_z_wald_wolfowitz"]["n"] == 300
    nudo = M.scheda(g, date, n_mc=300)
    assert nudo["5_z_wald_wolfowitz"] is None and nudo["1_sharpe"]["dsr"] is None and nudo["7_portafoglio"] is None


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok", nome)
