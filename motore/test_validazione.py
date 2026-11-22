"""Controlli della validazione su dati finti dal risultato noto. Uso: python -m motore.test_validazione"""
import json
import tempfile
from pathlib import Path

import numpy as np

from . import metriche, validazione as V


def _giorni(anni, inizio="2010-01-01"):
    return np.arange(np.datetime64(inizio), np.datetime64(inizio) + int(anni * 365))


def test_blocchi_cpcv():
    b = V.blocchi_cpcv(range(2011, 2024), 2)
    assert len(b) == 78, len(b)
    train, test = b[0]
    assert test == [2011, 2012] and 2011 not in train and len(train) == 11
    assert all(set(tr).isdisjoint(te) and len(tr) + len(te) == 13 for tr, te in b)


def test_purga():
    ini = np.array(["2015-06-01", "2015-12-30", "2016-06-01", "2017-01-03", "2017-03-01"], dtype="datetime64[s]")
    fin = ini + np.timedelta64(3, "D")
    tieni = V.purga(ini, fin, [2016], embargo_giorni=5)
    # il trade del 30 dic 2015 attraversa l'inizio del 2016 e va tolto, come quelli del 2016
    # e quello del 3 gen 2017 (dentro l'embargo); quello di marzo 2017 resta
    assert tieni.tolist() == [True, False, False, False, True], tieni
    assert V.purga(ini, fin, [2016], 0).tolist() == [True, False, False, True, True]
    assert V.purga(ini, fin, [], 5).all()


def test_cpcv_selezione():
    rng = np.random.default_rng(0)
    d = _giorni(13)
    rumore = rng.normal(0, 1, (len(d), 10))
    r = V.cpcv_selezione(rumore, d)
    assert r["n_combinazioni"] == 78 and sum(r["scelte"]) == 78, r
    # rumore: la scelta cade quasi sempre sulla stessa variante (la migliore per caso sull'intero campione,
    # Sharpe ~0,5), quindi gli Sharpe fuori campione delle 78 combinazioni sono correlati e la quota
    # positiva non discrimina; la mediana resta però molto sotto quella di un vantaggio vero
    assert r["mediana"] < 1.0, r
    reale = rumore.copy()
    reale[:, 3] += 0.15  # variante con vantaggio vero (Sharpe annuo ~2,4)
    r = V.cpcv_selezione(reale, d)
    assert r["scelte"][3] == 78 and r["quota_positiva"] > 0.95 and r["mediana"] > 1.5, r


def test_pbo():
    rng = np.random.default_rng(1)
    r = V.pbo(rng.normal(0, 1, (1000, 50)))
    assert r["n_combinazioni"] == 12870 and 0.35 <= r["pbo"] <= 0.65, r
    m = rng.normal(0, 1, (1000, 50))
    m[:, 7] += 0.3  # una variante con media chiaramente positiva
    r = V.pbo(m)
    assert r["pbo"] < 0.1 and r["prob_perdita_oos"] < 0.1, r


def test_spa_e_romano_wolf():
    rng = np.random.default_rng(2)
    for _ in range(3):
        rumore = rng.normal(0, 1, (2500, 20))
        assert V.spa(rumore, b=500)["p"] > 0.1
        assert min(V.romano_wolf(rumore, b=500)["p"]) > 0.1
    m = rng.normal(0, 1, (2520, 20))
    m[:, 4] += 2 / np.sqrt(252)  # Sharpe annuo 2 su 10 anni
    s = V.spa(m, b=500)
    assert s["p"] < 0.05 and s["migliore"] == 4, s
    rw = V.romano_wolf(m, b=500)["p"]
    assert rw[4] < 0.05 and min(p for i, p in enumerate(rw) if i != 4) > 0.05, rw


def test_haircut():
    h = V.haircut(1.0, 10, 1)  # una sola prova: nessun taglio
    assert abs(h["bonferroni"]["haircut"]) < 1e-3 and abs(h["holm"]["haircut"]) < 1e-3, h
    h = V.haircut(1.0, 10, 100)
    assert 0 < h["bonferroni"]["haircut"] < h["bhy"]["haircut"] < 1, h  # BHY è il più severo, a rango 1
    assert V.haircut(0.5, 10, 100)["bonferroni"]["haircut"] > h["bonferroni"]["haircut"]  # Sharpe bassi tagliati di più
    assert V.haircut(0.1, 10, 100)["bhy"]["sr_corretto"] == 0.0


def test_n_indipendenti():
    rng = np.random.default_rng(3)
    base = rng.normal(0, 1, (1000, 1))
    copie = base + 0.05 * rng.normal(0, 1, (1000, 20))
    n = V.n_indipendenti(copie)
    assert n["autovalori"] < 1.2 and n["cluster"] == 1, n
    n = V.n_indipendenti(rng.normal(0, 1, (1000, 20)))
    assert n["autovalori"] > 18 and n["cluster"] == 20, n


def test_registro():
    vero = V.CARTELLA
    V.CARTELLA = Path(tempfile.mkdtemp()) / "registro"
    try:
        assert V.conteggio()["n_prove"] == 0
        rng = np.random.default_rng(4)
        d = _giorni(4)
        base = rng.normal(0.05, 1, len(d))
        id1 = V.registra("e1", "finestre", "JY", {"ora": "03:00"}, base, d)
        id2 = V.registra("e1", "finestre", "JY", {"ora": "04:00"}, base + 0.01 * rng.normal(0, 1, len(d)), d)
        V.registra("e1", "finestre", "AD", {"ora": "03:00"}, rng.normal(0, 1, len(d) - 10), d[10:])  # calendario diverso
        V.registra("e2", "altra", "JY", {}, rng.normal(0, 1, len(d)), d)
        assert (id1, id2) == ("t000001", "t000002")
        righe = [json.loads(r) for r in (V.CARTELLA / "tentativi.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(righe) == 4 and righe[0]["parametri"] == {"ora": "03:00"} and righe[0]["giorni"] == len(d)
        assert abs(righe[0]["sharpe"] - metriche.sharpe(base)) < 1e-3
        c = V.conteggio("finestre")
        assert c["n_prove"] == 3 and c["famiglie"] == ["finestre"] and c["var_sharpe"] is not None, c
        assert 1 <= c["n_effettivo_autovalori"] <= 3 and c["n_effettivo_cluster"] == 2, c  # i primi due sono quasi copie
        assert V.conteggio()["n_prove"] == 4 and V.conteggio("assente")["n_prove"] == 0
        json.dumps(V.conteggio())  # serializzabile
    finally:
        V.CARTELLA = vero


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok", nome)
