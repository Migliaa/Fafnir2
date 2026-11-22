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


def main():
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
        assert cu["esc"]["mc"]["p5"][-1] < cu["esc"]["mc"]["p50"][-1] < cu["esc"]["mc"]["p95"][-1]
        assert len(s["trade"]["righe"]) == c["backtest"]["n"] and "punti" in s["trade"]["colonne"]
        assert s["codice"]["codice"] == (server.CARTELLA_ESPERIMENTI / ESP / "candidati" / "c01.prc").read_text(encoding="utf-8")
        assert s["commento_ia"] is None or {"data", "modello", "testo"} <= set(s["commento_ia"])
        reg = j("/api/registro")
        assert len(reg["tentativi"]) == reg["conteggio"]["n_prove"] == 24
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
