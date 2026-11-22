"""Ricerca a cicli di Fafnir2: forza bruta, filtro, moltiplicazione, filtro, moltiplicazione, filtro, poi ricalcolo
esatto e verifica (`ricerca/protocollo-albero.md`, sezione "Ricerca a cicli").

1. **Forza bruta**: ogni ora d'ingresso (ogni 5 minuti) × ogni uscita × "nessuna condizione" o un pattern dello strato 1
   (struttura del prezzo, `motore/pattern.py`). Decine di migliaia di regole, sul motore a matrice.
2. **Filtro 1**: guadagno o margine, t >= 2, almeno 8 trade l'anno, fuori campione CPCV positivo, positiva in entrambe le
   metà del periodo; poi i migliori per punteggio, saltando quelli che guadagnano negli stessi giorni (semi).
3. **Moltiplicazione 1**: ogni seme × ogni altro pattern dello strato 1 e dello strato 2 (indicatori e candele).
4. **Filtro 2**: come il filtro 1, più il confronto con il genitore: batte il 95% dei filtri a caso che tolgono la stessa
   quota di trade, migliora il genitore in 2 terzi su 3, i trade tolti vanno peggio.
5. **Moltiplicazione 2**: ogni seme × i filtri di regime e di calendario (strato 3) e le varianti di uscita e di orario.
6. **Filtro 3**: come il filtro 2 con il 99% per il terzo filtro; le varianti devono avere un punteggio più alto.
7. **Ricalcolo esatto**: i finali passano al motore degli eventi e al backtest al minuto dentro l'albero
   (`motore/albero.py`): controllo della radice (gemello, metà, segnale isolato), uscite con stop, verifica, prova finale.

Il walk-forward rifà i passi 1-6 anno per anno con i soli anni precedenti e registra cosa avrebbe guadagnato la regola
scelta nell'anno dopo. Il DSR dei finali conta le prove della forza bruta come numero effettivo (gruppi di regole che
guadagnano negli stessi giorni, stimati su un campione e riportati al totale: stima prudente).

Uso: python -m motore.ricerca controlla|lancia <file.json>
"""
from __future__ import annotations

import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import albero, catalogo, condizioni, metriche, pattern, validazione
from .config import WF_PRIMO_ANNO
from .motori import matrice as MX

PREDEFINITI = {"semi_1": 300, "semi_2": 100, "finali": 12, "correlazione_semi": 0.9, "correlazione_max": 0.7, "margine_semi": 1.0, "spostamenti_minuti": [-30, -15, 15, 30],
               "quantile_2": 0.95, "quantile_3": 0.99, "candidati_per_seme": 10}
TRADE_ANNO_MIN, T_MIN, M_MIN = albero.TRADE_ANNO_FOGLIA, albero.T_MIN, albero.M_MIN
CAMPIONE_EFFETTIVI = 4000
MOTIVI = ["meno di 8 trade l'anno", "guadagno a trade troppo basso anche con un filtro", "guadagno non distinguibile dal caso (t < 2)",
          "perde sugli anni lasciati fuori (CPCV)", "perde in una metà del periodo", "non batte i filtri a caso",
          "non migliora il genitore in 2 terzi su 3", "i trade tolti non vanno peggio", "punteggio non migliore della regola di partenza"]


def _r(x, c=4):
    return albero._r(x, c)


