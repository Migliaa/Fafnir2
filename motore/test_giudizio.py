"""Filtri di Andrea, cancello statistico e prova finale nel giudizio. Uso: python -m motore.test_giudizio"""
from datetime import datetime

import numpy as np
import polars as pl

from . import giudizio as G


def _m(**kw):
    """Misure che passano tutto: 5 ore a trade, 30 euro a trade."""
    return {"euro_punto": 1.0, "n": 520, "trade_anno": 40.0, "guadagno_medio": 30.0, "ore_medie": 5.0, "r2": 0.9,
            "anni_positivi": 0.8, **kw}


def _esito(voci, nome):
    return next(v["esito"] for v in voci if v["nome"] == nome)


def test_soglie_di_guadagno_per_durata():
    # fino a 36 ore 20 euro, fino a 72 ore 30, oltre 50: i limiti appartengono alla fascia più corta
    assert [G.soglia_guadagno(o) for o in (0.5, 36.0, 36.01, 72.0, 72.01, 500.0)] == [20, 20, 30, 30, 50, 50]
    ok = lambda gm, ore: _esito(G.filtri_andrea(_m(guadagno_medio=gm, ore_medie=ore)), "Guadagno medio per trade")
    assert ok(20.0, 36.0) == "verde" and ok(19.99, 36.0) == "rosso"
    assert ok(20.0, 36.5) == "rosso" and ok(30.0, 36.5) == "verde" and ok(30.0, 72.0) == "verde"
    assert ok(29.99, 72.0) == "rosso" and ok(30.0, 72.5) == "rosso" and ok(50.0, 72.5) == "verde"
    assert ok(49.99, 400.0) == "rosso"


def test_trade_anno_r2_e_anni_positivi():
    voci = lambda **kw: G.filtri_andrea(_m(**kw))
    assert _esito(voci(trade_anno=12.0), "Trade l'anno") == "verde"
    assert _esito(voci(trade_anno=11.99), "Trade l'anno") == "rosso"
    assert _esito(voci(r2=0.85), "Regolarità della curva (R²)") == "verde"
    assert _esito(voci(r2=0.849), "Regolarità della curva (R²)") == "rosso"
    assert _esito(voci(anni_positivi=0.70), "Anni positivi") == "verde"
    assert _esito(voci(anni_positivi=0.69), "Anni positivi") == "rosso"
    assert G._motivo(voci()) is None


def test_motivo_principale_e_valore_del_punto():
    # il motivo è una frase con i numeri, e la prima voce che non passa vince
    m = G._motivo(G.filtri_andrea(_m(guadagno_medio=4.4, trade_anno=5.0)))
    assert m == "guadagno medio 4,4 € sotto i 20 €", m
    assert G._motivo(G.filtri_andrea(_m(trade_anno=11.2))) == "11 trade l'anno sotto i 12"
    assert G._motivo(G.filtri_andrea(_m(r2=0.5))) == "R² 0,50 sotto 0,85"
    assert G._motivo(G.filtri_andrea({"euro_punto": None})) == "valore del punto non noto"
    g = G.giudica({"1_sharpe": {"dsr": 0.99}, "2_pbo": {"pbo": 0.1}}, {}, {"euro_punto": None, "n": 100})
    assert g["esito"] == "scartato" and g["motivo"] == "valore del punto non noto" and not g["passa_scoperta"]


def test_cancello_statistico():
    assert G._motivo(G.cancello_statistico(0.95, 0.19)) is None
    assert G._motivo(G.cancello_statistico(0.949, 0.1)).startswith("DSR 0,949")
    assert G._motivo(G.cancello_statistico(0.99, 0.2)).startswith("PBO 0,20")      # PBO < 0,2: 0,2 non passa
    assert G._motivo(G.cancello_statistico(0.99, None)) is None                  # famiglia con meno di 4 combinazioni
    assert G._motivo(G.cancello_statistico(None, 0.1)) == "DSR non calcolabile"


