"""Server del cruscotto: solo libreria standard, solo 127.0.0.1, legge `risultati/` e `esperimenti/`.

L'unica scrittura è `risultati/cruscotto/decisioni.json` (POST sulla decisione di un sistema).
"""
from __future__ import annotations

import json
import math
import mimetypes
import re
import subprocess
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import numpy as np
import polars as pl

from motore import giudizio, validazione
from motore.config import RADICE, RISULTATI

HOST, PORTA = "127.0.0.1", 8765
STATIC = Path(__file__).resolve().parent / "static"
CARTELLA_ESPERIMENTI = RISULTATI / "esperimenti"       # risultati dei lanci
DEFINIZIONI = RADICE / "esperimenti"                   # file d'esperimento e resoconti
DECISIONI = RISULTATI / "cruscotto" / "decisioni.json"
CARTELLA_RICERCHE = RISULTATI / "ricerche"             # risultati di `motore.albero lancia`
STATI = ["da guardare", "da approfondire", "in verifica", "live", "scartato"]
ESITI_VERIFICA = ["", "confermata", "non confermata", "inconcludente"]
NOME = re.compile(r"^[A-Za-z0-9_.-]+$")
MAX_CORPO = 64 * 1024
MC_PERCORSI, MC_PASSO = 400, 5
_scrittura = threading.Lock()


class NonTrovato(Exception):
    pass


class RichiestaErrata(Exception):
    pass


# ---------------------------------------------------------------- lettura dei file

def _json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _nomi_esperimenti() -> list[str]:
    if not CARTELLA_ESPERIMENTI.exists():
        return []
    return sorted(d.name for d in CARTELLA_ESPERIMENTI.iterdir() if (d / "riassunto.json").exists())


def _riassunto(nome: str) -> dict:
    if not NOME.match(nome) or not (CARTELLA_ESPERIMENTI / nome / "riassunto.json").exists():
        raise NonTrovato(f"esperimento {nome}")
    return _json(CARTELLA_ESPERIMENTI / nome / "riassunto.json")


def _decisioni() -> dict:
    return _json(DECISIONI) if DECISIONI.exists() else {}


def _decisione(dec: dict, nome: str, id_: str) -> dict:
    d = dec.get(f"{nome}/{id_}", {})
    return {"stato": d.get("stato", STATI[0]), "nota": d.get("nota", ""),
            "verifica": d.get("verifica") or {"data": "", "esito": "", "note": ""}, "aggiornato": d.get("aggiornato")}


def _conta_esiti(righe: list[dict]) -> dict:
    out = {"candidato": 0, "scartato": 0, "non_giudicato": 0}
    for r in righe:
        out[r["esito"] if r.get("esito") in ("candidato", "scartato") else "non_giudicato"] += 1
    return out


def _soglie(r: dict) -> dict:
    """Le soglie in vigore: quelle del riassunto, completate con le costanti attuali di `giudizio.py`."""
    return {"dsr": giudizio.DSR_MIN, "pbo": giudizio.PBO_MAX,
            "guadagno_euro": [list(x) if x[0] != float("inf") else [None, x[1]] for x in giudizio.SOGLIE_GUADAGNO],
            "trade_anno": giudizio.TRADE_ANNO_MIN, "r2": giudizio.R2_MIN, "anni_positivi": giudizio.ANNI_POSITIVI_MIN,
            "fuori_campione": giudizio.FUORI_CAMPIONE_QUOTA_MIN, "rapporto_costi": giudizio.RAPPORTO_COSTI_INDICATIVO,
            **{k: v for k, v in (r.get("soglie") or {}).items() if k in ("guadagno_euro",) and v}}


# ---------------------------------------------------------------- API

def api_esperimenti() -> list[dict]:
    out = []
    for nome in _nomi_esperimenti():
        r = _riassunto(nome)
        out.append({"nome": nome, "intestazione": r["intestazione"], "prove": r["prove"], "pbo": r["pbo"],
                    "soglie": _soglie(r), "n_candidati": len(r["candidati"]),
                    "esiti": _conta_esiti(r["candidati"]), "arricchito": r.get("arricchito")})
    return out


