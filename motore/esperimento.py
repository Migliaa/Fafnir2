"""File d'esperimento: controllo contro il budget di prove, lancio e riassunto.

Un esperimento è un file `esperimenti/<nome>.json` (campi in `OBBLIGATORI` e `FACOLTATIVI`); la
griglia dà i valori da provare per alcune chiavi della regola, indicate da un percorso puntato
(`"cond.0.2": [3, 4, 5]`, `"uscita.barre": [50, 100]`, con indici numerici per le liste).

`controlla` verifica il file e il budget; `lancia` prova ogni combinazione con il motore degli
eventi, registra ogni prova, calcola PBO, CPCV e DSR per famiglia e porta i primi `k` al backtest
al minuto e alla scheda. Un file già lanciato non si rilancia: la validazione si fa una sola volta.
"""
from __future__ import annotations

import copy
import json
import math
import re
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import numpy as np
import polars as pl

from . import catalogo, condizioni, dati, metriche, validazione
from .config import RECENTE, RISULTATI, SCOPERTA
from .motori import backtest, eventi

CARTELLA = RISULTATI / "esperimenti"  # i test la sostituiscono con una cartella temporanea

OBBLIGATORI = {"nome": str, "ipotesi": str, "meccanismo": str, "fonte": str, "direzione": str,
               "modo": str, "prodotti": list, "barre": int, "regola": dict}
FACOLTATIVI = {"griglia": dict, "specchio": bool, "sr_obiettivo": (int, float), "k": int}
SOGLIA_DSR, SOGLIA_PBO = 0.95, 0.2


# ---------------------------------------------------------------- percorsi nella regola

def _passi(chiave: str) -> list:
    return [int(p) if p.isdigit() else p for p in chiave.split(".")]


def _esiste(regola, chiave: str) -> bool:
    x = regola
    for p in _passi(chiave):
        if isinstance(x, dict) and isinstance(p, str) and p in x:
            x = x[p]
        elif isinstance(x, list) and isinstance(p, int) and 0 <= p < len(x):
            x = x[p]
        else:
            return False
    return True


def _imposta(regola: dict, parametri: dict) -> dict:
    """Copia della regola con i valori della combinazione messi ai loro percorsi."""
    r = copy.deepcopy(regola)
    for chiave, valore in parametri.items():
        *strada, ultimo = _passi(chiave)
        x = r
        for p in strada:
            x = x[p]
        x[ultimo] = valore
    return r


def _combinazioni(griglia: dict) -> list[dict]:
    chiavi = list(griglia)
    return [dict(zip(chiavi, v)) for v in product(*(griglia[c] for c in chiavi))]


# ---------------------------------------------------------------- controllo

def carica(file) -> dict:
    return json.loads(Path(file).read_text(encoding="utf-8"))


def _budget(e: dict) -> float:
    anni = SCOPERTA[1] - SCOPERTA[0] + 1
    b = metriche.prove_ammesse(anni, float(e.get("sr_obiettivo", 1.0)))
    return b / 2 if e.get("modo") == "verticale" else b