def test_prova_finale():
    avanti = lambda **kw: G.prova_finale_voci({"avanti": {"n": 20, "utile": 100.0, "guadagno_medio": 12.0, **kw}}, 20.0)
    assert G._motivo(avanti()) is None
    assert G._motivo(avanti(guadagno_medio=10.0)) is None           # metà esatta di 20
    assert G._motivo(avanti(guadagno_medio=9.99)).startswith("fuori campione 9,9 € a trade")
    assert G._motivo(avanti(utile=-1.0)) == "fuori campione negativo"
    assert G._motivo(avanti(utile=0.0)) == "fuori campione negativo"
    assert G._motivo(G.prova_finale_voci({"avanti": {"n": 0, "utile": None, "guadagno_medio": None}}, 20.0)) == "nessun trade fuori campione"
    assert G._motivo(G.prova_finale_voci({"avanti": None, "indietro": None}, 20.0)) == "nessun trade fuori campione"
    assert G._motivo(G.prova_finale_voci(None, 20.0)) == "prova finale non eseguita"


def test_esito_con_prova_finale():
    scheda = {"1_sharpe": {"dsr": 0.99}, "2_pbo": {"pbo": 0.1}}
    pf = lambda gm, u=100.0: {"avanti": {"n": 20, "utile": u, "guadagno_medio": gm}}
    g = G.giudica(scheda, {}, _m(), pf(25.0))
    assert g["esito"] == "candidato" and g["passa_scoperta"], g["motivo"]
    # senza prova finale chi ha passato il resto resta scartato (non si promuove senza), ma passa la scoperta
    g = G.giudica(scheda, {}, _m(), None)
    assert g["esito"] == "scartato" and g["passa_scoperta"] and g["motivo"] == "prova finale non eseguita"
    g = G.giudica(scheda, {}, _m(), pf(25.0, -5.0))
    assert g["esito"] == "scartato" and g["motivo"] == "fuori campione negativo"
    # chi fallisce sulla scoperta non arriva alla prova finale: nessuna voce di prova finale
    g = G.giudica(scheda, {}, _m(guadagno_medio=4.4), pf(25.0))
    assert g["esito"] == "scartato" and g["prova_finale"] is None and not g["passa_scoperta"]


def test_misure_da_una_tabella_di_trade():
    t0 = datetime(2011, 1, 3, 10, 0)
    ing = [t0.replace(day=3 + i, month=1 + 3 * (i % 4)) for i in range(8)]
    uscite = [x.replace(hour=15) for x in ing]                          # cinque ore a trade
    punti = [30.0, 10.0, 20.0, -5.0, 25.0, 15.0, 30.0, 5.0]
    tr = pl.DataFrame({"ingresso": ing, "uscita": uscite, "barre": [5] * 8, "punti": punti, "costo": [2.0] * 8})
    date = np.arange(np.datetime64("2011-01-01"), np.datetime64("2012-01-01"))
    m = G.misure(tr, date, 2.0, 1000, anni=(2011, 2012))
    assert m["n"] == 8 and m["trade_anno"] == 4.0
    assert abs(m["guadagno_medio"] - 2.0 * np.mean(punti)) < 1e-9 and abs(m["costo_medio"] - 4.0) < 1e-9
    assert abs(m["lordo_medio"] - (m["guadagno_medio"] + 4.0)) < 1e-9 and abs(m["rapporto_costi"] - m["lordo_medio"] / 4.0) < 1e-9
    assert abs(m["ore_medie"] - 5.0) < 1e-9 and abs(m["in_mercato"] - 40 / 1000) < 1e-12
    assert abs(m["utile"] - 2.0 * sum(punti)) < 1e-9 and m["drawdown"] > 0 and m["anni_positivi"] == 0.5
    assert abs(m["utile_su_dd"] - m["utile"] / m["drawdown"]) < 1e-9 and 0 < m["r2"] <= 1
    assert G.misure(tr, date, None)["guadagno_medio"] is None and G.misure(tr, date, None)["n"] == 8


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok", nome)
