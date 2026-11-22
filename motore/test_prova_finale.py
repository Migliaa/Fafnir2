"""Prova finale: una volta per tentativo, mai oltre i dati ammessi. Uso: python -m motore.test_prova_finale"""
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl

from . import catalogo, dati, giudizio, prova_finale, validazione

REGOLA = {"lato": 1, "da": "09:00", "a": "09:00", "uscita": {"barre": 0}, "max_al_giorno": 1}


def _minuti(periodi, seme=5):
    """Minuti finti nei periodi dati (inizio, fine); rialzo fisso di 0,02 a minuto fra le 09:00 e le 10:00."""
    parti = []
    for i, (da, a) in enumerate(periodi):
        t = pl.datetime_range(da, a, "1m", time_zone="Europe/Rome", eager=True, closed="left")
        rng = np.random.default_rng(seme + i)
        r = rng.normal(0, 0.02, len(t))
        r[t.dt.hour().to_numpy() == 9] += 0.02
        c = 100 + np.cumsum(r)
        o = np.concatenate([[100.0], c[:-1]])
        parti.append(pl.DataFrame({"apre": t, "o": o, "h": np.maximum(o, c), "l": np.minimum(o, c), "c": c,
                                   "v": np.ones(len(t))}))
    return pl.concat(parti)


class _Ambiente:
    def __init__(self, periodi):
        self.periodi = periodi

    def __enter__(self):
        self.vecchi = (dati.barre, dati.minuti, validazione.CARTELLA, dict(catalogo.CATALOGO))
        self.tmp = Path(tempfile.mkdtemp())
        self.m = _minuti(self.periodi)
        self.letture = []

        def minuti(nome, cache=True):
            self.letture.append(("minuti", nome))
            return self.m

        def barre(nome, n, cache=True):
            self.letture.append(("barre", nome, n))
            return dati.aggrega(self.m, n)

        dati.minuti, dati.barre = minuti, barre
        validazione.CARTELLA = self.tmp / "registro"
        catalogo.CATALOGO["TST"] = catalogo.Prodotto("TST", "prova", (), True, 0.05, euro_punto=2.0)
        id_ = validazione.registra("e", "f", "TST", {}, np.zeros(10), np.arange(np.datetime64("2011-01-03"), np.datetime64("2011-01-13")))
        return id_, self

    def __exit__(self, *a):
        dati.barre, dati.minuti, validazione.CARTELLA, cat = self.vecchi
        catalogo.CATALOGO.clear()
        catalogo.CATALOGO.update(cat)


FINE_DATI = datetime(2025, 5, 31)
PERIODI = [(datetime(2010, 1, 4), datetime(2010, 3, 1)), (datetime(2023, 12, 1), FINE_DATI)]


def test_calcola_i_due_periodi_e_segna_il_tentativo():
    with _Ambiente(PERIODI) as (id_, amb):
        file = amb.tmp / "c01_holdout.parquet"
        r = prova_finale.esegui("TST", 60, REGOLA, id_, file)
        assert not r["gia_usata"] and r["avanti"]["n"] > 300 and r["indietro"]["n"] > 30, r
        assert r["avanti"]["da"] >= "2024-01-01" and r["avanti"]["a"] <= "2025-05-31", r["avanti"]
        assert r["indietro"]["a"] <= "2010-12-31"
        assert r["avanti"]["utile"] > 0 and r["avanti"]["guadagno_medio"] > 0           # il rialzo c'è
        assert r["avanti"]["euro_punto"] == 2.0
        assert validazione.holdout_usato(id_)["risultato"]["avanti"] == r["avanti"]
        s = pl.read_parquet(file)
        assert s.columns == ["data", "periodo", "punti"] and set(s["periodo"]) == {"indietro", "avanti"}
        assert s["data"].max().isoformat() <= "2025-05-31" and s.filter(pl.col("periodo") == "avanti")["data"].min().year == 2024
        assert abs(s.filter(pl.col("periodo") == "avanti")["punti"].sum() * 2.0 - r["avanti"]["utile"]) < 1e-6


def test_non_si_ripete_sullo_stesso_tentativo():
    with _Ambiente(PERIODI) as (id_, amb):
        r1 = prova_finale.esegui("TST", 60, REGOLA, id_)
        n = len(amb.letture)
        assert n > 0
        r2 = prova_finale.esegui("TST", 60, REGOLA, id_)           # nemmeno un dato letto
        assert len(amb.letture) == n and r2["gia_usata"] and r2["avanti"] == r1["avanti"] and r2["indietro"] == r1["indietro"]
        # nemmeno con un'altra regola: il tentativo ha già consumato la prova
        r3 = prova_finale.esegui("TST", 60, {**REGOLA, "uscita": {"barre": 3}}, id_)
        assert len(amb.letture) == n and r3["avanti"] == r1["avanti"]
        # un altro tentativo ha la sua prova
        altro = validazione.registra("e", "f", "TST", {"k": 1}, np.zeros(10), np.arange(np.datetime64("2011-01-03"), np.datetime64("2011-01-13")))
        prova_finale.esegui("TST", 60, REGOLA, altro)
        assert len(amb.letture) > n and validazione.holdout_usato(altro) is not None