def controlla(file) -> dict:
    """Controlla un file d'esperimento. `ok` è vero solo se non ci sono errori; senza `ok` non si lancia."""
    errori, avvisi = [], []
    out = {"file": str(file), "ok": False, "errori": errori, "avvisi": avvisi}
    try:
        e = carica(file)
    except (OSError, ValueError) as ex:
        errori.append(f"file illeggibile: {ex}")
        return out
    for campo, tipo in OBBLIGATORI.items():
        if campo not in e:
            errori.append(f"campo obbligatorio mancante: {campo}")
        elif not isinstance(e[campo], tipo) or isinstance(e[campo], bool):
            errori.append(f"campo {campo}: tipo atteso {tipo.__name__}")
    for campo, tipo in FACOLTATIVI.items():
        if campo in e and not isinstance(e[campo], tipo):
            errori.append(f"campo {campo}: tipo non valido")
    if errori:
        return out
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", e["nome"]):
        errori.append("nome: solo lettere, cifre, punto, trattino e trattino basso")
    if e["direzione"] not in ("long", "short"):
        errori.append("direzione: 'long' o 'short'")
    if e["modo"] not in ("ampiezza", "verticale"):
        errori.append("modo: 'ampiezza' o 'verticale'")
    if not e["prodotti"] or not all(isinstance(p, str) for p in e["prodotti"]):
        errori.append("prodotti: lista non vuota di nomi")
    for p in e["prodotti"] if isinstance(e["prodotti"], list) else []:
        try:
            if not catalogo.prodotto(p).adatto:
                avvisi.append(f"{p}: prodotto non adatto (costi alti secondo il catalogo)")
        except (KeyError, TypeError):
            errori.append(f"prodotto non nel catalogo: {p}")
    regola = e["regola"]
    if regola.get("lato") not in (1, -1):
        errori.append("regola.lato: 1 o -1")
    elif e["direzione"] in ("long", "short") and (regola["lato"] > 0) != (e["direzione"] == "long"):
        errori.append("direzione non coerente con regola.lato")
    griglia = e.get("griglia", {})
    for chiave, valori in griglia.items():
        if not isinstance(valori, list) or not valori:
            errori.append(f"griglia.{chiave}: serve una lista non vuota")
        if not _esiste(regola, chiave):
            errori.append(f"griglia.{chiave}: la chiave non esiste nella regola")
    if errori:
        return out

    comb = math.prod(len(v) for v in griglia.values())
    molt = len(e["prodotti"]) * (2 if e.get("specchio") else 1)
    nome = e["nome"]
    pregresse = sum(1 for r in validazione._righe() if r["famiglia"] in (nome, nome + "-specchio"))
    prove = comb * molt + pregresse
    budget = _budget(e)
    massimo = max(0, math.floor((budget - pregresse) / molt))
    out.update({"combinazioni": comb, "prove": prove, "pregresse": pregresse, "budget": round(budget, 1),
                "max_combinazioni": massimo})
    if prove > budget:
        errori.append(f"{prove} prove oltre il budget di {budget:.0f}: al massimo {massimo} combinazioni")
    if (CARTELLA / nome / "riassunto.json").exists():
        errori.append("esperimento già lanciato")
    out["ok"] = not errori
    return out


# ---------------------------------------------------------------- lancio

def _giornaliera(trade: pl.DataFrame, date: pl.Series) -> np.ndarray:
    """Profitto netto per giorno di borsa (zeri compresi), attribuito al giorno d'uscita."""
    return (pl.DataFrame({"data": date}).join(
        trade.group_by(pl.col("uscita").dt.date().alias("data")).agg(pl.col("netto").sum()),
        on="data", how="left").fill_null(0.0)["netto"].to_numpy())


def _n_effettivo(c: dict) -> float:
    """Numero effettivo di prove per il DSR: il più alto fra le due stime del registro (più prudente)."""
    v = [x for x in (c["n_effettivo_autovalori"], c["n_effettivo_cluster"]) if x is not None]
    return max(1.0, max(v)) if v else float(max(1, c["n_prove"]))