class Cicli:
    def __init__(self, mx: MX.Matrice, cfg: dict, log=print):
        self.mx, self.cfg, self.log = mx, {**PREDEFINITI, **(cfg or {})}, log
        self.ctx = mx.ctx
        self.fam = [pattern.famiglia(c) for c in mx.condizioni]
        self.strati = {s: [i for i, p in enumerate(pattern.PATTERN) if p[2] == s] for s in (1, 2, 3)}
        self.anno_data = self.ctx.date.astype("datetime64[Y]").astype(int) + 1970
        self.fb: dict | None = None

    # ---- utilità
    def maschera(self, ti: int, conds: tuple) -> np.ndarray:
        m = self.mx.maschere[self.mx.orari[ti]]
        return m[:, list(conds)].all(axis=1) if conds else np.ones(m.shape[0], bool)

    def etichetta(self, ti: int, k: int, conds: tuple) -> str:
        u = self.mx.uscite[k]
        nomi = " e ".join(pattern.nome(self.mx.condizioni[c], self.mx.lato) for c in conds)
        lato = "" if self.mx.lato > 0 else "short · "
        return f"{lato}{self.mx.orari[ti]}{', ' + nomi if nomi else ''} → {u.get('nome') or albero.descrivi({'uscita': u}, self.ctx.barre).split('→ ')[-1]}"

    def regola(self, ti: int, k: int, conds: tuple) -> dict:
        u = {a: b for a, b in self.mx.uscite[k].items() if a != "nome"}
        t = self.mx.orari[ti]
        return {"lato": self.mx.lato, "da": t, "a": t, "cond": [list(self.mx.condizioni[c]) for c in conds], "uscita": u, "max_al_giorno": 1}

    def _st(self, ag, mk):
        return MX.statistiche(ag, self.ctx.euro_esc, self.ctx.n_anni, mk)

    @staticmethod
    def _porte_base(st, margine: float = M_MIN) -> np.ndarray:
        """Codice della prima porta non superata (-1 = passa) per le porte comuni a tutti i filtri. Al filtro 1 il margine
        richiesto è più basso (`margine_semi`): un seme deve solo poter arrivare alla soglia, ci penseranno le
        moltiplicazioni; dal filtro 2 in poi si torna a 1,5."""
        with np.errstate(invalid="ignore"):
            prove = [st["trade_anno"] >= TRADE_ANNO_MIN, (st["G"] >= 1) | (st["M"] >= margine), st["t"] >= T_MIN,
                     st["cpcv"] > 0, (st["meta1"] > 0) & (st["meta2"] > 0)]
        cod = np.full(len(st["n"]), -1)
        for i in range(len(prove) - 1, -1, -1):
            cod = np.where(~np.nan_to_num(prove[i], nan=0).astype(bool), i, cod)
        return cod

    @staticmethod
    def _prepunteggio(st) -> np.ndarray:
        return np.nan_to_num(st["G"] * np.minimum(1, np.maximum(st["t"], 0) / 3), nan=-np.inf)

    def _serie(self, ti, k, conds, giorni_ok=None):
        s = self.mx.serie(self.mx.orari[ti], k, self.maschera(ti, conds))
        return s if giorni_ok is None else s[giorni_ok]

    def _scegli(self, cand: list[dict], quanti: int, giorni_ok, cmax: float | None = None) -> list[dict]:
        """I migliori per punteggio G × R² × min(1, t/3), saltando quelli con risultati giornalieri correlati oltre la
        soglia a uno già scelto. `cand` è già ordinato per punteggio senza R²."""
        cand = cand[: quanti * self.cfg["candidati_per_seme"]]
        for c in cand:
            c["_serie"] = self._serie(c["ti"], c["k"], c["conds"], giorni_ok)
            c["r2"] = MX.r2(c["_serie"])
            c["punteggio"] = float(c["G"] * max(c["r2"] if math.isfinite(c["r2"]) else 0, 0) * min(1, max(c["t"], 0) / 3))
        cand.sort(key=lambda c: -c["punteggio"])
        scelti, serie = [], []
        cmax = self.cfg["correlazione_max"] if cmax is None else cmax
        for c in cand:
            if len(scelti) >= quanti:
                break
            x = c["_serie"]
            if x.std() == 0:
                continue
            if serie and np.max(np.abs(np.corrcoef(np.vstack([x] + serie))[0, 1:])) > cmax:
                continue
            scelti.append(c)
            serie.append(x)
        return scelti

    def _record(self, ti, k, conds, st, j) -> dict:
        return {"ti": int(ti), "k": int(k), "conds": tuple(int(c) for c in conds), "n": float(st["n"][j]), "media": float(st["media"][j]),
                "var": float(st["var"][j]), "t": float(st["t"][j]), "G": float(st["G"][j]), "M": float(st["M"][j]),
                "trade_anno": float(st["trade_anno"][j]), "ore": float(st["ore"][j]), "cpcv": float(st["cpcv"][j]),
                "terzi": [float(x) for x in st["terzi"][:, j]], "s": float(st["s"][j])}

    # ---- passo 1: forza bruta, aggregati di tutte le regole su tutti gli anni (una volta sola)
    def forza_bruta(self):
        parti = {"ti": [], "k": [], "c": [], "n": [], "s": [], "q": [], "h": [], "l": []}
        S1 = self.strati[1]
        for ti, t in enumerate(self.mx.orari):
            m = self.mx.maschere[t]
            M = np.hstack([np.ones((m.shape[0], 1), bool), m[:, S1]])
            for k in range(len(self.mx.uscite)):
                ag = self.mx.aggregati(t, k, M)
                for x in ("n", "s", "q"):
                    parti[x].append(ag[x])
                parti["h"].append(ag["h"])
                parti["l"].append(ag["l"])
                parti["ti"].append(np.full(M.shape[1], ti))
                parti["k"].append(np.full(M.shape[1], k))
                parti["c"].append(np.array([-1] + S1))
        self.fb = {x: np.hstack(v) if x in ("n", "s", "q") else np.concatenate(v) for x, v in parti.items()}
        return len(self.fb["ti"])

    def campione_effettivi(self, seme: int = 0) -> dict:
        """Prove effettive della forza bruta e varianza dei loro Sharpe, su un campione casuale di regole."""
        tot = len(self.fb["ti"])
        rng = np.random.default_rng(seme)
        idx = rng.choice(tot, min(CAMPIONE_EFFETTIVI, tot), replace=False)
        serie = np.column_stack([self._serie(self.fb["ti"][j], self.fb["k"][j], () if self.fb["c"][j] < 0 else (self.fb["c"][j],)) for j in idx])
        serie = serie[:, serie.std(axis=0) > 0]
        ni = validazione.n_indipendenti(serie)
        sr = np.array([MX.sharpe(serie[:, j]) for j in range(serie.shape[1])])
        quota = ni["cluster"] / serie.shape[1]
        return {"campione": int(serie.shape[1]), "gruppi_nel_campione": int(ni["cluster"]), "quota": _r(quota),
                "effettive": int(math.ceil(quota * tot)), "var_sharpe": float(np.nanvar(sr, ddof=1))}

    # ---- un giro completo dei filtri e delle moltiplicazioni sugli anni della maschera
    def giro(self, mk: np.ndarray | None = None) -> dict:
        cfg = self.cfg
        giorni_ok = None if mk is None else np.isin(self.anno_data, np.array(self.ctx.anni)[mk])
        out = {"passi": []}
        # filtro 1
        st = self._st(self.fb, mk)
        cod = self._porte_base(st, cfg["margine_semi"])
        ok = np.flatnonzero(cod < 0)
        pre = self._prepunteggio(st)
        ordine = ok[np.argsort(-pre[ok])]
        cand = [self._record(self.fb["ti"][j], self.fb["k"][j], () if self.fb["c"][j] < 0 else (self.fb["c"][j],), st, j) for j in ordine[: cfg["semi_1"] * cfg["candidati_per_seme"]]]
        semi1 = self._scegli(cand, cfg["semi_1"], giorni_ok, cfg["correlazione_semi"])
        out["passi"].append({"strato": "forza", "nome": "Forza bruta: ora × uscita × pattern", "n": len(st["n"])})
        out["passi"].append({"strato": "filtro1", "nome": "Filtro 1", "n": len(ok), "semi": len(semi1), "motivi": _motivi(cod)})
        # moltiplicazione 1 e filtro 2
        figli, provate, cod_tot = [], 0, []
        for s in semi1:
            usati = {self.fam[c] for c in s["conds"]}
            cols = [j for j in self.strati[1] + self.strati[2] if self.fam[j] not in usati]
            ff, p, c2 = self._figli(s, cols, mk, cfg["quantile_2"])
            figli += ff
            provate += p
            cod_tot.append(c2)
        out["passi"].append({"strato": "molt1", "nome": "Moltiplicazione 1: + un pattern o un indicatore", "n": provate})
        pool = sorted(figli + semi1, key=lambda c: -c["G"] * min(1, max(c["t"], 0) / 3))
        semi2 = self._scegli(pool, cfg["semi_2"], giorni_ok, cfg["correlazione_semi"])
        cod2 = np.concatenate(cod_tot) if cod_tot else np.array([])
        out["passi"].append({"strato": "filtro2", "nome": "Filtro 2", "n": len(figli), "semi": len(semi2), "motivi": _motivi(cod2)})
        # moltiplicazione 2 e filtro 3
        figli3, provate3, cod3 = [], 0, []
        for s in semi2:
            usati = {self.fam[c] for c in s["conds"]}
            cols = [j for j in self.strati[3] if self.fam[j] not in usati]
            ff, p, c3 = self._figli(s, cols, mk, cfg["quantile_3"])
            figli3 += ff
            provate3 += p
            cod3.append(c3)
            vv, p, c4 = self._varianti(s, mk)
            figli3 += vv
            provate3 += p
            cod3.append(c4)
        out["passi"].append({"strato": "molt2", "nome": "Moltiplicazione 2: + regime o calendario, altre uscite e orari", "n": provate3})
        pool = sorted(figli3 + semi2, key=lambda c: -c["G"] * min(1, max(c["t"], 0) / 3))
        finali = self._scegli(pool, cfg["finali"], giorni_ok)
        cod3 = np.concatenate(cod3) if cod3 else np.array([])
        out["passi"].append({"strato": "filtro3", "nome": "Filtro 3: i finali", "n": len(figli3), "semi": len(finali), "motivi": _motivi(cod3)})
        out.update({"semi1": semi1, "semi2": semi2, "finali": finali, "provate": len(st["n"]) + provate + provate3})
        return out

    def _figli(self, padre: dict, cols: list[int], mk, q_min: float):
        """Il padre AND ogni condizione di `cols`; porte comuni e confronto con il padre."""
        if not cols:
            return [], 0, np.array([])
        t = self.mx.orari[padre["ti"]]
        base = self.maschera(padre["ti"], padre["conds"])
        M = base[:, None] & self.mx.maschere[t][:, cols]
        st = self._st(self.mx.aggregati(t, padre["k"], M), mk)
        cod = self._porte_base(st)
        q = MX.quantile_filtro(st["n"], st["media"], padre["n"], padre["media"], padre["var"])
        migliora = (st["terzi"] > np.array(padre["terzi"])[:, None]).sum(0)
        with np.errstate(divide="ignore", invalid="ignore"):
            resto = (padre["s"] - st["s"]) / (padre["n"] - st["n"])
        extra = [np.nan_to_num(q, nan=0) >= q_min, migliora >= 2, ~(resto >= st["media"])]
        for i, e in enumerate(extra):
            cod = np.where((cod < 0) & ~e, 5 + i, cod)
        ok = np.flatnonzero(cod < 0)
        out = []
        for j in ok:
            r = self._record(padre["ti"], padre["k"], padre["conds"] + (cols[j],), st, j)
            r["quantile"] = float(q[j])
            out.append(r)
        return out, len(cols), cod

    def _varianti(self, padre: dict, mk):
        """Stesse condizioni con le altre uscite e con l'ingresso spostato di pochi minuti: devono fare di meglio."""
        alt = [(padre["ti"], k) for k in range(len(self.mx.uscite)) if k != padre["k"]]
        t0 = eventi_min(self.mx.orari[padre["ti"]])
        pos = {eventi_min(t): i for i, t in enumerate(self.mx.orari)}
        alt += [(pos[t0 + d], padre["k"]) for d in self.cfg["spostamenti_minuti"] if t0 + d in pos]
        out, cods = [], []
        for ti, k in alt:
            m = self.maschera(ti, padre["conds"])[:, None]
            st = self._st(self.mx.aggregati(self.mx.orari[ti], k, m), mk)
            cod = self._porte_base(st)
            sc = st["G"][0] * min(1, max(np.nan_to_num(st["t"][0]), 0) / 3)
            if cod[0] < 0 and not sc > padre["G"] * min(1, max(padre["t"], 0) / 3):
                cod[0] = 8
            cods.append(cod)
            if cod[0] < 0:
                out.append(self._record(ti, k, padre["conds"], st, 0))
        return out, len(alt), np.concatenate(cods) if cods else np.array([])

    # ---- walk-forward della procedura intera
    def walkforward(self) -> dict:
        """Per ogni anno dal 2017: rifà forza bruta, filtri e moltiplicazioni con i soli anni precedenti e registra cosa
        hanno fatto nell'anno dopo tutti i finali scelti, insieme (come un portafoglio con un CFD ciascuno)."""
        anni = np.array(self.ctx.anni)
        righe, tot = [], np.zeros(2)
        for y in range(max(WF_PRIMO_ANNO, anni[0] + 1), anni[-1] + 1):
            g = self.giro(anni < y)
            iy = int(np.flatnonzero(anni == y)[0])
            n = s = 0.0
            for f in g["finali"]:
                ag = self.mx.aggregati(self.mx.orari[f["ti"]], f["k"], self.maschera(f["ti"], f["conds"])[:, None])
                n += float(ag["n"][iy, 0])
                s += float(ag["s"][iy, 0])
            tot += (n, s)
            primo = self.etichetta(g["finali"][0]["ti"], g["finali"][0]["k"], g["finali"][0]["conds"]) if g["finali"] else "nessuna regola passa i filtri"
            righe.append({"anno": int(y), "nodo": None, "etichetta": f"{len(g['finali'])} finali, il primo: {primo}", "n": int(n),
                          "media_esc": _r(s / n) if n else None})
            self.log(f"  walk-forward {y}: {len(g['finali'])} finali, {int(n)} trade, media {righe[-1]['media_esc']}")
        return {"anni": righe, "n": int(tot[0]), "media_esc": _r(tot[1] / tot[0]) if tot[0] else None, "intera_ricerca": True}

    # ---- prova sul rumore
    def rumore(self, ripetizioni: int, seme: int = 0) -> dict:
        """Rifà forza bruta, filtri e moltiplicazioni `ripetizioni` volte con le condizioni slegate dai risultati
        (`Matrice.spostata`, spostamento casuale di almeno un anno). Per ogni giro conserva il punteggio del finale
        migliore e il guadagno medio dei finali: è quanto di bello esce da questa ricerca quando non c'è niente da trovare."""
        rng = np.random.default_rng(seme)
        nd = len(self.ctx.date)
        giri = []
        for i in range(ripetizioni):
            passo = int(rng.integers(260, max(261, nd - 260)))
            c = Cicli(self.mx.spostata(passo), self.cfg, log=lambda *a: None)
            c.forza_bruta()
            g = c.giro()
            pt = [f["punteggio"] for f in g["finali"]]
            giri.append({"passo": passo, "finali": len(pt), "migliore": max(pt) if pt else 0.0,
                         "euro_medio": float(np.mean([f["media"] for f in g["finali"]]) * (self.ctx.euro_esc or 0)) if pt else None,
                         "punteggi": [round(x, 4) for x in pt]})
            self.log(f"  rumore {i + 1}/{ripetizioni}: {len(pt)} finali, migliore {giri[-1]['migliore']:.3f}")
        return {"ripetizioni": ripetizioni, "giri": giri}

    def mostra(self, r: dict) -> dict:
        """Una regola per il cruscotto: nome, misure e mini-curva in euro di oggi."""
        s = self._serie(r["ti"], r["k"], r["conds"])
        e = self.ctx.euro_esc or 0
        c = np.cumsum(s) * e
        idx = np.unique(np.linspace(0, len(c) - 1, 60).round().astype(int))
        return {"etichetta": self.etichetta(r["ti"], r["k"], r["conds"]), "euro_oggi": _r(r["media"] * e, 2), "trade_anno": _r(r["trade_anno"], 1),
                "t": _r(r["t"], 2), "G": _r(r["G"], 3), "M": _r(r["M"], 3), "ore": _r(r["ore"], 1), "r2": _r(r.get("r2"), 3),
                "quantile": _r(r.get("quantile"), 3), "mini": [round(float(c[i]), 1) for i in idx], "regola": self.regola(r["ti"], r["k"], r["conds"])}


