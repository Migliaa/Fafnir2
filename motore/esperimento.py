"""File d'esperimento: controllo contro il budget di prove, lancio e riassunto.

Un esperimento è un file `esperimenti/<nome>.json` (campi in `OBBLIGATORI` e `FACOLTATIVI`); la
griglia dà i valori da provare per alcune chiavi della regola, indicate da un percorso puntato
(`"cond.0.2": [3, 4, 5]`, `"uscita.barre": [50, 100]`, con indici numerici per le liste).

`controlla` verifica il file e il budget; `lancia` prova ogni combinazione con il motore degli
eventi (su più processi), registra ogni prova, applica subito i filtri di Andrea (`giudizio.py`), calcola PBO,
CPCV e DSR per famiglia e porta i primi `k` sopravvissuti al backtest al minuto e alla scheda. `arricchisci`
aggiunge robustezza, giudizio completo e, solo per chi ha passato tutto sulla scoperta, la prova finale
(`prova_finale.py`). Un file già lanciato non si rilancia: la validazione si fa una sola volta.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import math
import os
import pickle
import re
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import numpy as np
import polars as pl

from . import catalogo, condizioni, dati, giudizio, metriche, prova_finale, robustezza, uscita, validazione
from .config import RECENTE, RISULTATI, SCOPERTA
from .motori import backtest, eventi

CARTELLA = RISULTATI / "esperimenti"  # i test la sostituiscono con una cartella temporanea

OBBLIGATORI = {"nome": str, "ipotesi": str, "meccanismo": str, "fonte": str, "direzione": str,
               "modo": str, "prodotti": list, "barre": int, "regola": dict}
FACOLTATIVI = {"griglia": dict, "specchio": bool, "sr_obiettivo": (int, float), "k": int}
PREPARA_LAVORATORI = None   # "modulo:funzione" chiamata in ogni processo prima di leggere i dati (i test installano dati finti)
LOTTO = 50                  # prove per lotto di lavoro
SALVA_OGNI = 1000           # prove fra due salvataggi intermedi


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
    anni = SCOPERTA[1] - SCOPERTA[0] + 1
    sr_min = math.sqrt(2 * math.log(max(prove * (2 if e.get("modo") == "verticale" else 1), 2)) / anni)
    out.update({"combinazioni": comb, "prove": prove, "pregresse": pregresse, "budget": round(budget, 1),
                "max_combinazioni": massimo, "sr_minimo": round(sr_min, 3),
                "sr_obiettivo": float(e.get("sr_obiettivo", 1.0))})
    if prove > budget:
        errori.append(f"{prove} prove oltre il budget di {budget:.0f}: al massimo {massimo} combinazioni; "
                      f"{prove} prove richiedono sr_obiettivo >= {sr_min:.2f}")
    if (CARTELLA / nome / "riassunto.json").exists():
        errori.append("esperimento già lanciato")
    out["ok"] = not errori
    return out


# ---------------------------------------------------------------- lancio

def _giornaliera(trade: pl.DataFrame, date, colonna: str = "netto") -> np.ndarray:
    """Somma di `colonna` per giorno di borsa (zeri compresi), attribuita al giorno d'uscita."""
    d = date.to_numpy() if hasattr(date, "to_numpy") else np.asarray(date)
    d = d.astype("datetime64[D]")
    if not trade.height:
        return np.zeros(len(d))
    giorno = np.minimum(np.searchsorted(d, trade["uscita"].dt.date().to_numpy().astype("datetime64[D]")), len(d) - 1)
    return np.bincount(giorno, weights=trade[colonna].to_numpy(), minlength=len(d))


def _n_effettivo(c: dict) -> float:
    """Numero effettivo di prove per il DSR: il più alto fra le due stime del registro (più prudente)."""
    v = [x for x in (c["n_effettivo_autovalori"], c["n_effettivo_cluster"]) if x is not None]
    return max(1.0, max(v)) if v else float(max(1, c["n_prove"]))


# stato di ogni processo di lavoro: tabelle di base e regole, costruite una volta
_W: dict = {}