def api_esperimento(nome: str) -> dict:
    r = _riassunto(nome)
    f = DEFINIZIONI / f"{nome}.md"
    r["resoconto"] = f.read_text(encoding="utf-8") if f.exists() else None
    r["soglie"] = _soglie(r)
    r["esiti"] = _conta_esiti(r["candidati"])
    return r


def _lato(intestazione: dict, famiglia: str) -> str:
    lato = intestazione["direzione"]
    if famiglia.endswith("-specchio"):
        lato = "short" if lato == "long" else "long"
    return lato


def api_sistemi() -> list[dict]:
    dec = _decisioni()
    out = []
    for nome in _nomi_esperimenti():
        r = _riassunto(nome)
        ih = r["intestazione"]
        for c in r["candidati"]:
            riga = {**c, "esperimento": nome, "nome": f"{nome}/{c['id']}", "lato": _lato(ih, c["famiglia"]),
                    "barre": ih["barre"], "direzione_esperimento": ih["direzione"],
                    "etichetta": ", ".join(f"{k}={v}" for k, v in (c.get("parametri") or {}).items())}
            riga.update({f"decisione_{k}": v for k, v in _decisione(dec, nome, c["id"]).items() if k in ("stato", "nota")})
            riga["mini"] = _mini(nome, c["id"], c.get("euro_punto"))
            out.append(riga)
    return out


def _completa(nome: str, id_: str, euro_punto: float | None) -> dict | None:
    """Curva netta in euro di 1 CFD IG su tutto il tempo, in ordine di data: holdout all'indietro, scoperta, holdout
    in avanti, ognuno cumulato di seguito al precedente. `segmenti` dice dove inizia e finisce ogni periodo (indici)."""
    cart = CARTELLA_ESPERIMENTI / nome / "candidati"
    fg, ft = cart / f"{id_}_giorn.parquet", cart / f"{id_}_trade.parquet"
    if euro_punto is None or not fg.exists() or not ft.exists():
        return None
    t = pl.read_parquet(ft)
    if "punti" not in t.columns:
        return None
    g = pl.read_parquet(fg).sort("data").select("data").join(
        t.group_by(pl.col("uscita").dt.date().alias("data")).agg(pl.col("punti").sum()), on="data", how="left").fill_null(0.0)
    parti = [("scoperta", g["data"], g["punti"].to_numpy())]
    fh = cart / f"{id_}_holdout.parquet"
    if fh.exists():
        h = pl.read_parquet(fh).sort("data")
        for periodo in ("antico", "indietro", "vicino", "avanti"):     # "indietro": file di prima del 2026-11-22
            x = h.filter(pl.col("periodo") == periodo)
            if x.height:
                parti.append((periodo, x["data"], x["punti"].to_numpy()))
    parti.sort(key=lambda q: q[1][0])
    date, cum, dd, seg, base, picco = [], [], [], [], 0.0, 0.0
    for periodo, d, x in parti:
        c = base + np.cumsum(x * euro_punto)
        picco_c = np.maximum.accumulate(np.maximum(c, picco))
        seg.append([periodo, len(date), len(date) + len(c) - 1])
        date += d.dt.strftime("%Y-%m-%d").to_list()
        cum += np.round(c, 2).tolist()
        dd += np.round(c - picco_c, 2).tolist()
        base, picco = float(c[-1]), float(picco_c[-1])
    return {"date": date, "cum": cum, "dd": dd, "segmenti": seg, "unita": "eur"}


_CACHE_MINI: dict = {}