def eventi_min(hhmm: str) -> int:
    a, b = hhmm.split(":")
    return int(a) * 60 + int(b)


def _motivi(cod: np.ndarray) -> dict:
    if not len(cod):
        return {}
    v, c = np.unique(cod[cod >= 0], return_counts=True)
    return {MOTIVI[int(a)]: int(b) for a, b in sorted(zip(v, c), key=lambda x: -x[1])}


# ---------------------------------------------------------------- file e lancio

def controlla(file) -> dict:
    e = albero.carica(file)
    errori = [f"manca o è sbagliato '{k}'" for k, tp in {"tipo": str, "nome": str, "ipotesi": str, "prodotto": str, "barre": int,
                                                          "forza_bruta": dict}.items() if not isinstance(e.get(k), tp)]
    if e.get("tipo") != "cicli":
        errori.append("tipo deve essere 'cicli'")
    try:
        catalogo.prodotto(e.get("prodotto", ""))
    except KeyError:
        errori.append(f"prodotto sconosciuto {e.get('prodotto')}")
    for p in pattern.PATTERN:
        try:
            condizioni.grandezza(p[3][0], 1)
        except (KeyError, ValueError):
            errori.append(f"pattern {p[0]}: grandezza sconosciuta {p[3][0]}")
    fb = e.get("forza_bruta") or {}
    o = fb.get("orari") or {}
    n_orari = len(MX.orari(o["da"], o["a"], int(o["passo"]))) if {"da", "a", "passo"} <= set(o) else 0
    n_fb = n_orari * len(fb.get("uscite", [])) * (1 + len(pattern.dello_strato(1)))
    return {"file": str(file), "ok": not errori, "errori": errori, "prove_forza_bruta": n_fb}


