"""Verifica del server sui risultati veri (sola lettura; le decisioni vanno in una cartella temporanea).
Uso: python -m cruscotto.test_server"""
import json
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

from . import server

ESP = "dax-long-5m-momento-chiusura"


def _chiama(porta, percorso, corpo=None, host=None, origine=None):
    intest = {"Host": host or f"127.0.0.1:{porta}"}
    if corpo is not None:
        intest["Content-Type"] = "application/json"
    if origine:
        intest["Origin"] = origine
    rq = urllib.request.Request(f"http://127.0.0.1:{porta}{percorso}", headers=intest,
                                data=None if corpo is None else json.dumps(corpo).encode("utf-8"))
    try:
        with urllib.request.urlopen(rq) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_curva_con_i_due_holdout():
    """Curva completa con serie FINTE dei due holdout (numeri costruiti qui): fasce in ordine di data, cumulato continuo."""
    import shutil

    import numpy as np
    import polars as pl
    tmp = Path(tempfile.mkdtemp())
    dst = tmp / ESP
    shutil.copytree(server.CARTELLA_ESPERIMENTI / ESP, dst)
    (dst / "commenti").mkdir(exist_ok=True)
    ind = pl.DataFrame({"data": [__import__("datetime").date(2010, 12, 28), __import__("datetime").date(2010, 12, 29)], "punti": [10.0, -4.0],
                        "periodo": ["indietro", "indietro"]})
    avanti = pl.DataFrame({"data": [__import__("datetime").date(2024, 1, 2), __import__("datetime").date(2024, 1, 3), __import__("datetime").date(2024, 1, 4)],
                           "punti": [5.0, 5.0, -2.0], "periodo": ["avanti"] * 3})
    pl.concat([ind, avanti]).select("data", "periodo", "punti").write_parquet(dst / "candidati" / "c01_holdout.parquet")
    vero, server.CARTELLA_ESPERIMENTI = server.CARTELLA_ESPERIMENTI, tmp
    try:
        c = server._completa(ESP, "c01", 1.0)
        assert [x[0] for x in c["segmenti"]] == ["indietro", "scoperta", "avanti"], c["segmenti"]
        (_, a0, a1), (_, b0, b1), (_, c0, c1) = c["segmenti"]
        assert (a0, a1) == (0, 1) and b0 == 2 and c1 == len(c["cum"]) - 1 and c0 == b1 + 1
        assert c["cum"][:2] == [10.0, 6.0] and c["date"][0] == "2010-12-28" and c["date"][-1] == "2024-01-04"
        g = pl.read_parquet(dst / "candidati" / "c01_giorn.parquet").sort("data")
        t = pl.read_parquet(dst / "candidati" / "c01_trade.parquet")
        profitto = float(t["punti"].sum())
        assert abs(c["cum"][b1] - (6.0 + profitto)) < 0.01 and abs(c["cum"][-1] - (6.0 + profitto + 8.0)) < 0.01
        assert c["date"][b0] == str(g["data"][0]) and c["date"][b1] == str(g["data"][-1])
        assert min(c["dd"]) <= c["dd"][b1] <= 0
        m = server._mini(ESP, "c01", 1.0)
        assert m["segmenti"][0][0] == "indietro" and m["segmenti"][-1][0] == "avanti" and len(m["y"]) <= 60
    finally:
        server.CARTELLA_ESPERIMENTI = vero