def _inizia(spec: dict) -> None:
    if spec.get("prepara"):
        modulo, funzione = spec["prepara"].split(":")
        getattr(importlib.import_module(modulo), funzione)()
    tabelle = spec.get("tabelle") or {p: eventi.base(p, spec["barre"]) for p in spec["prodotti"]}
    _W.clear()
    _W.update({"tabelle": tabelle, "regole": spec["regole"], "combinazioni": spec["combinazioni"], "barre": spec["barre"],
               "date": {p: t["data"].unique().sort().to_numpy().astype("datetime64[D]") for p, t in tabelle.items()},
               "ep": {p: catalogo.prodotto(p).euro_punto for p in tabelle}})


def _inizia_da_file(percorso: str) -> None:
    """Come `_inizia`, con la specifica letta da un file: passarla nei parametri dell'avvio la farebbe scrivere nel
    canale verso il nuovo processo, e su Windows chi avvia resta fermo finché quello non parte (secondi a testa)."""
    _inizia(pickle.loads(Path(percorso).read_bytes()))


def _lavora(lotto: list) -> list:
    """Prova un lotto di (famiglia, prodotto, indice di combinazione): serie giornaliera netta in escursioni e
    misure in euro per i filtri, calcolate sui trade del motore degli eventi."""
    out = []
    for fam, prod, i in lotto:
        regola = _imposta(_W["regole"][fam], _W["combinazioni"][i])
        tab = _W["tabelle"][prod]
        _, trade = eventi.prova(prod, _W["barre"], regola, tab, riassumi=False)
        g = _giornaliera(trade, _W["date"][prod])
        m = giudizio.misure(trade, _W["date"][prod], _W["ep"][prod], tab.height, SCOPERTA)
        out.append((fam, prod, i, g, m))
    return out


def _barra(fatte: int, tot: int, t0: float, ultima: list, forza: bool = False) -> None:
    ora = time.perf_counter()
    if not forza and ora - ultima[0] < 0.5:
        return
    ultima[0] = ora
    trascorso = ora - t0
    eta = trascorso / fatte * (tot - fatte) if fatte else 0
    pieno = int(30 * fatte / tot)
    sys.stderr.write(f"\r[{'#' * pieno}{'.' * (30 - pieno)}] {fatte}/{tot} {100 * fatte / tot:3.0f}%  "
                     f"{trascorso:5.0f}s, ne mancano ~{eta:.0f}s ")
    sys.stderr.flush()


def _identita(file) -> str:
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def _esegui_lotti(lotti: list, spec: dict, lavoratori: int, cartella: Path, riprendi: bool, ident: str,
                  usa) -> None:
    """Esegue i lotti di lavoro (in parallelo se `lavoratori` > 1), con barra su stderr e salvataggi intermedi
    ogni `SALVA_OGNI` prove in `cartella/_parziale`; `usa(lotto_id, risultati)` riceve ogni lotto finito."""
    par = cartella / "_parziale"
    fatti: set[int] = set()
    if par.exists():
        if not riprendi:
            raise ValueError(f"c'è un lancio interrotto in {par}: usa --riprendi per continuarlo o cancella la cartella")
        info = json.loads((par / "identita.json").read_text(encoding="utf-8"))
        if info["file"] != ident or info["lotto"] != spec["lotto"]:
            raise ValueError("il lancio interrotto è di un altro file d'esperimento: non si può riprendere")
        for f in sorted(par.glob("parte_*.pkl")):
            for lid, ris in pickle.loads(f.read_bytes()).items():
                fatti.add(lid)
                usa(lid, ris)
    else:
        if riprendi:
            raise ValueError("non c'è nessun lancio interrotto da riprendere")
        par.mkdir(parents=True)
        (par / "identita.json").write_text(json.dumps({"file": ident, "lotto": spec["lotto"]}), encoding="utf-8")
    da_fare = [(i, lotto) for i, lotto in enumerate(lotti) if i not in fatti]
    tot = sum(len(l) for l in lotti)
    fatte = sum(len(lotti[i]) for i in fatti)
    t0, ultima, nuovi, quanti = time.perf_counter(), [0.0], {}, 0
    _barra(fatte, tot, t0, ultima, True)

    def ricevi(lid, ris):
        nonlocal fatte, nuovi, quanti
        usa(lid, ris)
        nuovi[lid] = ris
        fatte += len(lotti[lid])
        quanti += len(lotti[lid])
        if quanti >= SALVA_OGNI and fatte < tot:
            n = len(list(par.glob("parte_*.pkl"))) + 1
            tmp = par / f"parte_{n:04d}.tmp"
            tmp.write_bytes(pickle.dumps(nuovi))
            tmp.replace(par / f"parte_{n:04d}.pkl")
            nuovi, quanti = {}, 0
        _barra(fatte, tot, t0, ultima)

    if lavoratori <= 1:
        _inizia(spec)
        for lid, lotto in da_fare:
            ricevi(lid, _lavora(lotto))
    else:
        file_spec = par / "specifica.pkl"
        file_spec.write_bytes(pickle.dumps({k: v for k, v in spec.items() if k != "tabelle"}))
        with ProcessPoolExecutor(max_workers=lavoratori, initializer=_inizia_da_file, initargs=(str(file_spec),)) as ex:
            for (lid, _), ris in zip(da_fare, ex.map(_lavora, [l for _, l in da_fare])):
                ricevi(lid, ris)
    _barra(fatte, tot, t0, ultima, True)
    sys.stderr.write("\n")
    shutil.rmtree(par, ignore_errors=True)