def _mini(nome: str, id_: str, euro_punto: float | None) -> dict | None:
    """Curva ridotta a circa 60 punti per il grafico piccolo dell'elenco (con gli estremi dei tre periodi)."""
    f = CARTELLA_ESPERIMENTI / nome / "candidati" / f"{id_}_trade.parquet"
    if euro_punto is None or not f.exists():
        return None
    fh = f.with_name(f"{id_}_holdout.parquet")
    chiave = (str(f), f.stat().st_mtime_ns, fh.stat().st_mtime_ns if fh.exists() else None, euro_punto)
    if chiave not in _CACHE_MINI:
        c = _completa(nome, id_, euro_punto)
        if not c:
            _CACHE_MINI[chiave] = None
        else:
            n = len(c["cum"])
            idx = sorted({int(round(i * (n - 1) / 59)) for i in range(60)})
            _CACHE_MINI[chiave] = {"y": [c["cum"][i] for i in idx],
                                   "segmenti": [[p, idx.index(min(idx, key=lambda i: abs(i - a))), idx.index(min(idx, key=lambda i: abs(i - b)))]
                                                for p, a, b in c["segmenti"]]}
    return _CACHE_MINI[chiave]


def _curva(nome: str, id_: str, euro_punto: float | None) -> dict | None:
    cart = CARTELLA_ESPERIMENTI / nome / "candidati"
    f = cart / f"{id_}_giorn.parquet"
    if not f.exists():
        return None
    g = pl.read_parquet(f).sort("data")
    date = g["data"].dt.strftime("%Y-%m-%d").to_list()
    serie = {"esc": g["netto"].to_numpy()}
    ft = cart / f"{id_}_trade.parquet"
    if euro_punto is not None and ft.exists():
        t = pl.read_parquet(ft)
        if "punti" in t.columns:
            d = g.select("data").join(t.group_by(pl.col("uscita").dt.date().alias("data"))
                                      .agg(pl.col("punti").sum()), on="data", how="left").fill_null(0.0)
            serie["eur"] = d["punti"].to_numpy() * euro_punto
    out = {"date": date, "unita": list(serie)}
    for u, x in serie.items():
        c = np.cumsum(x)
        out[u] = {"cum": np.round(c, 4).tolist(), "dd": np.round(c - np.maximum.accumulate(np.maximum(c, 0)), 4).tolist(),
                  "mc": _montecarlo(x)}
    return out