def test_alberi():
    """Elenco e dettaglio di un albero finto in una cartella temporanea; nomi non ammessi rifiutati."""
    vecchia = server.CARTELLA_ALBERI
    server.CARTELLA_ALBERI = Path(tempfile.mkdtemp())
    try:
        assert server.api_alberi() == []
        d = server.CARTELLA_ALBERI / "prova"
        d.mkdir()
        nodi = [{"id": "n001", "livello": "L0", "esito": "passa"}, {"id": "n002", "livello": "L0", "esito": "scartato"},
                {"id": "n003", "livello": "L2", "esito": "pronto"}]
        foglie = [{"id": "n003", "esito": "candidato"}, {"id": "n001", "esito": "scartato"}]
        (d / "albero.json").write_text(json.dumps({"intestazione": {"prodotto": "FDAX", "barre": 5}, "quando": "2026-11-22T10:00:00",
                                                   "prove": 3, "budget": 200, "nodi": nodi, "foglie": foglie}), encoding="utf-8")
        (server.CARTELLA_ALBERI / "vuota").mkdir()                     # cartella senza albero.json: ignorata
        l = server.api_alberi()
        assert l == [{"nome": "prova", "prodotto": "FDAX", "barre": 5, "quando": "2026-11-22T10:00:00", "prove": 3, "budget": 200,
                      "radici": 2, "radici_vive": 1, "foglie": 2, "candidati": 1}], l
        a = server.api_albero("prova")
        assert a["nodi"] == nodi and a["soglie_guadagno"][-1] == [None, 50.0]
        for cattivo in ("../prova", "vuota", "nessuno"):
            try:
                server.api_albero(cattivo)
            except server.NonTrovato:
                pass
            else:
                raise AssertionError(cattivo)
    finally:
        server.CARTELLA_ALBERI = vecchia