def test_non_legge_oltre_il_taglio_e_non_segna_se_fallisce():
    # dati fino a dicembre 2025: la prova finale non li accetta e il tentativo non risulta consumato
    lunghi = [(datetime(2023, 12, 1), datetime(2025, 12, 31))]
    with _Ambiente(lunghi) as (id_, amb):
        try:
            prova_finale.esegui("TST", 60, REGOLA, id_)
        except RuntimeError as ex:
            assert "oltre il taglio" in str(ex)
        else:
            raise AssertionError("dati oltre il taglio accettati")
        assert validazione.holdout_usato(id_) is None
    # senza dati prima del 2011 non c'è holdout all'indietro; senza dati nel periodo in avanti non c'è nemmeno quello
    with _Ambiente([(datetime(2023, 12, 1), datetime(2024, 3, 1))]) as (id_, amb):
        r = prova_finale.esegui("TST", 60, REGOLA, id_)
        assert r["indietro"] is None and r["avanti"]["n"] > 0 and r["avanti"]["a"] <= "2024-03-01"
    with _Ambiente([(datetime(2011, 1, 3), datetime(2011, 3, 1))]) as (id_, amb):
        r = prova_finale.esegui("TST", 60, REGOLA, id_)
        assert r["avanti"] is None and r["indietro"] is None
        assert giudizio._motivo(giudizio.prova_finale_voci(r, 20.0)) == "nessun trade fuori campione"


def test_dati_veri_finiscono_prima_del_taglio():
    # il lettore dei dati veri non restituisce nulla da TAGLIO in poi, qualunque cosa ci sia sul disco
    from .config import TAGLIO
    assert TAGLIO == datetime(2025, 11, 21, tzinfo=TAGLIO.tzinfo)
    try:
        dati.controlla_taglio(pl.DataFrame({"apre": [datetime(2025, 11, 21, 2)]}).with_columns(
            pl.col("apre").dt.replace_time_zone("Europe/Rome")))
    except RuntimeError:
        pass
    else:
        raise AssertionError("barra oltre il taglio accettata")


def test_arricchisci_legge_gli_holdout_solo_per_chi_passa_e_una_volta():
    from . import esperimento
    from .test_esperimento import CAMBI_FILTRI
    from .test_robustezza import _ambiente, _lancia
    veri = {"SOGLIE_GUADAGNO": ((36.0, 20.0), (72.0, 30.0), (float("inf"), 50.0)), "TRADE_ANNO_MIN": 12.0, "R2_MIN": 0.85,
            "ANNI_POSITIVI_MIN": 0.70}              # i filtri di Andrea (l'ambiente di prova li allarga)
    with _ambiente() as tmp:
        _lancia(tmp)
        chiamate, vera = [], prova_finale._periodo
        prova_finale._periodo = lambda *a, **k: (chiamate.append(a[3]), vera(*a, **k))[1]
        try:
            larghi = {k: getattr(giudizio, k) for k in CAMBI_FILTRI}
            for k, v in veri.items():
                setattr(giudizio, k, v)
            r = esperimento.arricchisci("prova")           # con i filtri veri nessuno passa: nessun holdout letto
            assert {c["esito"] for c in r["candidati"]} == {"scartato"} and chiamate == [], chiamate
            assert not [x for x in validazione._righe() if x.get("holdout_usato")]
            assert all(c["motivo"].startswith("guadagno medio") and c["fuori_campione"] is None for c in r["candidati"])
            for k, v in larghi.items():
                setattr(giudizio, k, v)
            r = esperimento.arricchisci("prova")           # con i filtri larghi passano la scoperta e consumano la prova
            passano = [c for c in r["candidati"] if c["motivo"] == "nessun trade fuori campione"]
            assert len(passano) == 3 and len(chiamate) == 6, (len(passano), chiamate)     # due periodi a testa
            assert len([x for x in validazione._righe() if x.get("holdout_usato")]) == 3
            r = esperimento.arricchisci("prova")           # un secondo giro non legge più nulla
            assert len(chiamate) == 6 and len([c for c in r["candidati"] if c["motivo"] == "nessun trade fuori campione"]) == 3
        finally:
            prova_finale._periodo = vera


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok", nome)