def lancia(file, n_mc: int = 2000) -> dict:
    """Lancia l'esperimento e scrive i risultati in `CARTELLA/<nome>/`. Restituisce il riassunto."""
    e = carica(file)
    if "nome" in e and (CARTELLA / str(e["nome"]) / "riassunto.json").exists():
        raise ValueError(f"{e['nome']}: esperimento già lanciato, la validazione si fa una volta sola")
    c = controlla(file)
    if not c["ok"]:
        raise ValueError("controllo non superato: " + "; ".join(c["errori"]))
    nome, minuti, k = e["nome"], e["barre"], int(e.get("k", 10))
    griglia = e.get("griglia", {})
    combinazioni = _combinazioni(griglia)
    famiglie = {nome: e["regola"]}
    if e.get("specchio"):
        famiglie[nome + "-specchio"] = condizioni.specchia(e["regola"])

    # 1. ogni prova con il motore degli eventi, registrata con la sua serie giornaliera
    tabelle, date, prove = {}, {}, []
    for prod in e["prodotti"]:
        tabelle[prod] = eventi.base(prod, minuti)
        date[prod] = tabelle[prod]["data"].unique().sort()
    for fam, regola_fam in famiglie.items():
        for prod in e["prodotti"]:
            for par in combinazioni:
                regola = _imposta(regola_fam, par)
                _, trade = eventi.prova(prod, minuti, regola, tabelle[prod])
                g = _giornaliera(trade, date[prod])
                id_ = validazione.registra(nome, fam, prod, par, g, date[prod].to_numpy())
                prove.append({"famiglia": fam, "prodotto": prod, "parametri": par, "regola": regola,
                              "id_registro": id_, "giorn": g, "sharpe": metriche.sharpe(g)})

    # 2. PBO e CPCV per famiglia e prodotto, DSR per ogni prova
    pbo, cpcv = {}, {}
    for fam in famiglie:
        pbo[fam], cpcv[fam] = {}, {}
        for prod in e["prodotti"]:
            sel = [p for p in prove if p["famiglia"] == fam and p["prodotto"] == prod]
            mat = np.column_stack([p["giorn"] for p in sel])
            d = date[prod].to_numpy()
            pbo[fam][prod] = validazione.pbo(mat) if mat.shape[1] >= 4 else None
            try:
                cpcv[fam][prod] = validazione.cpcv_selezione(mat, d)
            except (ValueError, IndexError):
                cpcv[fam][prod] = None
    conteggi = {fam: validazione.conteggio(fam) for fam in famiglie}
    for p in prove:
        cn = conteggi[p["famiglia"]]
        v = cn["var_sharpe"] if cn["var_sharpe"] is not None else 0.0
        p["dsr"] = metriche.dsr(p["giorn"], _n_effettivo(cn), v)
    chiave = lambda p: (-math.inf if not math.isfinite(p["dsr"]) else p["dsr"],
                        -math.inf if not math.isfinite(p["sharpe"]) else p["sharpe"])
    prove.sort(key=chiave, reverse=True)

    # 3-4. i primi k al backtest al minuto e alla scheda; scrittura dei file
    cartella = CARTELLA / nome
    (cartella / "candidati").mkdir(parents=True, exist_ok=True)
    minuti_prod, righe = {}, []
    for rango, p in enumerate(prove[:k], 1):
        prod, fam = p["prodotto"], p["famiglia"]
        if prod not in minuti_prod:
            minuti_prod[prod] = dati.minuti(prod)
        rias, trade = backtest.simula(prod, minuti, p["regola"], tabelle[prod], minuti_prod[prod])
        id_ = f"c{rango:02d}"
        riga = {"id": id_, "prodotto": prod, "famiglia": fam, "parametri": p["parametri"], "n": rias["n"],
                "dsr_eventi": p["dsr"], "id_registro": p["id_registro"], "passa": False}
        scheda = None
        if trade.height >= 5:
            g = _giornaliera(trade, date[prod])
            cn = conteggi[fam]
            scheda = metriche.scheda(g, date[prod].to_numpy(), trade["netto"].to_numpy(),
                                     n_prove=_n_effettivo(cn), var_sr_prove=cn["var_sharpe"] or 0.0,
                                     cpcv=cpcv[fam][prod], pbo=pbo[fam][prod], n_mc=n_mc)
            dsr = scheda["1_sharpe"]["dsr"]
            pb = (pbo[fam][prod] or {}).get("pbo")
            riga.update({"media": rias.get("media_esc"), "pf": rias.get("pf"), "sharpe": rias.get("sharpe"),
                         "dsr": dsr, "anni_positivi": rias.get("anni_positivi"),
                         f"media_{RECENTE[0]}_{RECENTE[1]}": rias.get("media_recente_esc"), "pbo": pb,
                         "passa": bool(dsr is not None and dsr > SOGLIA_DSR and pb is not None and pb < SOGLIA_PBO)})
            g_df = pl.DataFrame({"data": date[prod], "netto": g})
            g_df.write_parquet(cartella / "candidati" / f"{id_}_giorn.parquet")
        trade.write_parquet(cartella / "candidati" / f"{id_}_trade.parquet")
        completa = metriche.pulisci({"id": id_, "esperimento": nome, "prodotto": prod, "famiglia": fam,
                                     "parametri": p["parametri"], "regola": p["regola"], "backtest": rias,
                                     "scheda": scheda})
        (cartella / "candidati" / f"{id_}.json").write_text(
            json.dumps(completa, ensure_ascii=False, indent=1), encoding="utf-8")
        righe.append(metriche.pulisci(riga))

    riassunto = metriche.pulisci({
        "intestazione": {**{c: e[c] for c in ("nome", "ipotesi", "meccanismo", "fonte", "direzione", "modo")},
                         "barre": minuti, "prodotti": e["prodotti"], "specchio": bool(e.get("specchio")),
                         "quando": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        "prove": {"questa": len(prove), "totali_registro": c["prove"], "budget": c["budget"],
                  "n_effettivo": {fam: _n_effettivo(cn) for fam, cn in conteggi.items()}},
        "pbo": {fam: {prod: (v or {}).get("pbo") for prod, v in d.items()} for fam, d in pbo.items()},
        "soglie": {"dsr": SOGLIA_DSR, "pbo": SOGLIA_PBO},
        "candidati": righe})
    # scritto per ultimo: la sua esistenza segna l'esperimento come lanciato
    (cartella / "riassunto.json").write_text(
        json.dumps(riassunto, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return riassunto


def riassunto(nome: str) -> dict:
    return json.loads((CARTELLA / nome / "riassunto.json").read_text(encoding="utf-8"))