def main():
    test_curva_con_i_due_holdout()
    test_alberi()
    tmp = Path(tempfile.mkdtemp())
    server.DECISIONI = tmp / "cruscotto" / "decisioni.json"
    srv = server.crea_server(0)
    porta = srv.server_address[1]
    assert srv.server_address[0] == "127.0.0.1", srv.server_address
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        get = lambda p, **k: _chiama(porta, p, **k)
        j = lambda p: json.loads(get(p)[1].decode("utf-8"))
        for p in ("/", "/app.js", "/style.css", "/api/esperimenti", f"/api/esperimenti/{ESP}", "/api/sistemi",
                  f"/api/sistemi/{ESP}/c01", "/api/registro", f"/api/registro?famiglia={ESP}"):
            assert get(p)[0] == 200, p
        assert get("/api/nulla")[0] == 404 and get("/api/esperimenti/xx")[0] == 404 and get("/../motore/config.py")[0] == 404
        assert get(f"/api/sistemi/{ESP}/c99")[0] == 404
        assert get("/api/sistemi", host="altro.example")[0] == 403

        e = j(f"/api/esperimenti/{ESP}")
        assert e["resoconto"] and e["intestazione"]["nome"] == ESP and sum(e["esiti"].values()) == len(e["candidati"])
        lista = j("/api/esperimenti")
        assert lista[0]["nome"] == ESP and lista[0]["n_candidati"] == 10
        righe = j("/api/sistemi")
        assert len(righe) == 10 and righe[0]["esito"] and set(righe[0]["gruppi"]) == {
            "caso", "costi", "regolarita", "robustezza", "rischio", "portafoglio"}
        assert righe[0]["decisione_stato"] == "da guardare"
        # esiti: solo candidato o scartato; col guadagno medio di 4,4 euro a trade nessun candidato dell'esperimento DAX passa
        assert {r["esito"] for r in righe} == {"scartato"} and e["esiti"] == {"candidato": 0, "scartato": 10, "non_giudicato": 0}
        assert all(r["motivo"].startswith("guadagno medio") and r["misure"]["guadagno_medio"] < 20 for r in righe)
        assert lista[0]["soglie"]["trade_anno"] == 12 and lista[0]["soglie"]["guadagno_euro"][0] == [36.0, 20.0]
        assert righe[0]["mini"]["y"] and righe[0]["mini"]["segmenti"][0][0] == "scoperta" and not righe[0]["fuori_campione"]

        # i numeri della scheda di c01 sono quelli del file dei candidati
        s = j(f"/api/sistemi/{ESP}/c01")
        c = json.loads((server.CARTELLA_ESPERIMENTI / ESP / "candidati" / "c01.json").read_text(encoding="utf-8"))
        assert s["scheda"] == c and s["scheda"]["backtest"]["n"] == c["backtest"]["n"]
        riga = next(r for r in righe if r["id"] == "c01")
        for k in ("n", "media", "pf", "sharpe", "dsr", "anni_positivi", "pbo"):
            assert riga[k] is not None
        assert riga["n"] == c["backtest"]["n"] and riga["media"] == c["backtest"]["media_esc"]
        assert riga["pf"] == c["backtest"]["pf"] and riga["sharpe"] == c["backtest"]["sharpe"]
        assert riga["dsr"] == c["scheda"]["1_sharpe"]["dsr"] and riga["pbo"] == c["scheda"]["2_pbo"]["pbo"]
        assert riga["esito"] == c["giudizio"]["esito"]
        assert riga["gruppi"] == {k: g["esito"] for k, g in c["giudizio"]["gruppi"].items()}
        assert abs(riga["netto_euro"] - c["robustezza"]["euro"]["profitto"]) < 0.01
        # curva: l'ultimo valore cumulato è il profitto netto del file, il drawdown massimo è quello della scheda
        cu = s["curva"]
        assert abs(cu["esc"]["cum"][-1] - c["scheda"]["4_robustezza"]["profitto"]) < 0.01, cu["esc"]["cum"][-1]
        assert abs(-min(cu["esc"]["dd"]) - c["scheda"]["3_regolarita"]["massimo"]) < 0.01
        assert abs(cu["eur"]["cum"][-1] - c["robustezza"]["euro"]["profitto"]) < 0.5
        # curva completa in euro: senza prova finale una sola fascia, la scoperta, e chiude sul profitto in euro
        co = s["completa"]
        assert [x[0] for x in co["segmenti"]] == ["scoperta"] and abs(co["cum"][-1] - c["robustezza"]["euro"]["profitto"]) < 0.5
        assert len(co["date"]) == len(co["cum"]) == len(co["dd"]) and min(co["dd"]) <= 0 and co["date"][-1] <= "2023-12-31"
        assert c["misure"]["guadagno_medio"] < 20 and c["prova_finale"] is None and c["giudizio"]["prova_finale"] is None
        assert cu["esc"]["mc"]["p5"][-1] < cu["esc"]["mc"]["p50"][-1] < cu["esc"]["mc"]["p95"][-1]
        assert len(s["trade"]["righe"]) == c["backtest"]["n"] and "punti" in s["trade"]["colonne"]
        assert s["codice"]["codice"] == (server.CARTELLA_ESPERIMENTI / ESP / "candidati" / "c01.prc").read_text(encoding="utf-8")
        assert s["commento_ia"] is None or {"data", "modello", "testo"} <= set(s["commento_ia"])
        reg = j("/api/registro")
        assert len(reg["tentativi"]) == reg["conteggio"]["n_prove"] >= 24
        assert len(j(f"/api/registro?famiglia={ESP}-specchio")["tentativi"]) == 12

        # decisione: scrittura valida, rilettura, rifiuti
        corpo = {"stato": "in verifica", "nota": "prova", "verifica": {"data": "2026-11-23", "esito": "confermata", "note": "ok"}}
        base = f"/api/sistemi/{ESP}/c01/decisione"
        st, b = get(base, corpo=corpo)
        assert st == 200 and json.loads(b)["stato"] == "in verifica", (st, b)
        assert json.loads(server.DECISIONI.read_text(encoding="utf-8"))[f"{ESP}/c01"]["verifica"]["esito"] == "confermata"
        assert j(f"/api/sistemi/{ESP}/c01")["decisione"]["nota"] == "prova"
        assert next(r for r in j("/api/sistemi") if r["id"] == "c01")["decisione_stato"] == "in verifica"
        assert get(base, corpo={**corpo, "stato": "boh"})[0] == 400
        assert get(base, corpo={**corpo, "verifica": {"data": "ieri"}})[0] == 400
        assert get(f"/api/sistemi/{ESP}/c99/decisione", corpo=corpo)[0] == 404
        assert get(base, corpo=corpo, origine="http://evil.example")[0] == 403
        assert get(base, corpo=corpo, host="evil.example")[0] == 403
        print("ok cruscotto.test_server")
    finally:
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    main()