def _misure_corte(m: dict) -> dict:
    return {k: m.get(k) for k in ("guadagno_medio", "ore_medie", "trade_anno", "r2", "anni_positivi", "utile",
                                  "drawdown", "utile_su_dd", "rapporto_costi", "in_mercato", "n")}


def lancia(file, n_mc: int = 2000, lavoratori: int | None = None, riprendi: bool = False) -> dict:
    """Lancia l'esperimento e scrive i risultati in `CARTELLA/<nome>/`. Restituisce il riassunto.

    `lavoratori` sono i processi (di norma i processori meno uno; uno solo, o poche prove, e si lavora nel
    processo principale). Con `riprendi` si continua un lancio interrotto dal punto dell'ultimo salvataggio."""
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
    tempi: dict = {}
    t_tot = time.perf_counter()
    cartella = CARTELLA / nome
    cartella.mkdir(parents=True, exist_ok=True)

    # 1. ogni prova con il motore degli eventi: serie giornaliera e misure dei filtri, su più processi
    t = time.perf_counter()
    tabelle, date = {}, {}
    for prod in e["prodotti"]:
        tabelle[prod] = eventi.base(prod, minuti)
        date[prod] = tabelle[prod]["data"].unique().sort()
    chiavi = [(fam, prod) for fam in famiglie for prod in e["prodotti"]]
    lavori = [(fam, prod, i) for fam, prod in chiavi for i in range(len(combinazioni))]
    lotti = [lavori[i:i + LOTTO] for i in range(0, len(lavori), LOTTO)]
    nl = lavoratori if lavoratori is not None else (max(1, (os.cpu_count() or 2) - 1) if len(lavori) >= 200 else 1)
    spec = {"barre": minuti, "prodotti": e["prodotti"], "regole": famiglie, "combinazioni": combinazioni,
            "prepara": PREPARA_LAVORATORI, "lotto": LOTTO, "tabelle": tabelle}
    mat = {ch: np.zeros((len(date[ch[1]]), len(combinazioni))) for ch in chiavi}
    misure_prove = {ch: [None] * len(combinazioni) for ch in chiavi}

    def usa(lid, ris):
        for fam, prod, i, g, m in ris:
            mat[(fam, prod)][:, i] = g
            misure_prove[(fam, prod)][i] = m

    _esegui_lotti(lotti, spec, nl, cartella, riprendi, _identita(file), usa)
    tempi["eventi"] = time.perf_counter() - t

    # 2. registro: una scrittura per famiglia e prodotto
    t = time.perf_counter()
    prove = []
    for fam, prod in chiavi:
        d_np = date[prod].to_numpy()
        ids = validazione.registra_molti(nome, fam, prod, [(par, mat[(fam, prod)][:, i]) for i, par in enumerate(combinazioni)], d_np)
        for i, id_ in enumerate(ids):
            g = mat[(fam, prod)][:, i]
            prove.append({"famiglia": fam, "prodotto": prod, "parametri": combinazioni[i], "i": i, "id_registro": id_,
                          "sharpe": metriche.sharpe(g), "misure": misure_prove[(fam, prod)][i]})
    tempi["registro"] = time.perf_counter() - t

    # 3. filtri di Andrea sui risultati degli eventi: scartano quasi tutto prima delle parti costose
    per_motivo: dict = {}

    def conta(motivo):
        tipo = re.sub(r"-?\d[\d.,]*", "#", motivo)         # per tipo di filtro, senza i numeri della singola prova
        per_motivo[tipo] = per_motivo.get(tipo, 0) + 1

    for p in prove:
        p["scarto"] = giudizio._motivo(giudizio.filtri_andrea(p["misure"]))
        if p["scarto"]:
            conta(p["scarto"])
    sopravvissute = [p for p in prove if p["scarto"] is None]

    # 4. PBO e CPCV per famiglia e prodotto (CPCV solo dove ci sono sopravvissute), DSR delle sopravvissute
    t = time.perf_counter()
    pbo, cpcv = {}, {}
    for fam, prod in chiavi:
        m_ = mat[(fam, prod)]
        pbo.setdefault(fam, {})[prod] = validazione.pbo(m_) if m_.shape[1] >= 4 else None
    tempi["pbo"] = time.perf_counter() - t
    t = time.perf_counter()
    for fam, prod in chiavi:
        cpcv.setdefault(fam, {})[prod] = None
        if any(p["famiglia"] == fam and p["prodotto"] == prod for p in sopravvissute):
            try:
                cpcv[fam][prod] = validazione.cpcv_selezione(mat[(fam, prod)], date[prod].to_numpy())
            except (ValueError, IndexError):
                pass
    tempi["cpcv"] = time.perf_counter() - t
    t = time.perf_counter()
    conteggi = {fam: validazione.conteggio(fam) for fam in famiglie}
    tempi["n_effettivo"] = time.perf_counter() - t
    t = time.perf_counter()
    for p in sopravvissute:
        cn = conteggi[p["famiglia"]]
        v = cn["var_sharpe"] if cn["var_sharpe"] is not None else 0.0
        p["dsr"] = metriche.dsr(mat[(p["famiglia"], p["prodotto"])][:, p["i"]], _n_effettivo(cn), v)
        pb = (pbo[p["famiglia"]][p["prodotto"]] or {}).get("pbo")
        voci = giudizio.cancello_statistico(p["dsr"] if math.isfinite(p["dsr"]) else None, pb)
        p["scarto"] = giudizio._motivo(voci)
        if p["scarto"]:
            conta(p["scarto"])
    passano = [p for p in sopravvissute if p["scarto"] is None]
    chiave = lambda p: (p["dsr"], -math.inf if not math.isfinite(p["sharpe"]) else p["sharpe"])
    passano.sort(key=chiave, reverse=True)
    tempi["dsr"] = time.perf_counter() - t

    # 5. file con tutte le prove (per capire dove si è fermata ognuna)
    pl.DataFrame({"id_registro": [p["id_registro"] for p in prove], "famiglia": [p["famiglia"] for p in prove],
                  "prodotto": [p["prodotto"] for p in prove],
                  "parametri": [json.dumps(p["parametri"], ensure_ascii=False) for p in prove],
                  "sharpe": [p["sharpe"] if math.isfinite(p["sharpe"]) else None for p in prove],
                  "guadagno_medio": [p["misure"].get("guadagno_medio") for p in prove],
                  "ore_medie": [p["misure"].get("ore_medie") for p in prove],
                  "trade_anno": [p["misure"].get("trade_anno") for p in prove],
                  "r2": [p["misure"].get("r2") for p in prove],
                  "anni_positivi": [p["misure"].get("anni_positivi") for p in prove],
                  "utile_su_dd": [p["misure"].get("utile_su_dd") for p in prove],
                  "scartata_da": [p["scarto"] for p in prove]}).write_parquet(cartella / "prove.parquet")

    # 6. i primi k che hanno passato tutto vanno al backtest al minuto e alla scheda; scrittura dei file
    (cartella / "candidati").mkdir(parents=True, exist_ok=True)
    minuti_prod, righe = {}, []
    t_bt = t_sc = 0.0
    for rango, p in enumerate(passano[:k], 1):
        prod, fam = p["prodotto"], p["famiglia"]
        if prod not in minuti_prod:
            minuti_prod[prod] = dati.minuti(prod)
        t = time.perf_counter()
        regola = _imposta(famiglie[fam], p["parametri"])
        rias, trade = backtest.simula(prod, minuti, regola, tabelle[prod], minuti_prod[prod])
        t_bt += time.perf_counter() - t
        id_ = f"c{rango:02d}"
        riga = {"id": id_, "prodotto": prod, "famiglia": fam, "parametri": p["parametri"], "n": rias["n"],
                "dsr_eventi": p["dsr"], "id_registro": p["id_registro"], "passa": False,
                "misure_eventi": _misure_corte(p["misure"]), "euro_punto": p["misure"].get("euro_punto")}
        scheda = None
        if trade.height >= 5:
            t = time.perf_counter()
            g = _giornaliera(trade, date[prod])
            cn = conteggi[fam]
            scheda = metriche.scheda(g, date[prod].to_numpy(), trade["netto"].to_numpy(),
                                     n_prove=_n_effettivo(cn), var_sr_prove=cn["var_sharpe"] or 0.0,
                                     cpcv=cpcv[fam][prod], pbo=pbo[fam][prod], n_mc=n_mc)
            t_sc += time.perf_counter() - t
            dsr = scheda["1_sharpe"]["dsr"]
            pb = (pbo[fam][prod] or {}).get("pbo")
            ms = giudizio.misure(trade, date[prod].to_numpy(), catalogo.prodotto(prod).euro_punto, tabelle[prod].height, SCOPERTA)
            motivo = giudizio._motivo(giudizio.filtri_andrea(ms) + giudizio.cancello_statistico(dsr, pb))
            riga.update({"media": rias.get("media_esc"), "pf": rias.get("pf"), "sharpe": rias.get("sharpe"),
                         "dsr": dsr, "anni_positivi": rias.get("anni_positivi"),
                         f"media_{RECENTE[0]}_{RECENTE[1]}": rias.get("media_recente_esc"), "pbo": pb,
                         "misure": _misure_corte(ms), "passa": motivo is None, "motivo": motivo})
            pl.DataFrame({"data": date[prod], "netto": g}).write_parquet(cartella / "candidati" / f"{id_}_giorn.parquet")
        trade.write_parquet(cartella / "candidati" / f"{id_}_trade.parquet")
        completa = metriche.pulisci({"id": id_, "esperimento": nome, "prodotto": prod, "famiglia": fam,
                                     "parametri": p["parametri"], "regola": regola, "backtest": rias,
                                     "scheda": scheda})
        (cartella / "candidati" / f"{id_}.json").write_text(
            json.dumps(completa, ensure_ascii=False, indent=1), encoding="utf-8")
        righe.append(metriche.pulisci(riga))
    tempi["backtest_minuto"], tempi["scheda"] = t_bt, t_sc
    tempi["totale"] = time.perf_counter() - t_tot

    riassunto = metriche.pulisci({
        "intestazione": {**{c: e[c] for c in ("nome", "ipotesi", "meccanismo", "fonte", "direzione", "modo")},
                         "barre": minuti, "prodotti": e["prodotti"], "specchio": bool(e.get("specchio")),
                         "quando": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        "prove": {"questa": len(prove), "totali_registro": c["prove"], "budget": c["budget"],
                  "sr_minimo": c["sr_minimo"], "sr_obiettivo": c["sr_obiettivo"],
                  "n_effettivo": {fam: _n_effettivo(cn) for fam, cn in conteggi.items()},
                  "dopo_filtri": len(sopravvissute), "dopo_cancello": len(passano), "scartate_per": per_motivo},
        "pbo": {fam: {prod: (v or {}).get("pbo") for prod, v in d.items()} for fam, d in pbo.items()},
        "soglie": {"dsr": giudizio.DSR_MIN, "pbo": giudizio.PBO_MAX,
                   "guadagno_euro": [list(x) for x in giudizio.SOGLIE_GUADAGNO], "trade_anno": giudizio.TRADE_ANNO_MIN,
                   "r2": giudizio.R2_MIN, "anni_positivi": giudizio.ANNI_POSITIVI_MIN,
                   "fuori_campione": giudizio.FUORI_CAMPIONE_QUOTA_MIN},
        "tempi": {k_: round(v, 2) for k_, v in tempi.items()},
        "candidati": righe})
    # scritto per ultimo: la sua esistenza segna l'esperimento come lanciato
    (cartella / "riassunto.json").write_text(
        json.dumps(riassunto, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return riassunto


def riassunto(nome: str) -> dict:
    return json.loads((CARTELLA / nome / "riassunto.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- arricchimento per il cruscotto

def arricchisci(nome: str) -> dict:
    """Aggiunge a ogni candidato di un esperimento già lanciato robustezza, giudizio e ProRealCode.

    Scrive `robustezza`, `giudizio`, `misure`, `prova_finale` e `prorealcode` in `candidati/<id>.json`, il codice
    in `<id>.prc`, la colonna `punti` nella tabella dei trade e l'esito di ogni candidato in `riassunto.json`.
    La robustezza è sul periodo della scoperta e il registro non si tocca, salvo per la prova finale: solo se il
    candidato ha passato i filtri e il cancello statistico sulla scoperta si leggono i due holdout (una volta per
    tentativo, `prova_finale.py`); a un secondo giro si riusa il risultato salvato senza rileggere dati."""
    r = riassunto(nome)
    cartella = CARTELLA / nome / "candidati"
    ctx: dict = {}
    for riga in r["candidati"]:
        f = cartella / f"{riga['id']}.json"
        c = json.loads(f.read_text(encoding="utf-8"))
        regola, prod, barre = c["regola"], c["prodotto"], r["intestazione"]["barre"]
        rob, trade = robustezza.calcola(regola, prod, barre, famiglia=c.get("famiglia"),
                                        parametri=c.get("parametri"), ctx=ctx)
        tab = ctx[(prod, barre)][0]
        ms = giudizio.misure(trade, tab["data"].unique().sort().to_numpy(), catalogo.prodotto(prod).euro_punto,
                             tab.height, SCOPERTA)
        giud = giudizio.giudica(c.get("scheda"), rob, ms)
        pf = None
        if giud["passa_scoperta"]:
            pf = prova_finale.esegui(prod, barre, regola, riga["id_registro"], cartella / f"{riga['id']}_holdout.parquet")
            giud = giudizio.giudica(c.get("scheda"), rob, ms, pf)
        prc = uscita.traduci(regola, prod, barre)
        c.update(metriche.pulisci({"robustezza": rob, "giudizio": giud, "prorealcode": prc, "misure": ms,
                                   "prova_finale": pf}))
        f.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
        (cartella / f"{riga['id']}.prc").write_text(prc["codice"], encoding="utf-8")
        trade.write_parquet(cartella / f"{riga['id']}_trade.parquet")
        riga["esito"] = giud["esito"]
        riga["motivo"] = giud["motivo"]
        riga["gruppi"] = {k: g["esito"] for k, g in giud["gruppi"].items()}
        riga["netto_euro"] = metriche.pulisci((rob.get("euro") or {}).get("profitto"))
        riga["misure"] = metriche.pulisci(_misure_corte(ms))
        riga["euro_punto"] = ms["euro_punto"]
        riga["fuori_campione"] = metriche.pulisci((pf or {}).get("avanti"))
    r["arricchito"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (CARTELLA / nome / "riassunto.json").write_text(
        json.dumps(metriche.pulisci(r), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return r
