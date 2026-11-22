"""Campagna: una ricerca per prodotto, lato e timeframe, ripresa dopo un'interruzione, riepilogo con le conferme.
Uso: python -m motore.test_campagna"""
import json

from . import albero as A
from . import campagna as C
from . import ricerca as R
from .test_esperimento import _Ambiente

SPEC = {"tipo": "campagna", "nome": "prova-camp", "ipotesi": "x", "meccanismo": "y", "fonte": "z", "prodotti": ["KW"], "lati": [1, -1],
        "barre": [60], "orari": {"da": "08:00", "a": "12:00"}, "uscite": {"60": [{"nome": "una barra", "barre": 0}, {"nome": "alle 15", "ora": "15:00"}]},
        "cicli": {"semi_1": 3, "semi_2": 2, "finali": 2, "margine_semi": 0.0}, "rumore": {"ripetizioni": 2}, "uscite_finali": []}


def test_campagna():
    with _Ambiente() as tmp:
        A.CARTELLA, C.CARTELLA = tmp / "ricerche", tmp / "campagne"
        vecchi = (A.SCOPERTA, R.WF_PRIMO_ANNO)
        A.SCOPERTA, R.WF_PRIMO_ANNO = (2014, 2016), 2015
        try:
            f = tmp / "c.json"
            f.write_text(json.dumps(SPEC), encoding="utf-8")
            c = C.controlla(f)
            assert c["ok"] and c["ricerche"] == 2, c
            nomi = [r["nome"] for r in C.ricerche(SPEC)]
            assert nomi == ["prova-camp-KW-long-60m", "prova-camp-KW-short-60m"]
            assert C.ricerche(SPEC)[1]["lato"] == -1 and C.ricerche(SPEC)[0]["forza_bruta"]["orari"]["passo"] == 60
            r = C.lancia(f, log=lambda *a: None, lavoratori=1)
            assert [e["stato"] for e in r["esiti"]] == ["finita", "finita"], r["esiti"]
            for n in nomi:
                a = json.loads((tmp / "ricerche" / n / "ricerca.json").read_text(encoding="utf-8"))
                assert a["campagna"] == "prova-camp" and a["lato"] in (1, -1)
            assert (tmp / "campagne" / "prova-camp" / "campagna.json").exists()
            assert all(x["stato"] == "finita" for x in r["righe"])
            # una seconda volta non rifà niente: riparte da dove era
            r2 = C.lancia(f, log=lambda *a: None, lavoratori=1)
            assert r2["esiti"] == []
            # una ricerca interrotta (solo lo stato, niente risultato) si rifà
            (tmp / "ricerche" / nomi[1] / "ricerca.json").unlink()
            r3 = C.lancia(f, log=lambda *a: None, lavoratori=1)
            assert [e["nome"] for e in r3["esiti"]] == [nomi[1]]
            bad = dict(SPEC, prodotti=["VX"], barre=[30])
            f.write_text(json.dumps(bad), encoding="utf-8")
            e = C.controlla(f)["errori"]
            assert any("valore del punto" in x for x in e) and any("uscite per le barre da 30" in x for x in e), e
        finally:
            A.SCOPERTA, R.WF_PRIMO_ANNO = vecchi


if __name__ == "__main__":
    test_campagna()
    print("ok test_campagna")