def p_rumore(punteggio: float, rumore: dict) -> float:
    """Probabilità che la ricerca sul rumore produca un finale migliore: (1 + giri con un migliore >= punteggio) / (1 + giri)."""
    giri = rumore["giri"]
    return (1 + sum(g["migliore"] >= punteggio for g in giri)) / (1 + len(giri))


def lancia(file, log=print) -> dict:
    c = controlla(file)
    if not c["ok"]:
        raise ValueError("; ".join(c["errori"]))
    return lancia_spec(albero.carica(file), log)


def lancia_spec(spec: dict, log=print) -> dict:
    """Esegue una ricerca a cicli descritta da `spec` (stesso formato del file)."""
    cart = albero.CARTELLA / spec["nome"]
    if (cart / "ricerca.json").exists():
        raise ValueError(f"ricerca {spec['nome']} già lanciata: la prova finale si usa una volta sola (cambiare nome per una ricerca nuova)")
    cart.mkdir(parents=True, exist_ok=True)
    inizio = datetime.now(timezone.utc).isoformat(timespec="seconds")
    diario = []

    def nota(fase, testo, entrati=None, usciti=None, prove=None):
        diario.append({"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"), "fase": fase, "testo": testo,
                       "entrati": entrati, "usciti": usciti, "prove": prove})
        albero._scrivi_stato(cart, {"stato": "in corso", "inizio": inizio, "prove": prove or 0, "budget": None, "fase": testo, "diario": diario})
        log(f"{fase}: {testo}")

    try:
        t0 = time.time()
        ctx = albero.Contesto(spec["prodotto"], spec["barre"], spec.get("seme", 0))
        fb = spec["forza_bruta"]
        mx = MX.Matrice(ctx, MX.orari(fb["orari"]["da"], fb["orari"]["a"], int(fb["orari"]["passo"])), fb["uscite"],
                        [p[3] for p in pattern.PATTERN], int(spec.get("lato", 1)))
        cic = Cicli(mx, spec.get("cicli"), log)
        n_fb = cic.forza_bruta()
        nota("forza bruta", f"{n_fb} regole: {len(mx.orari)} orari × {len(mx.uscite)} uscite × {1 + len(cic.strati[1])} (nessun pattern o uno dello strato 1)", prove=n_fb)
        g = cic.giro()
        for p in g["passi"][1:]:
            if "semi" in p:
                nota(p["strato"], f"{p['n']} regole passano, {p['semi']} scelte come semi (diverse fra loro)", prove=g["provate"])
            else:
                nota(p["strato"], f"{p['n']} regole nuove dalla combinazione dei semi", prove=g["provate"])
        eff = cic.campione_effettivi(spec.get("seme", 0))
        eff["effettive"] = int(math.ceil(eff["quota"] * g["provate"]))       # la stessa quota applicata a tutte le prove
        nota("conto delle prove", f"{g['provate']} prove; su un campione di {eff['campione']} regole della forza bruta "
                                  f"i gruppi indipendenti sono il {eff['quota']:.0%}: circa {eff['effettive']} prove effettive per il DSR", prove=g["provate"])
        nota("walk-forward", "la ricerca si rifà anno per anno dal 2017 con i soli anni precedenti", prove=g["provate"])
        wf = cic.walkforward()
        rum, p_fin = None, {}
        n_rum = int((spec.get("rumore") or {}).get("ripetizioni", 0))
        if n_rum and g["finali"]:
            nota("prova sul rumore", f"la ricerca si rifà {n_rum} volte con le condizioni slegate dai risultati, per vedere quanto "
                                     f"belli escono i finali per caso (solo perché la ricerca vera ha dei finali)", prove=g["provate"])
            rum = cic.rumore(n_rum, spec.get("seme", 0))
            for f in g["finali"]:
                p_fin[json.dumps(cic.regola(f["ti"], f["k"], f["conds"]), sort_keys=True)] = p_rumore(f["punteggio"], rum)
            rum["finali_veri"] = [{"etichetta": cic.etichetta(f["ti"], f["k"], f["conds"]), "punteggio": _r(f["punteggio"]),
                                   "p": _r(p_rumore(f["punteggio"], rum), 3)} for f in g["finali"]]
        elif n_rum:
            nota("prova sul rumore", "non serve: la ricerca vera non ha finali", prove=g["provate"])
        # ricalcolo esatto e verifica nell'albero
        spec_al = {**spec, "tipo": "ricerca", "ingressi": [], "max_condizioni": 0, "foglie_per_radice": 1,
                   "uscite": spec.get("uscite_finali", []),
                   "radici": [{"nome": cic.etichetta(f["ti"], f["k"], f["conds"]), "regola": cic.regola(f["ti"], f["k"], f["conds"])} for f in g["finali"]],
                   "budget": len(g["finali"]) * (2 + len(spec.get("uscite_finali", [])))}
        al = albero.Albero(spec_al, ctx)
        al.prove_esterne, al.var_sr_esterna, al.wf_esterno = eff["effettive"], eff["var_sharpe"], wf
        al.rumore_p = p_fin if rum else None
        al.diario = diario
        nota("ricalcolo esatto", f"{len(g['finali'])} finali ricalcolati con il motore degli eventi, poi gemello, metà del periodo e segnale isolato", prove=g["provate"])
        ris = al.esegui(log)
        passi = g["passi"]
        imb = [{"strato": "forza", "nome": passi[0]["nome"], "n": passi[0]["n"], "tipo": "moltiplica"},
               {"strato": "filtro1", "nome": "Filtro 1: semi", "n": passi[1]["semi"], "provati": passi[1]["n"], "tipo": "filtra"},
               {"strato": "molt1", "nome": passi[2]["nome"], "n": passi[2]["n"], "tipo": "moltiplica"},
               {"strato": "filtro2", "nome": "Filtro 2: semi", "n": passi[3]["semi"], "provati": passi[3]["n"], "tipo": "filtra"},
               {"strato": "molt2", "nome": passi[4]["nome"], "n": passi[4]["n"], "tipo": "moltiplica"},
               {"strato": "filtro3", "nome": "Filtro 3: finali", "n": passi[5]["semi"], "provati": passi[5]["n"], "tipo": "filtra"}]
        extra = {"imbuto_cicli": imb, "prove_cicli": g["provate"], "effettive": eff, "durata_cicli_s": round(time.time() - t0, 1),
                 "cicli": [{**p, "migliori": [cic.mostra(r) for r in lista[:40]]} for p, lista in
                           zip([passi[1], passi[3], passi[5]], [g["semi1"], g["semi2"], g["finali"]])],
                 "pattern": [{"nome": p[0], "categoria": p[1], "strato": p[2], "condizione": p[3]} for p in pattern.PATTERN],
                 "uscite_forza_bruta": fb["uscite"], "orari": mx.orari, "rumore": rum, "lato": int(spec.get("lato", 1)),
                 "campagna": spec.get("campagna")}
        out = albero.concludi(al, ris, spec, cart, inizio, extra)
    except Exception as ex:
        albero._scrivi_stato(cart, {"stato": "fallita", "inizio": inizio, "errore": f"{type(ex).__name__}: {ex}", "diario": diario})
        raise
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    comando, file = sys.argv[1], sys.argv[2]
    if comando == "controlla":
        print(json.dumps(controlla(file), ensure_ascii=False, indent=1))
    elif comando == "lancia":
        r = lancia(file)
        print(f"{r['prove']} prove")
        for f in r["foglie"]:
            print(f"{f['id']} {f['etichetta']}: {f['esito']} — {f['motivo']}")
    else:
        raise SystemExit("uso: python -m motore.ricerca controlla|lancia <file.json>")