def _montecarlo(x: np.ndarray, blocco: float | None = None) -> dict | None:
    """Bande 5°-50°-95° della curva cumulata con bootstrap a blocchi mobili (seme fisso, `MC_PERCORSI` percorsi)."""
    n = len(x)
    if n < 50:
        return None
    L = int(max(2, min(n // 4, round(blocco or 5))))
    rng = np.random.default_rng(0)
    nb = -(-n // L)
    idx = (rng.integers(0, n, size=(MC_PERCORSI, nb))[:, :, None] + np.arange(L)) % n
    c = np.cumsum(x[idx.reshape(MC_PERCORSI, -1)[:, :n]], axis=1)
    p = np.percentile(c, [5, 50, 95], axis=0)[:, ::MC_PASSO]
    return {"passo": MC_PASSO, "p5": np.round(p[0], 4).tolist(), "p50": np.round(p[1], 4).tolist(),
            "p95": np.round(p[2], 4).tolist(), "percorsi": MC_PERCORSI, "blocco": L}


def _trade(nome: str, id_: str) -> dict | None:
    f = CARTELLA_ESPERIMENTI / nome / "candidati" / f"{id_}_trade.parquet"
    if not f.exists():
        return None
    t = pl.read_parquet(f).with_columns(
        pl.col("ingresso").dt.strftime("%Y-%m-%d %H:%M"), pl.col("uscita").dt.strftime("%Y-%m-%d %H:%M"))
    for col in ("lordo", "netto", "punti"):
        if col in t.columns:
            t = t.with_columns(pl.col(col).round(4))
    return {"colonne": t.columns, "righe": t.rows()}


def _commento(nome: str, id_: str) -> dict | None:
    f = CARTELLA_ESPERIMENTI / nome / "commenti" / f"{id_}.md"
    if not f.exists():
        return None
    testo = f.read_text(encoding="utf-8")
    meta = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", testo, re.S)
    if m:
        for riga in m.group(1).splitlines():
            if ":" in riga:
                k, v = riga.split(":", 1)
                meta[k.strip().lower()] = v.strip()
        testo = testo[m.end():]
    return {"data": meta.get("data"), "modello": meta.get("modello"), "testo": testo.strip()}


def api_sistema(nome: str, id_: str) -> dict:
    if not NOME.match(id_):
        raise NonTrovato(id_)
    r = _riassunto(nome)
    f = CARTELLA_ESPERIMENTI / nome / "candidati" / f"{id_}.json"
    if not f.exists():
        raise NonTrovato(f"{nome}/{id_}")
    c = _json(f)
    riga = next((x for x in r["candidati"] if x["id"] == id_), {})
    euro_punto = ((c.get("robustezza") or {}).get("euro") or {}).get("euro_punto")
    curva = _curva(nome, id_, euro_punto)
    blocco = (((c.get("scheda") or {}).get("6_montecarlo")) or {}).get("lungh_blocco")
    if curva and blocco:
        for u in curva["unita"]:
            if curva[u]["mc"]:
                x = np.diff(np.array(curva[u]["cum"]), prepend=0.0)
                curva[u]["mc"] = _montecarlo(x, blocco)
    prc = c.get("prorealcode") or None
    cod = CARTELLA_ESPERIMENTI / nome / "candidati" / f"{id_}.prc"
    if prc is None and cod.exists():
        prc = {"codice": cod.read_text(encoding="utf-8"), "completo": None, "da_tradurre": []}
    return {"nome": f"{nome}/{id_}", "esperimento": nome, "id": id_, "intestazione": r["intestazione"],
            "soglie": _soglie(r), "riga": riga, "lato": _lato(r["intestazione"], c.get("famiglia", "")),
            "scheda": c, "curva": curva, "completa": _completa(nome, id_, euro_punto), "trade": _trade(nome, id_), "codice": prc,
            "commento_ia": _commento(nome, id_), "decisione": _decisione(_decisioni(), nome, id_)}


def _stato_ricerca(d: Path) -> dict | None:
    f = d / "stato.json"
    return _json(f) if f.exists() else None


def api_ricerche() -> list[dict]:
    """Tutte le ricerche, dalla più recente: quelle nuove (ampiezza e profondità, anche in corso) e quelle del
    formato precedente (solo ampiezza, `risultati/esperimenti`)."""
    out = []
    if CARTELLA_RICERCHE.exists():
        for d in CARTELLA_RICERCHE.iterdir():
            f, st = d / "ricerca.json", _stato_ricerca(d)
            if f.exists():
                a = _json(f)
                imb = a.get("imbuto") or []
                out.append({"nome": d.name, "formato": "ricerca", "stato": "finita", "prodotto": a["intestazione"]["prodotto"],
                            "barre": a["intestazione"]["barre"], "quando": a["quando"], "prove": a["prove"], "budget": a["budget"],
                            "ampiezza": imb[0]["n"] if imb else None, "radici": sum(1 for n in a["nodi"] if n.get("livello1")),
                            "finali": len(a["foglie"]), "candidati": sum(x["esito"] == "candidato" for x in a["foglie"]),
                            "ipotesi": a["intestazione"].get("ipotesi")})
            elif st:
                out.append({"nome": d.name, "formato": "ricerca", "stato": st.get("stato"), "quando": st.get("inizio"),
                            "prove": st.get("prove"), "budget": st.get("budget"), "fase": st.get("fase"), "errore": st.get("errore")})
    for nome in _nomi_esperimenti():
        r = _riassunto(nome)
        ih = r["intestazione"]
        out.append({"nome": nome, "formato": "esperimento", "stato": "finita", "prodotto": ", ".join(ih["prodotti"]), "barre": ih["barre"],
                    "quando": ih.get("quando") or "", "prove": r["prove"]["questa"], "budget": None, "ampiezza": r["prove"]["questa"],
                    "radici": None, "finali": len(r["candidati"]), "candidati": sum(c.get("esito") == "candidato" for c in r["candidati"]),
                    "ipotesi": ih.get("ipotesi")})
    return sorted(out, key=lambda x: x.get("quando") or "", reverse=True)


def api_ricerca(nome: str) -> dict:
    if not NOME.match(nome):
        raise NonTrovato(nome)
    d = CARTELLA_RICERCHE / nome
    f = d / "ricerca.json"
    if not f.exists():
        st = _stato_ricerca(d)
        if st is None:
            raise NonTrovato(nome)
        return {"nome": nome, "in_corso": True, **st}
    a = _json(f)
    a["nome"] = nome
    a["soglie_guadagno"] = [[None if math.isinf(x) else x, e] for x, e in giudizio.SOGLIE_GUADAGNO]
    return a


_VERSIONE: dict = {}


def api_versione() -> dict:
    """Ultima modifica del software (commit git), per sapere quale versione sta girando."""
    if not _VERSIONE:
        try:
            out = subprocess.run(["git", "log", "-1", "--format=%h|%cI|%s"], cwd=RADICE, capture_output=True, text=True,
                                 timeout=5, encoding="utf-8").stdout.strip()
            h, quando, titolo = out.split("|", 2)
            _VERSIONE.update({"commit": h, "quando": quando, "titolo": titolo})
        except (OSError, ValueError, subprocess.SubprocessError):
            _VERSIONE.update({"commit": None, "quando": None, "titolo": None})
        _VERSIONE["avviato"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return _VERSIONE


def api_registro(famiglia: str | None) -> dict:
    righe = validazione._righe()
    famiglie = sorted({r["famiglia"] for r in righe})
    sel = [r for r in righe if not famiglia or r["famiglia"] == famiglia]
    return {"famiglie": famiglie, "tentativi": sel, "conteggio": validazione.conteggio(famiglia or None)}


def salva_decisione(nome: str, id_: str, corpo: dict) -> dict:
    api_sistema_esiste(nome, id_)
    stato, nota, ver = corpo.get("stato"), corpo.get("nota", ""), corpo.get("verifica") or {}
    if stato not in STATI:
        raise RichiestaErrata(f"stato non valido: {stato!r}")
    if not isinstance(nota, str) or len(nota) > 10000:
        raise RichiestaErrata("nota: testo fino a 10000 caratteri")
    if not isinstance(ver, dict) or any(not isinstance(ver.get(k, ""), str) for k in ("data", "esito", "note")):
        raise RichiestaErrata("verifica: serve {data, esito, note} di testi")
    if ver.get("esito", "") not in ESITI_VERIFICA:
        raise RichiestaErrata("verifica.esito non valido")
    if ver.get("data") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", ver["data"]):
        raise RichiestaErrata("verifica.data: AAAA-MM-GG")
    voce = {"stato": stato, "nota": nota,
            "verifica": {"data": ver.get("data", ""), "esito": ver.get("esito", ""), "note": ver.get("note", "")[:10000]},
            "aggiornato": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    with _scrittura:
        dec = _decisioni()
        dec[f"{nome}/{id_}"] = voce
        DECISIONI.parent.mkdir(parents=True, exist_ok=True)
        tmp = DECISIONI.with_suffix(".tmp")
        tmp.write_text(json.dumps(dec, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(DECISIONI)
    return _decisione({f"{nome}/{id_}": voce}, nome, id_)


def api_sistema_esiste(nome: str, id_: str) -> None:
    _riassunto(nome)
    if not NOME.match(id_) or not (CARTELLA_ESPERIMENTI / nome / "candidati" / f"{id_}.json").exists():
        raise NonTrovato(f"{nome}/{id_}")


# ---------------------------------------------------------------- HTTP

class Gestore(BaseHTTPRequestHandler):
    server_version = "Cruscotto"

    def log_message(self, *a):          # niente righe di log a ogni richiesta
        pass

    # risposte
    def _invia(self, codice: int, corpo: bytes, tipo: str):
        self.send_response(codice)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, dati, codice: int = 200):
        self._invia(codice, json.dumps(dati, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
                    "application/json; charset=utf-8")

    def _errore(self, codice: int, messaggio: str):
        self._json({"errore": messaggio}, codice)

    def _host_ok(self) -> bool:
        porta = self.server.server_address[1]
        return self.headers.get("Host", "") in (f"127.0.0.1:{porta}", f"localhost:{porta}")

    def _percorso(self):
        u = urlparse(self.path)
        return [unquote(p) for p in u.path.split("/") if p], parse_qs(u.query)

    # metodi
    def do_GET(self):
        if not self._host_ok():
            return self._errore(403, "host non ammesso")
        try:
            parti, q = self._percorso()
            if parti[:1] == ["api"]:
                return self._json(self._api_get(parti[1:], q))
            return self._statico(parti)
        except NonTrovato as e:
            self._errore(404, f"non trovato: {e}")
        except Exception as e:      # noqa: BLE001 - l'errore va al browser, il server resta su
            self._errore(500, f"{type(e).__name__}: {e}")

    def do_POST(self):
        if not self._host_ok():
            return self._errore(403, "host non ammesso")
        origine = self.headers.get("Origin")
        if origine and origine not in (f"http://127.0.0.1:{self.server.server_address[1]}",
                                       f"http://localhost:{self.server.server_address[1]}"):
            return self._errore(403, "origine non ammessa")
        try:
            parti, _ = self._percorso()
            if not (len(parti) == 5 and parti[:2] == ["api", "sistemi"] and parti[4] == "decisione"):
                raise NonTrovato(self.path)
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                raise RichiestaErrata("serve application/json")
            n = int(self.headers.get("Content-Length", "0"))
            if n <= 0 or n > MAX_CORPO:
                raise RichiestaErrata("corpo vuoto o troppo grande")
            corpo = json.loads(self.rfile.read(n).decode("utf-8"))
            if not isinstance(corpo, dict):
                raise RichiestaErrata("serve un oggetto JSON")
            self._json(salva_decisione(parti[2], parti[3], corpo))
        except NonTrovato as e:
            self._errore(404, f"non trovato: {e}")
        except (RichiestaErrata, ValueError) as e:
            self._errore(400, str(e))
        except Exception as e:      # noqa: BLE001
            self._errore(500, f"{type(e).__name__}: {e}")

    def _api_get(self, p: list[str], q: dict):
        if p == ["esperimenti"]:
            return api_esperimenti()
        if len(p) == 2 and p[0] == "esperimenti":
            return api_esperimento(p[1])
        if p == ["sistemi"]:
            return api_sistemi()
        if len(p) == 3 and p[0] == "sistemi":
            return api_sistema(p[1], p[2])
        if p == ["ricerche"]:
            return api_ricerche()
        if len(p) == 2 and p[0] == "ricerche":
            return api_ricerca(p[1])
        if p == ["versione"]:
            return api_versione()
        if p == ["registro"]:
            return api_registro((q.get("famiglia") or [None])[0])
        raise NonTrovato("/".join(["api", *p]))

    def _statico(self, parti: list[str]):
        rel = "/".join(parti) or "index.html"
        f = (STATIC / rel).resolve()
        if STATIC.resolve() not in f.parents or not f.is_file():
            raise NonTrovato(rel)
        tipo = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo in ("application/javascript", "application/json"):
            tipo += "; charset=utf-8"
        self._invia(200, f.read_bytes(), tipo)


def crea_server(porta: int = PORTA) -> ThreadingHTTPServer:
    """Server legato solo a 127.0.0.1 (non si raggiunge dalla rete)."""
    return ThreadingHTTPServer((HOST, porta), Gestore)


def avvia(porta: int = PORTA, apri: bool = True) -> None:
    srv = crea_server(porta)
    url = f"http://{HOST}:{porta}/"
    print(f"Cruscotto su {url}  (Ctrl+C per fermarlo)")
    if apri:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
