"""Controlli di controllo e lancio degli esperimenti su dati finti. Uso: python -m motore.test_esperimento"""
import json
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl

from . import catalogo, dati, esperimento, giudizio, validazione

CAMPI = {"nome": "prova", "ipotesi": "il prezzo sale fra le 09 e le 10", "meccanismo": "flusso d'ordini del mattino",
         "fonte": "dati finti", "direzione": "long", "modo": "ampiezza", "prodotti": ["KW"], "barre": 60,
         "regola": {"lato": 1, "da": "09:00", "a": "09:00", "uscita": {"barre": 0}, "max_al_giorno": 1},
         "griglia": {"uscita.barre": [0, 1, 2, 3, 4, 5]}}


def _minuti_finti(nome, cache=True):
    # tre anni di minuti; passeggiata casuale, più un rialzo fisso fra le 09:00 e le 10:00 di ogni giorno
    t = pl.datetime_range(datetime(2014, 1, 6), datetime(2017, 1, 1), "1m", time_zone="Europe/Rome",
                          eager=True, closed="left")
    rng = np.random.default_rng(5)
    r = rng.normal(0, 0.02, len(t))
    ora = t.dt.hour().to_numpy()
    r[ora == 9] += 0.02
    c = 100 + np.cumsum(r)
    o = np.concatenate([[100.0], c[:-1]])
    return pl.DataFrame({"apre": t, "o": o, "h": np.maximum(o, c), "l": np.minimum(o, c), "c": c,
                         "v": np.ones(len(t))})


def _scrivi(cartella, **modifiche):
    e = {**CAMPI, **modifiche}
    e = {k: v for k, v in e.items() if v is not None}
    f = Path(cartella) / "e.json"
    f.write_text(json.dumps(e), encoding="utf-8")
    return f


CAMBI_FILTRI = {"SOGLIE_GUADAGNO": ((float("inf"), 0.1),), "TRADE_ANNO_MIN": 1.0, "R2_MIN": 0.5, "ANNI_POSITIVI_MIN": 0.2}


def installa_dati_finti():
    """Dati finti al posto di quelli veri e un KW con valore del punto noto e costi nulli. Chiamata anche in ogni
    processo di lavoro (`esperimento.PREPARA_LAVORATORI`), dove le sostituzioni del processo principale non arrivano."""
    m = _minuti_finti("KW")
    dati.minuti = lambda nome, cache=True: m
    dati.barre = lambda nome, minuti, cache=True: dati.aggrega(m, minuti)
    catalogo.CATALOGO["KW"] = catalogo.Prodotto("KW", "prova", (), True, 0.0, euro_punto=1.0)


class _Ambiente:
    """Dati finti, cartelle temporanee e filtri di Andrea allargati (i dati finti hanno tre anni e vantaggi piccoli)."""
    def __enter__(self):
        self.vecchi = (dati.barre, dati.minuti, esperimento.CARTELLA, validazione.CARTELLA, dict(catalogo.CATALOGO),
                       {k: getattr(giudizio, k) for k in CAMBI_FILTRI}, esperimento.PREPARA_LAVORATORI)
        self.tmp = Path(tempfile.mkdtemp())
        installa_dati_finti()
        for k, v in CAMBI_FILTRI.items():
            setattr(giudizio, k, v)
        esperimento.CARTELLA, esperimento.PREPARA_LAVORATORI = self.tmp / "esperimenti", "motore.test_esperimento:installa_dati_finti"
        validazione.CARTELLA = self.tmp / "registro"
        return self.tmp

    def __exit__(self, *a):
        (dati.barre, dati.minuti, esperimento.CARTELLA, validazione.CARTELLA, cat, filtri,
         esperimento.PREPARA_LAVORATORI) = self.vecchi
        catalogo.CATALOGO.clear()
        catalogo.CATALOGO.update(cat)
        for k, v in filtri.items():
            setattr(giudizio, k, v)


def test_controlla_rifiuta():
    with _Ambiente() as tmp:
        assert esperimento.controlla(_scrivi(tmp))["ok"]
        r = esperimento.controlla(_scrivi(tmp, ipotesi=None))
        assert not r["ok"] and any("ipotesi" in x for x in r["errori"]), r
        r = esperimento.controlla(_scrivi(tmp, griglia={"uscita.giorni": [1, 2]}))
        assert not r["ok"] and any("uscita.giorni" in x for x in r["errori"]), r
        r = esperimento.controlla(_scrivi(tmp, direzione="short"))
        assert not r["ok"] and any("direzione" in x for x in r["errori"]), r
        r = esperimento.controlla(_scrivi(tmp, prodotti=["XXX"]))
        assert not r["ok"], r
        # budget: con Sharpe obiettivo 0,5 su 10 anni le prove ammesse sono 3; in verticale la metà
        r = esperimento.controlla(_scrivi(tmp, sr_obiettivo=0.5))
        assert not r["ok"] and r["budget"] == 3.5 and r["max_combinazioni"] == 3, r
        assert "al massimo 3 combinazioni" in r["errori"][0], r
        r = esperimento.controlla(_scrivi(tmp, sr_obiettivo=0.5, griglia={"uscita.barre": [0, 1, 2]}))
        assert r["ok"], r
        r = esperimento.controlla(_scrivi(tmp, sr_obiettivo=0.5, modo="verticale",
                                          griglia={"uscita.barre": [0, 1, 2]}))
        assert not r["ok"] and r["max_combinazioni"] == 1, r
        # lo specchio raddoppia le prove
        r = esperimento.controlla(_scrivi(tmp, sr_obiettivo=0.5, specchio=True,
                                          griglia={"uscita.barre": [0, 1, 2, 3, 4]}))
        assert not r["ok"] and r["prove"] == 10, r


def test_lancia_trova_il_vantaggio_e_non_si_rilancia():
    with _Ambiente() as tmp:
        f = _scrivi(tmp, k=3)
        r = esperimento.lancia(f, n_mc=200)
        c = r["candidati"]
        assert len(c) == 3 and c[0]["parametri"] == {"uscita.barre": 0}, c
        assert c[0]["dsr"] > 0.95 and c[0]["sharpe"] > 5 and c[0]["n"] > 1000, c[0]
        assert [x["dsr_eventi"] for x in c] == sorted((x["dsr_eventi"] for x in c), reverse=True)
        assert r["prove"]["questa"] == 6 and r["pbo"]["prova"]["KW"] is not None, r["prove"]
        cart = esperimento.CARTELLA / "prova" / "candidati"
        for nome in ("c01.json", "c01_trade.parquet", "c01_giorn.parquet"):
            assert (cart / nome).exists(), nome
        assert json.loads((cart / "c01.json").read_text(encoding="utf-8"))["scheda"]["6_montecarlo"]
        assert len(validazione._righe()) == 6
        assert esperimento.riassunto("prova") == r
        # un secondo lancio dello stesso file è rifiutato e non tocca il registro
        try:
            esperimento.lancia(f, n_mc=200)
        except ValueError as ex:
            assert "già lanciato" in str(ex)
        else:
            raise AssertionError("secondo lancio accettato")
        assert len(validazione._righe()) == 6
        assert not esperimento.controlla(f)["ok"]


if __name__ == "__main__":
    for f in (test_controlla_rifiuta, test_lancia_trova_il_vantaggio_e_non_si_rilancia):
        f()
        print("ok", f.__name__)
