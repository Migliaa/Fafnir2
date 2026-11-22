"""Campagna di ricerche a cicli: più prodotti, tutti e due i lati, più timeframe, ognuna con la prova sul rumore.

Ogni combinazione (prodotto, lato, barre) è una ricerca di `motore/ricerca.py` con nome `<campagna>-<prodotto>-<lato>-<barre>m`.
Le ricerche girano in parallelo su più processi (`lavoratori`); una ricerca già finita non si rifà, quindi una campagna
interrotta riprende da dove era. Alla fine il riepilogo `risultati/campagne/<nome>/campagna.json` mette insieme i finali
di tutte le ricerche e prova ognuno, con la stessa regola, sugli altri prodotti della campagna (stesso lato e timeframe):
una regola che guadagna anche su altre valute negli stessi anni è meno probabilmente fortuna.

Uso: python -m motore.campagna controlla|lancia <file.json>
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from . import albero, catalogo, metriche, ricerca
from .config import RISULTATI

CARTELLA = RISULTATI / "campagne"
LATI = {1: "long", -1: "short"}


def carica(file) -> dict:
    return json.loads(Path(file).read_text(encoding="utf-8"))


def ricerche(spec: dict) -> list[dict]:
    """Le specifiche delle ricerche della campagna, una per prodotto, lato e timeframe."""
    out = []
    for prod in spec["prodotti"]:
        gem = next((g for g in catalogo.prodotto(prod).gemelli if g in catalogo.CATALOGO), None)
        for barre in spec["barre"]:
            for lato in spec["lati"]:
                out.append({
                    "tipo": "cicli", "campagna": spec["nome"], "nome": f"{spec['nome']}-{prod}-{LATI[lato]}-{barre}m",
                    "ipotesi": spec["ipotesi"], "meccanismo": spec["meccanismo"], "fonte": spec["fonte"],
                    "prodotto": prod, "gemello": gem, "barre": int(barre), "lato": int(lato),
                    "forza_bruta": {"orari": {**spec["orari"], "passo": int(barre)}, "uscite": spec["uscite"][str(barre)]},
                    "cicli": spec.get("cicli", {}), "rumore": spec.get("rumore", {}), "uscite_finali": spec.get("uscite_finali", []),
                    "seme": spec.get("seme", 0)})
    return out


def controlla(file) -> dict:
    s = carica(file)
    errori = [f"manca '{k}'" for k in ("nome", "prodotti", "lati", "barre", "orari", "uscite", "ipotesi", "meccanismo", "fonte") if k not in s]
    if s.get("tipo") != "campagna":
        errori.append("tipo deve essere 'campagna'")
    for p in s.get("prodotti", []):
        try:
            pr = catalogo.prodotto(p)
            if pr.euro_punto is None:
                errori.append(f"{p}: valore del punto in euro non noto")
            if pr.spread is None:
                errori.append(f"{p}: costi IG non noti")
        except KeyError:
            errori.append(f"prodotto sconosciuto {p}")
    for b in s.get("barre", []):
        if str(b) not in s.get("uscite", {}):
            errori.append(f"mancano le uscite per le barre da {b} minuti")
    for lato in s.get("lati", []):
        if lato not in LATI:
            errori.append(f"lato {lato} non valido")
    n = 0
    if not errori:
        for r in ricerche(s):
            o = r["forza_bruta"]["orari"]
            n += len(ricerca.MX.orari(o["da"], o["a"], o["passo"])) * len(r["forza_bruta"]["uscite"]) * (1 + len(ricerca.pattern.dello_strato(1)))
    return {"file": str(file), "ok": not errori, "errori": errori, "ricerche": len(ricerche(s)) if not errori else 0, "prove_forza_bruta": n}


def _una(spec: dict, cartella_log: str, prepara: str | None = None) -> dict:
    """Lavoro di un processo: una ricerca intera, con il registro di quello che fa su file."""
    if prepara:
        modulo, funzione = prepara.split(":")
        getattr(__import__(modulo, fromlist=[funzione]), funzione)()
    log = Path(cartella_log) / f"{spec['nome']}.log"
    with open(log, "a", encoding="utf-8") as f:
        def scrivi(*a):
            f.write(" ".join(str(x) for x in a) + "\n")
            f.flush()
        t0 = time.time()
        try:
            r = ricerca.lancia_spec(spec, scrivi)
            return {"nome": spec["nome"], "stato": "finita", "durata_s": round(time.time() - t0, 1), "prove": r["prove"]}
        except Exception as ex:      # noqa: BLE001 - una ricerca fallita non ferma la campagna
            scrivi(traceback.format_exc())
            return {"nome": spec["nome"], "stato": "fallita", "errore": f"{type(ex).__name__}: {ex}"}


PREPARA_LAVORATORI = None   # "modulo:funzione" chiamata in ogni processo (i test installano dati finti)


def lancia(file, log=print, lavoratori: int | None = None) -> dict:
    c = controlla(file)
    if not c["ok"]:
        raise ValueError("; ".join(c["errori"]))
    spec = carica(file)
    cart = CARTELLA / spec["nome"]
    cart.mkdir(parents=True, exist_ok=True)
    (cart / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    (cart / "campagna.json").unlink(missing_ok=True)       # il riepilogo vecchio non vale più finché la campagna gira
    tutte = ricerche(spec)
    da_fare = [r for r in tutte if not (albero.CARTELLA / r["nome"] / "ricerca.json").exists()]
    for r in tutte:                                       # una ricerca interrotta a metà si rifà da capo
        st = albero.CARTELLA / r["nome"] / "stato.json"
        if r in da_fare and st.exists():
            st.unlink()
    n = lavoratori or int(spec.get("lavoratori", 4))
    log(f"campagna {spec['nome']}: {len(tutte)} ricerche, {len(tutte) - len(da_fare)} già fatte, {len(da_fare)} da fare su {n} processi")
    esiti = []
    if n <= 1:
        for r in da_fare:
            esiti.append(_una(r, str(cart), PREPARA_LAVORATORI))
            log(f"  {esiti[-1]['nome']}: {esiti[-1]['stato']}")
    else:
        with ProcessPoolExecutor(max_workers=n) as ex:
            futuri = [ex.submit(_una, r, str(cart), PREPARA_LAVORATORI) for r in da_fare]
            for fu in as_completed(futuri):
                esiti.append(fu.result())
                log(f"  {esiti[-1]['nome']}: {esiti[-1]['stato']} ({len(esiti)}/{len(da_fare)})")
    return riepilogo(spec, esiti, log)


def riepilogo(spec: dict, esiti: list[dict] | None = None, log=print) -> dict:
    """Tutti i finali della campagna in una tabella, con la conferma della stessa regola sugli altri prodotti."""
    cart = CARTELLA / spec["nome"]
    righe, ctx = [], {}
    for r in ricerche(spec):
        f = albero.CARTELLA / r["nome"] / "ricerca.json"
        if not f.exists():
            righe.append({"ricerca": r["nome"], "prodotto": r["prodotto"], "lato": r["lato"], "barre": r["barre"], "stato": "non finita"})
            continue
        a = json.loads(f.read_text(encoding="utf-8"))
        imb = {x["strato"]: x["n"] for x in a.get("imbuto", [])}
        base = {"ricerca": r["nome"], "prodotto": r["prodotto"], "lato": r["lato"], "barre": r["barre"], "stato": "finita",
                "prove": a["prove"], "forza_bruta": imb.get("forza"), "finali_cicli": imb.get("filtro3"),
                "wf_euro": (a.get("walkforward_ricerca") or {}).get("media_esc") and a["walkforward_ricerca"]["media_esc"] * (a.get("euro_per_escursione_oggi") or 0),
                "rumore_finali_medi": _media([g["finali"] for g in ((a.get("rumore") or {}).get("giri") or [])])}
        if not a["foglie"]:
            righe.append({**base, "sistema": None})
        for fo in a["foglie"]:
            m = fo.get("misure_minuto") or {}
            altri = [p for p in spec["prodotti"] if p != r["prodotto"]]
            conf = []
            for p in altri:
                chiave = (p, r["barre"])
                try:
                    if chiave not in ctx:
                        ctx[chiave] = albero.Contesto(p, r["barre"])
                    mm = albero.misure(ctx[chiave], ctx[chiave].trade(fo["regola"]))
                    conf.append({"prodotto": p, "n": mm.get("n"), "media_esc": mm.get("media_esc"), "euro_oggi": mm.get("euro_oggi")})
                except (KeyError, ValueError, FileNotFoundError) as ex:
                    conf.append({"prodotto": p, "errore": str(ex)})
            p_r = next((x.get("valore") for x in fo.get("porte", []) if x["nome"].startswith("Batte la ricerca sul rumore")), None)
            righe.append({**base, "sistema": fo["etichetta"], "id": fo["id"], "esito": fo["esito"], "motivo": fo["motivo"],
                          "euro_oggi": m.get("euro_oggi"), "trade_anno": m.get("trade_anno"), "ore": m.get("ore_medie"), "r2": m.get("r2"),
                          "dd_euro_oggi": m.get("dd_euro_oggi"), "t": m.get("t"), "dsr": fo.get("dsr"), "efficienza_wf": fo.get("efficienza_wf"),
                          "p_rumore": p_r, "conferme": sum(1 for x in conf if (x.get("media_esc") or 0) > 0), "su": len(altri), "altri": conf,
                          "mini": _mini_curva(fo.get("curva"))})
    out = {"nome": spec["nome"], "intestazione": spec, "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "esiti": esiti or [], "righe": righe}
    cart.mkdir(parents=True, exist_ok=True)
    (cart / "campagna.json").write_text(json.dumps(metriche.pulisci(out), ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"riepilogo: {sum(1 for x in righe if x.get('sistema'))} finali, {sum(1 for x in righe if x.get('esito') == 'candidato')} candidati")
    return out


def _media(x):
    return sum(x) / len(x) if x else None


def _mini_curva(c: dict | None, punti: int = 60) -> list:
    if not c or not c.get("cum"):
        return []
    n = len(c["cum"])
    return [c["cum"][round(i * (n - 1) / (punti - 1))] for i in range(punti)]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    comando, file = sys.argv[1], sys.argv[2]
    if comando == "controlla":
        print(json.dumps(controlla(file), ensure_ascii=False, indent=1))
    elif comando == "lancia":
        lancia(file)
    elif comando == "riepilogo":
        riepilogo(carica(file))
    else:
        raise SystemExit("uso: python -m motore.campagna controlla|lancia|riepilogo <file.json>")
