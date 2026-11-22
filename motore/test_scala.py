"""Lancio su molte combinazioni, su più processi e con ripresa, su dati finti. Uso: python -m motore.test_scala"""
import json

import numpy as np
import polars as pl

from . import esperimento, metriche, validazione
from .motori import eventi
from .test_esperimento import _Ambiente, _scrivi

ORE = [f"{h:02d}:00" for h in range(0, 20)]


def _griglia(n_da, n_barre, n_soglie):
    return {"da": ORE[:n_da], "uscita.barre": list(range(n_barre)),
            "cond.0.2": [round(-0.5 + 0.25 * i, 2) for i in range(n_soglie)]}


REGOLA = {"lato": 1, "da": "08:00", "a": "23:00", "cond": [["dal_close_ieri", ">=", 0]], "uscita": {"barre": 0},
          "max_al_giorno": 1}


def test_lancia_2000_combinazioni_su_piu_processi():
    with _Ambiente() as tmp:
        f = _scrivi(tmp, barre=60, k=3, sr_obiettivo=1.5, regola=REGOLA, griglia=_griglia(20, 10, 10))
        c = esperimento.controlla(f)
        assert c["ok"] and c["combinazioni"] == 2000 and c["sr_minimo"] < 1.5, c
        r = esperimento.lancia(f, n_mc=100, lavoratori=3)
        assert r["prove"]["questa"] == 2000
        assert len(validazione._righe()) == 2000
        df = pl.read_parquet(validazione.CARTELLA / "curve" / "prova.parquet")
        ids = [x["id"] for x in validazione._righe()]
        assert df.columns == ["data", *ids] and df.width == 2001, df.width        # una colonna per prova
        assert (validazione.CARTELLA / "curve").glob("*.parquet")
        assert r["tempi"]["eventi"] > 0 and set(r["tempi"]) >= {"eventi", "registro", "pbo", "totale"}
        # i filtri hanno scartato la gran parte delle prove, prima della parte costosa
        pr = r["prove"]
        assert sum(pr["scartate_per"].values()) + pr["dopo_cancello"] == 2000 and pr["dopo_filtri"] >= pr["dopo_cancello"], pr
        assert len(r["candidati"]) == min(3, pr["dopo_cancello"]) and pr["scartate_per"], pr
        assert (esperimento.CARTELLA / "prova" / "prove.parquet").exists()
        assert not (esperimento.CARTELLA / "prova" / "_parziale").exists()


def test_processi_e_lavoro_singolo_danno_le_stesse_serie():
    risultati = []
    for lavoratori in (1, 2):
        with _Ambiente() as tmp:
            f = _scrivi(tmp, barre=60, k=2, sr_obiettivo=1.5, regola=REGOLA, griglia=_griglia(6, 5, 4))
            esperimento.lancia(f, n_mc=100, lavoratori=lavoratori)
            righe = validazione._righe()
            # ogni serie registrata è quella della sua combinazione, ricalcolata qui a parte
            tab = eventi.base("KW", 60)
            for r in righe[::13]:
                _, tr = eventi.prova("KW", 60, esperimento._imposta(REGOLA, r["parametri"]), tab, riassumi=False)
                g = esperimento._giornaliera(tr, tab["data"].unique().sort())
                assert abs(metriche.sharpe(g) - r["sharpe"]) < 1e-3, (r, metriche.sharpe(g))
            df = pl.read_parquet(validazione.CARTELLA / "curve" / "prova.parquet")
            risultati.append(([(r["parametri"], r["sharpe"]) for r in righe], df.drop("data").to_numpy()))
    assert risultati[0][0] == risultati[1][0]
    assert np.array_equal(risultati[0][1], risultati[1][1])


def test_ripresa_dopo_un_interruzione():
    with _Ambiente() as tmp:
        f = _scrivi(tmp, barre=60, k=2, sr_obiettivo=1.5, regola=REGOLA, griglia=_griglia(6, 5, 4))     # 120 combinazioni
        vecchi = (esperimento.LOTTO, esperimento.SALVA_OGNI, esperimento._lavora)
        esperimento.LOTTO, esperimento.SALVA_OGNI = 10, 30
        lavora, chiamate = vecchi[2], []

        def a_scatti(lotto):
            if len(chiamate) == 7:
                raise KeyboardInterrupt("interrotto")
            chiamate.append(lotto[0])
            return lavora(lotto)

        esperimento._lavora = a_scatti
        try:
            try:
                esperimento.lancia(f, n_mc=100, lavoratori=1)
            except KeyboardInterrupt:
                pass
            else:
                raise AssertionError("l'interruzione non è arrivata")
            par = esperimento.CARTELLA / "prova" / "_parziale"
            assert par.exists() and len(list(par.glob("parte_*.pkl"))) == 2, list(par.iterdir())   # salvate 60 prove
            assert not validazione._righe() and not (esperimento.CARTELLA / "prova" / "riassunto.json").exists()
            try:
                esperimento.lancia(f, n_mc=100, lavoratori=1)
            except ValueError as ex:
                assert "--riprendi" in str(ex)
            else:
                raise AssertionError("rilancio senza --riprendi accettato")
            chiamate.clear()
            esperimento._lavora = lambda lotto: (chiamate.append(lotto[0]), lavora(lotto))[1]
            r = esperimento.lancia(f, n_mc=100, lavoratori=1, riprendi=True)
        finally:
            esperimento.LOTTO, esperimento.SALVA_OGNI, esperimento._lavora = vecchi
        assert len(chiamate) == 12 - 6, len(chiamate)          # i 6 lotti non salvati, non tutti i 12
        assert len(validazione._righe()) == 120 and r["prove"]["questa"] == 120
        interrotto = [x["sharpe"] for x in validazione._righe()]
    with _Ambiente() as tmp:
        f = _scrivi(tmp, barre=60, k=2, sr_obiettivo=1.5, regola=REGOLA, griglia=_griglia(6, 5, 4))
        esperimento.lancia(f, n_mc=100, lavoratori=1)
        assert [x["sharpe"] for x in validazione._righe()] == interrotto       # come un lancio mai interrotto
    with _Ambiente() as tmp:
        f = _scrivi(tmp, barre=60, sr_obiettivo=1.5, regola=REGOLA, griglia=_griglia(6, 5, 4))
        try:
            esperimento.lancia(f, n_mc=100, lavoratori=1, riprendi=True)
        except ValueError as ex:
            assert "nessun lancio interrotto" in str(ex)
        else:
            raise AssertionError("ripresa senza lancio interrotto accettata")


def test_controlla_dice_lo_sharpe_minimo_per_il_numero_di_prove():
    with _Ambiente() as tmp:
        grande = {"da": ORE[:20], "uscita.barre": list(range(10)), "cond.0.2": [round(i * 0.1, 1) for i in range(50)]}   # 10.000
        r = esperimento.controlla(_scrivi(tmp, regola=REGOLA, griglia=grande, sr_obiettivo=1.0))
        assert r["combinazioni"] == 10000 and abs(r["sr_minimo"] - 1.19) < 0.005, r
        assert not r["ok"] and "richiedono sr_obiettivo >= 1.19" in r["errori"][0], r["errori"]
        assert esperimento.controlla(_scrivi(tmp, regola=REGOLA, griglia=grande, sr_obiettivo=1.2))["ok"]
        v = esperimento.controlla(_scrivi(tmp, regola=REGOLA, griglia=grande, sr_obiettivo=1.2, modo="verticale"))
        assert not v["ok"] and v["sr_minimo"] > 1.2, v         # in verticale il budget è la metà


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok", nome)
