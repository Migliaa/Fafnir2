"""Ricerca in profondità ad albero (`ricerca/protocollo-albero.md`).

Un file d'esperimento di tipo `albero` dichiara il prodotto, le radici (regole già trovate), le ipotesi d'ingresso con il
meccanismo e la direzione scritti prima, le varianti d'uscita e il budget di prove. Il motore esegue i livelli in
sequenza e applica le porte:

- L0 radice: pronta (copertura G >= 1) o con margine (M >= 1,5), t >= 2, mediana fuori campione della CPCV positiva;
- L1 radice: gemello con lo stesso segno, entrambe le metà del periodo positive, strato differenziale (D2);
- L2 ingressi: ogni figlio aggiunge una condizione al genitore; batte i filtri casuali che tolgono la stessa quota di
  trade (95% con la prima condizione aggiunta, 99% con la seconda), migliora il genitore in 2 terzi su 3, le soglie
  vicine vanno nella stessa direzione, il resto dei trade va peggio, strato differenziale; la scelta fra fratelli è
  misurata fuori campione con la CPCV;
- L3 uscite: varianti dal file più uno stop ricavato dall'escursione contraria dei trade vincenti; utile/drawdown
  migliore del genitore;
- L4 verifica, senza ricerca: backtest al minuto, costi doppi, gemello, Monte Carlo a blocchi, DSR sulle prove
  dell'albero, walk-forward della procedura, filtri di Andrea in euro di oggi; poi la prova finale una volta per albero.

Unità: i trade sono in escursioni medie giornaliere (`netto`, `lordo`); gli euro "di oggi" sono escursioni per
l'escursione media in punti dell'ultimo anno della scoperta per il valore del punto di 1 CFD IG.

Uso: python -m motore.albero controlla <file.json> | lancia <file.json>
"""
from __future__ import annotations

import copy
import json
import math
import sys
import time
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import numpy as np
import polars as pl

from . import catalogo, condizioni, dati, giudizio, metriche, prova_finale, uscita, validazione
from .config import RISULTATI, SCOPERTA, WF_PRIMO_ANNO
from .motori import backtest, eventi

CARTELLA = RISULTATI / "ricerche"   # i test la sostituiscono con una cartella temporanea

# ---- porte (protocollo, "Porte come funzioni di altre metriche")
T_MIN = 2.0                          # guadagno medio / errore standard
TRADE_ANNO_RAMO = 12.0               # per approfondire un ramo con altri filtri
TRADE_ANNO_FOGLIA = 6.0              # pavimento pratico di un sistema finale
M_MIN = 1.5                          # margine per approfondire
QUANTILE_FILTRO = {1: 0.95, 2: 0.99}  # batte questa quota dei filtri casuali (1a e 2a condizione aggiunta)
D2_QUOTA_LORDO = 0.5                 # il segnale isolato vale almeno metà del lordo
WF_EFFICIENZA_MIN = 0.5              # walk-forward della procedura: fuori campione / in-sample
R2_MIN, ANNI_POSITIVI_MIN, DSR_MIN = giudizio.R2_MIN, giudizio.ANNI_POSITIVI_MIN, giudizio.DSR_MIN
PERMUTAZIONI = 1000
MIN_TRADE_TRAIN = 10                 # trade minimi negli anni di training per scegliere un fratello
SOGLIE_STOP = (0.25, 0.5, 0.75, 1.0, 1.5)   # valori tondi per lo stop ricavato dall'escursione contraria

OBBLIGATORI = {"tipo": str, "nome": str, "ipotesi": str, "prodotto": str, "barre": int, "budget": int, "ingressi": list}


# ---------------------------------------------------------------- contesto e nodi

class Contesto:
    """Tabella di base della scoperta e le costanti che servono a ogni nodo."""

    def __init__(self, prodotto: str, barre: int, seme: int = 0):
        self.prodotto, self.barre = prodotto, barre
        self.tab = eventi.base(prodotto, barre)
        dati.controlla_taglio(self.tab)
        self.date = self.tab["data"].unique().sort().to_numpy().astype("datetime64[D]")
        self.anni = list(range(SCOPERTA[0], SCOPERTA[1] + 1))
        self.n_anni = len(self.anni)
        p = catalogo.prodotto(prodotto)
        self.ep = p.euro_punto
        self.anno_oggi = int(self.tab["data"].dt.year().max())      # ultimo anno della scoperta con dati (2023)
        ultimo = self.tab.filter(pl.col("data").dt.year() == self.anno_oggi)
        self.esc_oggi = float(ultimo.group_by("data").agg(pl.col("esc").first())["esc"].mean())
        self.euro_esc = None if self.ep is None else self.esc_oggi * self.ep   # euro di oggi per un'escursione
        # sottostante giorno per giorno, in escursioni: chiusura su chiusura
        g = (self.tab.group_by("data").agg(pl.col("c").last(), pl.col("esc").first(), pl.col("chiude").last()).sort("data"))
        ret = (g["c"] - g["c"].shift(1)) / g["esc"]
        self.ret_giorno = np.nan_to_num(ret.to_numpy())
        ore = (g["chiude"][-1] - g["chiude"][0]).total_seconds() / 3600
        self.deriva_ora = float(np.nansum(ret.to_numpy()) / ore)        # escursioni per ora di calendario
        self.rng = np.random.default_rng(seme)
        self._rif: dict = {}

    def trade(self, regola: dict, molt_costi: float = 1.0) -> pl.DataFrame:
        _, t = eventi.prova(self.prodotto, self.barre, regola, self.tab, molt_costi=molt_costi, riassumi=False)
        return t

    def riferimento(self, regola: dict) -> pl.DataFrame:
        """Trade della stessa finestra senza condizioni (riferimento D2), uno per regola senza condizioni."""
        r = {k: v for k, v in regola.items() if k != "cond"}
        chiave = json.dumps(r, sort_keys=True)
        if chiave not in self._rif:
            self._rif[chiave] = self.trade(r)
        return self._rif[chiave]

    def giornaliera(self, trade: pl.DataFrame, colonna: str = "netto") -> np.ndarray:
        if not trade.height:
            return np.zeros(len(self.date))
        i = np.minimum(np.searchsorted(self.date, trade["uscita"].dt.date().to_numpy().astype("datetime64[D]")), len(self.date) - 1)
        return np.bincount(i, weights=trade[colonna].to_numpy(), minlength=len(self.date))


def _annuali(ctx: Contesto, trade: pl.DataFrame) -> np.ndarray:
    """Per anno della scoperta: numero di trade, somma e somma dei quadrati del netto (righe = anni)."""
    out = np.zeros((ctx.n_anni, 3))
    if not trade.height:
        return out
    a = trade["uscita"].dt.year().to_numpy() - SCOPERTA[0]
    x = trade["netto"].to_numpy()
    ok = (a >= 0) & (a < ctx.n_anni)
    for k, w in enumerate((np.ones(len(x)), x, x * x)):
        out[:, k] = np.bincount(a[ok], weights=w[ok], minlength=ctx.n_anni)
    return out


def _stat(ann: np.ndarray, maschera=None) -> tuple[int, float | None, float | None]:
    """(n, media, t) dagli aggregati annuali, sugli anni della maschera."""
    a = ann if maschera is None else ann[maschera]
    n, s, q = a[:, 0].sum(), a[:, 1].sum(), a[:, 2].sum()
    if n < 2:
        return int(n), (s / n if n else None), None
    media = s / n
    var = max(q - n * media * media, 0) / (n - 1)
    return int(n), media, (media / math.sqrt(var) * math.sqrt(n) if var > 0 else None)


def _r(x, c=4):
    if x is None:
        return None
    x = float(x)
    return round(x, c) if math.isfinite(x) else None


def misure(ctx: Contesto, trade: pl.DataFrame) -> dict:
    """Misure di un nodo: in escursioni e in euro di oggi (1 CFD IG), con le porte come rapporti (G, M, t)."""
    n = trade.height
    out = {"n": n, "trade_anno": n / ctx.n_anni}
    if n < 3:
        return out
    x, lordo = trade["netto"].to_numpy(), trade["lordo"].to_numpy()
    sd = float(x.std(ddof=1))
    ore = float((trade["uscita"] - trade["ingresso"]).dt.total_seconds().mean() / 3600)
    media = float(x.mean())
    out.update({"media_esc": media, "lordo_esc": float(lordo.mean()), "sd_esc": sd, "ore_medie": ore,
                "t": media / sd * math.sqrt(n) if sd > 0 else None,
                "n_necessari": math.ceil((T_MIN * sd / media) ** 2) if media > 0 and sd > 0 else None})
    g = ctx.giornaliera(trade)
    out["dd_esc"] = float(metriche.drawdown(g)["massimo"])
    anno = trade["uscita"].dt.year().to_numpy()
    out["anni_positivi"] = float(np.mean([x[anno == a].sum() > 0 for a in ctx.anni]))
    out["r2"] = float(metriche.r2(g)) if g.std() > 0 else None
    out["sharpe"] = float(metriche.sharpe(g))
    if ctx.euro_esc is not None:
        e = ctx.euro_esc
        richiesto = giudizio.soglia_guadagno(ore)
        out.update({"euro_oggi": media * e, "euro_storico": float(trade["punti"].mean() * ctx.ep),
                    "costo_euro_oggi": float((lordo - x).mean() * e), "richiesto": richiesto,
                    "G": media * e / richiesto, "M": media * e * out["trade_anno"] / (12 * richiesto),
                    "utile_anno_oggi": media * e * out["trade_anno"], "dd_euro_oggi": out["dd_esc"] * e})
        out["utile_su_dd"] = (media * n / out["dd_esc"]) if out["dd_esc"] > 0 else None
    return out


def punteggio(m: dict) -> float:
    """Ordine dei nodi: G × R² × min(1, t/3)."""
    if m.get("G") is None or m.get("t") is None:
        return -math.inf
    return m["G"] * max(m.get("r2") or 0, 0) * min(1.0, max(m["t"], 0) / 3)


# ---------------------------------------------------------------- strato differenziale

def differenziale(ctx: Contesto, regola: dict, trade: pl.DataFrame, lato: int) -> dict:
    """D1 (deriva), D2 (stessa finestra in tutti i giorni), D3 (sottoinsiemi casuali della finestra) e la regressione
    giornaliera sul sottostante, in escursioni lorde per trade, ognuno con il suo t."""
    n = trade.height
    if n < 3:
        return {}
    y = trade["lordo"].to_numpy()
    rif = ctx.riferimento(regola)
    r = rif["lordo"].to_numpy()
    N = len(r)
    out = {"lordo": float(y.mean()), "n_sistema": n, "rif_lordo": float(r.mean()) if N else None,
           "rif_netto": float(rif["netto"].mean()) if N else None, "rif_n": N}
    # D1: deriva per ora di calendario per la durata di ogni trade
    ore = (trade["uscita"] - trade["ingresso"]).dt.total_seconds().to_numpy() / 3600
    d1 = y - lato * ctx.deriva_ora * ore
    out["D1"] = float(d1.mean())
    out["t_D1"] = float(d1.mean() / d1.std(ddof=1) * math.sqrt(n)) if d1.std() > 0 else None
    # D2: media dei trade meno media della finestra; errore di un campione senza reimmissione dalla finestra
    if N > n and r.std() > 0:
        out["D2"] = float(y.mean() - r.mean())
        se = r.std(ddof=1) * math.sqrt(max(1 / n - 1 / N, 1e-12))
        out["t_D2"] = out["D2"] / se
        out["quota_D2"] = out["D2"] / y.mean() if y.mean() > 0 else None
        # D3: dove sta la media del sistema fra 1.000 sottoinsiemi casuali della finestra con lo stesso numero di trade
        idx = np.argpartition(ctx.rng.random((PERMUTAZIONI, N)), n - 1, axis=1)[:, :n]
        medie = r[idx].mean(axis=1)
        out["D3_quantile"] = float(np.mean(medie < y.mean()))
        out["D3"] = float(y.mean() - np.median(medie))
    else:                                        # il sistema è la finestra intera: nessuna selezione da misurare
        out.update({"D2": 0.0, "t_D2": 0.0, "quota_D2": 0.0, "D3_quantile": None, "D3": None})
    # regressione dei rendimenti giornalieri del sistema su quelli del sottostante
    g, u = ctx.giornaliera(trade, "lordo"), ctx.ret_giorno
    uc = u - u.mean()
    beta = float((uc @ (g - g.mean())) / (uc @ uc)) if uc @ uc > 0 else 0.0
    res = g - g.mean() - beta * uc
    alfa = float(g.mean() - beta * u.mean())
    se_a = math.sqrt((res @ res) / (len(g) - 2) / len(g)) if len(g) > 2 else None
    out.update({"beta": beta, "alfa_giorno": alfa, "t_alfa": alfa / se_a if se_a else None})
    if ctx.euro_esc is not None:
        out["D2_euro"] = out["D2"] * ctx.euro_esc
    return out


def porte_differenziale(d: dict) -> list[dict]:
    """D2 > 0 con t >= 2 e almeno metà del lordo. Se il sistema è la finestra intera (nessuna condizione, D3 non
    calcolato) D2 è zero per costruzione e il riferimento giusto è la deriva: la stessa porta si applica a D1."""
    if d.get("D3_quantile") is None and d.get("rif_n") == d.get("n_sistema", d.get("rif_n")):
        d1, t1, lordo = d.get("D1"), d.get("t_D1"), d.get("lordo")
        q = d1 / lordo if d1 is not None and lordo and lordo > 0 else None
        return [_porta("Segnale meno la deriva D1 > 0 con t >= 2", d1, f"t >= {T_MIN:g}",
                       None if d1 is None or t1 is None else (d1 > 0 and t1 >= T_MIN)),
                _porta("D1 almeno metà del lordo", q, f">= {D2_QUOTA_LORDO:.0%}", None if q is None else q >= D2_QUOTA_LORDO)]
    d2, t2, q = d.get("D2"), d.get("t_D2"), d.get("quota_D2")
    return [_porta("Segnale isolato D2 > 0 con t >= 2", d2, f"t >= {T_MIN:g}",
                   None if d2 is None or t2 is None else (d2 > 0 and t2 >= T_MIN)),
            _porta("D2 almeno metà del lordo", q, f">= {D2_QUOTA_LORDO:.0%}", None if q is None else q >= D2_QUOTA_LORDO)]


# ---------------------------------------------------------------- confronti

def filtri_casuali(ctx: Contesto, figlio: pl.DataFrame, padre: pl.DataFrame) -> dict:
    """Il figlio contro 1.000 filtri casuali che tengono lo stesso numero di trade del padre; e il resto dei trade."""
    x = padre["netto"].to_numpy()
    k, N = figlio.height, len(x)
    tenuti = padre["ingresso"].is_in(figlio["ingresso"].implode()).to_numpy()
    resto = x[~tenuti]
    out = {"n_padre": N, "quota_tenuta": k / N if N else None, "resto_media": float(resto.mean()) if len(resto) else None}
    if k < 3 or k >= N:
        out["quantile"] = None
        return out
    idx = np.argpartition(ctx.rng.random((PERMUTAZIONI, N)), k - 1, axis=1)[:, :k]
    out["quantile"] = float(np.mean(x[idx].mean(axis=1) < figlio["netto"].mean()))
    return out


def terzi(ctx: Contesto) -> list[np.ndarray]:
    """Tre parti della scoperta (maschere sugli anni) per il controllo "migliora in 2 terzi su 3"."""
    return [np.isin(np.arange(ctx.n_anni), p) for p in np.array_split(np.arange(ctx.n_anni), 3)]


def cpcv_nodo(ctx: Contesto, ann: np.ndarray) -> dict:
    """Guadagno medio a trade negli anni di prova di ogni combinazione della CPCV (10 anni, 2 di prova: 45)."""
    oos = []
    for _, test in validazione.blocchi_cpcv(ctx.anni, 2):
        n, m, _ = _stat(ann, np.isin(ctx.anni, test))
        if n:
            oos.append(m)
    return _distribuzione(oos)


def _distribuzione(oos: list) -> dict:
    if not oos:
        return {"n": 0, "mediana": None, "p10": None, "quota_positiva": None}
    o = np.array(oos, dtype=float)
    return {"n": len(o), "mediana": float(np.median(o)), "p10": float(np.percentile(o, 10)), "quota_positiva": float(np.mean(o > 0))}


def scelta_fratelli(ctx: Contesto, anns: list[np.ndarray]) -> dict:
    """CPCV della scelta fra fratelli: in ogni combinazione si sceglie il fratello con il t più alto negli anni di
    training e se ne misura il guadagno medio negli anni di prova."""
    oos, scelte = [], [0] * len(anns)
    for train, test in validazione.blocchi_cpcv(ctx.anni, 2):
        mtr, mte = np.isin(ctx.anni, train), np.isin(ctx.anni, test)
        migliore, tmax = None, -math.inf
        for i, a in enumerate(anns):
            n, _, t = _stat(a, mtr)
            if n >= MIN_TRADE_TRAIN and t is not None and t > tmax:
                migliore, tmax = i, t
        if migliore is None:
            continue
        n, m, _ = _stat(anns[migliore], mte)
        if n:
            scelte[migliore] += 1
            oos.append(m)
    return {**_distribuzione(oos), "scelte": scelte}


# ---------------------------------------------------------------- escursione contraria (MAE) per lo stop

def escursioni_trade(ctx: Contesto, trade: pl.DataFrame, lato: int) -> tuple[np.ndarray, np.ndarray]:
    """Escursione contraria e a favore massima di ogni trade (in escursioni), sulle barre del motore."""
    apre = ctx.tab["apre"]
    e = np.searchsorted(apre.to_numpy(), trade["ingresso"].to_numpy())
    u = np.searchsorted(apre.to_numpy(), trade["uscita"].to_numpy())
    o, h, l, esc = (ctx.tab[c].to_numpy() for c in ("o", "h", "l", "esc"))
    mae, mfe = np.zeros(len(e)), np.zeros(len(e))
    for k, (i, j) in enumerate(zip(e, u)):
        j = max(j, i + 1)
        lo, hi, p0, s = l[i:j].min(), h[i:j].max(), o[i], esc[i - 1]
        mae[k], mfe[k] = ((p0 - lo) / s, (hi - p0) / s) if lato > 0 else ((hi - p0) / s, (p0 - lo) / s)
    return mae, mfe


def stop_da_mae(ctx: Contesto, trade: pl.DataFrame, lato: int) -> float | None:
    """Stop tondo appena sopra il 90° percentile dell'escursione contraria dei trade vincenti: taglia le perdite
    grandi lasciando passare quasi tutti i trade che poi vincono. None se nessun valore tondo serve."""
    if trade.height < 20:
        return None
    mae, _ = escursioni_trade(ctx, trade, lato)
    vinti = mae[trade["lordo"].to_numpy() > 0]
    if len(vinti) < 10:
        return None
    p90 = float(np.percentile(vinti, 90))
    for s in SOGLIE_STOP:
        if s >= p90:
            return s if s < mae.max() else None
    return None


# ---------------------------------------------------------------- porte

def _porta(nome, valore, soglia, ok, info: bool = False):
    return {"nome": nome, "valore": _r(valore) if isinstance(valore, (int, float)) and not isinstance(valore, bool) else valore,
            "soglia": soglia, "esito": "info" if info else ("grigio" if ok is None else ("verde" if ok else "rosso"))}


def _passa(porte: list[dict]) -> bool:
    return all(p["esito"] in ("verde", "info") for p in porte)


def _motivo(porte: list[dict]) -> str | None:
    for p in porte:
        if p["esito"] in ("rosso", "grigio"):
            return f"{p['nome']}: {p['valore'] if p['valore'] is not None else 'n.d.'} (serve {p['soglia']})"
    return None


def porte_radice(m: dict, cp: dict) -> list[dict]:
    G, M, t = m.get("G"), m.get("M"), m.get("t")
    return [
        _porta("Pronto (G >= 1) o con margine (M >= 1,5)", G, f"G >= 1 o M >= {M_MIN:g} (M = {_r(M, 2)})",
               None if G is None or M is None else (G >= 1 or M >= M_MIN)),
        _porta("t del guadagno medio", t, f">= {T_MIN:g}", None if t is None else t >= T_MIN),
        _porta("Trade l'anno", m.get("trade_anno"), f">= {TRADE_ANNO_FOGLIA:g}", m.get("trade_anno", 0) >= TRADE_ANNO_FOGLIA),
        _porta("Mediana fuori campione CPCV", cp.get("mediana"), "> 0", None if cp.get("mediana") is None else cp["mediana"] > 0),
    ]


# ---------------------------------------------------------------- l'albero

class Albero:
    def __init__(self, spec: dict, ctx: Contesto | None = None):
        self.spec = spec
        self.ctx = ctx or Contesto(spec["prodotto"], spec["barre"], spec.get("seme", 0))
        self.nodi: list[dict] = []
        self.prove = 0
        self.budget = int(spec["budget"])
        self.esaurito = False
        self._trade: dict[str, pl.DataFrame] = {}
        self._ann: dict[str, np.ndarray] = {}
        self.livelli: list[dict] = []        # CPCV della scelta fra fratelli per ogni gruppo di figli
        self.diario: list[dict] = []         # passi della ricerca, per il cruscotto
        self.osserva = None                  # funzione (prove fatte, budget) chiamata a ogni nodo
        self.wf_ricerca: dict | None = None
        self.wf_esterno: dict | None = None     # walk-forward calcolato fuori (ricerca a cicli)
        self.prove_esterne: float | None = None  # prove effettive fatte prima dell'albero (forza bruta), per il DSR
        self.var_sr_esterna: float | None = None

    # -- nodi
    def nodo(self, regola: dict, livello: str, genitore: str | None, etichetta: str, n_cond: int, conta: bool = True,
             leggero: bool = False) -> dict | None:
        """Valuta una regola e la aggiunge all'albero. `leggero`: senza strato differenziale (ampiezza: si calcola
        solo per chi passa il primo livello)."""
        if conta:
            if self.prove >= self.budget:
                self.esaurito = True
                return None
            self.prove += 1
        t = self.ctx.trade(regola)
        id_ = f"n{len(self.nodi) + 1:03d}"
        m = misure(self.ctx, t)
        nd = {"id": id_, "genitore": genitore, "livello": livello, "etichetta": etichetta, "regola": regola,
              "n_cond": n_cond, "misure": m, "punteggio": punteggio(m), "porte": [], "esito": "da valutare", "motivo": None}
        self._trade[id_], self._ann[id_] = t, _annuali(self.ctx, t)
        nd["cpcv"] = cpcv_nodo(self.ctx, self._ann[id_])
        nd["differenziale"] = {} if leggero else differenziale(self.ctx, regola, t, int(regola["lato"]))
        self.nodi.append(nd)
        if self.osserva:
            self.osserva(self.prove, self.budget)
        return nd

    def _chiudi(self, nd: dict, porte: list[dict], esito_ok: str = "passa"):
        nd["porte"] += porte
        mot = _motivo(nd["porte"])
        nd["esito"], nd["motivo"] = ("scartato", mot) if mot else (esito_ok, None)
        return mot is None

    def trade(self, id_: str) -> pl.DataFrame:
        return self._trade[id_]

    # -- livelli
    def nota(self, fase: str, testo: str, entrati: int | None = None, usciti: int | None = None):
        self.diario.append({"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"), "fase": fase, "testo": testo,
                            "entrati": entrati, "usciti": usciti, "prove": self.prove})

    def radice(self, r: dict) -> dict | None:
        nd = self.nodo(r["regola"], "L0", None, r.get("nome", "radice"), 0)
        if nd is None:
            return None
        nd["descrizione"] = r.get("descrizione")
        if not self._chiudi(nd, porte_radice(nd["misure"], nd["cpcv"])):
            return nd
        return self.livello1(nd)

    def livello1(self, nd: dict) -> dict:
        """L1 sulla radice: gemello, due metà del periodo, strato differenziale."""
        if not nd["differenziale"]:
            nd["differenziale"] = differenziale(self.ctx, nd["regola"], self.trade(nd["id"]), int(nd["regola"]["lato"]))
        nd["livello1"] = True
        porte = []
        gem = self.spec.get("gemello")
        if gem:
            mg = self._gemello(nd["regola"])
            nd["gemello"] = mg
            porte.append(_porta(f"Gemello {gem}: stesso segno", mg.get("media_esc"), "> 0",
                                None if mg.get("media_esc") is None else mg["media_esc"] > 0))
        ann = self._ann[nd["id"]]
        meta = self.ctx.n_anni // 2
        for k, sl in enumerate((slice(0, meta), slice(meta, None))):
            mk = np.zeros(self.ctx.n_anni, bool)
            mk[sl] = True
            _, mm, _ = _stat(ann, mk)
            a0, a1 = np.array(self.ctx.anni)[mk][[0, -1]]
            porte.append(_porta(f"Metà {a0}-{a1} positiva", mm, "> 0", None if mm is None else mm > 0))
        porte += porte_differenziale(nd["differenziale"])
        self._chiudi(nd, porte, "pronto" if (nd["misure"].get("G") or 0) >= 1 else "passa")
        return nd

    def _gemello(self, regola: dict) -> dict:
        gem = self.spec["gemello"]
        try:
            ctx2 = getattr(self, "_ctx_gemello", None) or Contesto(gem, self.spec["barre"])
            self._ctx_gemello = ctx2
            return {"prodotto": gem, **{k: _r(v) for k, v in misure(ctx2, ctx2.trade(regola)).items() if k in ("n", "media_esc", "t", "euro_oggi")}}
        except (FileNotFoundError, KeyError, ValueError) as ex:
            return {"prodotto": gem, "errore": str(ex)}

    def figli(self, padre: dict) -> list[dict]:
        """L2: una condizione in più dalle ipotesi non ancora usate nel ramo, a ogni soglia dichiarata."""
        usate = {c[0] for c in padre["regola"].get("cond", [])}
        ordine = padre["n_cond"] + 1
        nuovi: list[dict] = []
        gruppi: list[tuple[dict, list[dict]]] = []
        for ip in self.spec["ingressi"]:
            if ip["grandezza"] in usate:
                continue
            serie = []
            for s in ip["soglie"]:
                reg = copy.deepcopy(padre["regola"])
                reg.setdefault("cond", []).append([ip["grandezza"], ip["op"], s])
                nd = self.nodo(reg, "L2", padre["id"], f"{ip['nome']} {ip['op']} {s:g}", ordine)
                if nd is None:
                    break
                nd["ipotesi"] = ip["nome"]
                serie.append(nd)
            gruppi.append((ip, serie))
            nuovi += serie
        if not nuovi:
            return []
        scelta = scelta_fratelli(self.ctx, [self._ann[n["id"]] for n in nuovi])
        scelta["genitore"], scelta["livello"] = padre["id"], "L2"
        scelta["fratelli"] = [n["id"] for n in nuovi]
        self.livelli.append(scelta)
        pm = padre["misure"]
        th = terzi(self.ctx)
        q_min = QUANTILE_FILTRO[min(ordine, 2)]
        livello_ok = scelta["mediana"] is not None and scelta["mediana"] > 0
        for ip, serie in gruppi:
            for k, nd in enumerate(serie):
                m = nd["misure"]
                fc = filtri_casuali(self.ctx, self.trade(nd["id"]), self.trade(padre["id"]))
                nd["filtri_casuali"] = fc
                migliora = []
                for mk in th:
                    _, mf, _ = _stat(self._ann[nd["id"]], mk)
                    _, mp, _ = _stat(self._ann[padre["id"]], mk)
                    migliora.append(mf is not None and mp is not None and mf > mp)
                vicini = [serie[j] for j in (k - 1, k + 1) if 0 <= j < len(serie)]
                vicini_ok = all((v["misure"].get("media_esc") or -math.inf) > (pm.get("media_esc") or math.inf) for v in vicini)
                media = m.get("media_esc")
                porte = [
                    _porta("Batte i filtri casuali", fc.get("quantile"), f">= {q_min:.0%}", None if fc.get("quantile") is None else fc["quantile"] >= q_min),
                    _porta("t del guadagno medio", m.get("t"), f">= {T_MIN:g}", None if m.get("t") is None else m["t"] >= T_MIN),
                    _porta("Trade l'anno", m.get("trade_anno"), f">= {TRADE_ANNO_FOGLIA:g}", m.get("trade_anno", 0) >= TRADE_ANNO_FOGLIA),
                    _porta("Migliora il genitore nei terzi del periodo", sum(migliora), ">= 2 su 3", sum(migliora) >= 2),
                    _porta("Soglie vicine migliorano il genitore", len(vicini), "tutte", vicini_ok),
                    _porta("I trade tolti vanno peggio", fc.get("resto_media"), f"< {_r(media, 3)}",
                           None if media is None or fc.get("resto_media") is None else fc["resto_media"] < media),
                    _porta("Scelta fra fratelli fuori campione (mediana CPCV)", scelta["mediana"], "> 0", livello_ok),
                    *porte_differenziale(nd["differenziale"]),
                ]
                self._chiudi(nd, porte, "pronto" if (m.get("G") or 0) >= 1 else "passa")
        return [n for n in nuovi if n["esito"] != "scartato"]

    def uscite(self, padre: dict) -> dict:
        """L3: varianti d'uscita; vince la migliore per punteggio fra quelle che migliorano utile/drawdown."""
        lato = int(padre["regola"]["lato"])
        varianti = [(v["nome"], v) for v in self.spec.get("uscite", [])]
        s = stop_da_mae(self.ctx, self.trade(padre["id"]), lato)
        if s is not None and not padre["regola"].get("stop"):
            varianti.append((f"stop {s:g} (escursione contraria dei vincenti)", {"stop": s}))
        nuovi = []
        for nome, v in varianti:
            reg = copy.deepcopy(padre["regola"])
            for k, val in v.items():
                if k in ("nome",):
                    continue
                if k == "uscita":
                    reg["uscita"] = dict(val)
                else:
                    reg[k] = val
            if reg == padre["regola"]:
                continue
            nd = self.nodo(reg, "L3", padre["id"], f"{padre['etichetta']}, {nome}", padre["n_cond"])
            if nd is None:
                break
            nuovi.append(nd)
        if not nuovi:
            return padre
        scelta = scelta_fratelli(self.ctx, [self._ann[padre["id"]]] + [self._ann[n["id"]] for n in nuovi])
        scelta.update({"genitore": padre["id"], "livello": "L3", "fratelli": [padre["id"]] + [n["id"] for n in nuovi]})
        self.livelli.append(scelta)
        ud_p = padre["misure"].get("utile_su_dd") or 0
        for nd in nuovi:
            m = nd["misure"]
            porte = [_porta("Utile/drawdown migliore del genitore", m.get("utile_su_dd"), f"> {_r(ud_p, 2)}", (m.get("utile_su_dd") or 0) > ud_p),
                     _porta("t del guadagno medio", m.get("t"), f">= {T_MIN:g}", None if m.get("t") is None else m["t"] >= T_MIN),
                     _porta("Trade l'anno", m.get("trade_anno"), f">= {TRADE_ANNO_FOGLIA:g}", m.get("trade_anno", 0) >= TRADE_ANNO_FOGLIA),
                     _porta("Scelta fra uscite fuori campione (mediana CPCV)", scelta["mediana"], "> 0",
                            scelta["mediana"] is not None and scelta["mediana"] > 0)]
            self._chiudi(nd, porte, "pronto" if (m.get("G") or 0) >= 1 else "passa")
        ok = [n for n in nuovi if n["esito"] != "scartato"]
        return max(ok, key=lambda n: n["punteggio"]) if ok else padre

    # -- walk-forward della procedura
    def procedura(self, radice: dict, mtr: np.ndarray) -> dict:
        """Ripete le scelte dell'albero usando solo gli anni della maschera: il figlio con il t più alto fra quelli
        che migliorano il genitore con t >= 2, fino a `max_condizioni`, poi la migliore uscita. Sceglie solo fra i
        nodi già valutati (i rami non approfonditi sul periodo intero restano fuori: limite dichiarato)."""
        cur = radice
        figli_di: dict[str, list[dict]] = {}
        for n in self.nodi:
            figli_di.setdefault(n["genitore"], []).append(n)
        for livello in ("L2", "L2", "L3"):
            _, mc, _ = _stat(self._ann[cur["id"]], mtr)
            migliore, tmax = None, -math.inf
            for f in figli_di.get(cur["id"], []):
                if f["livello"] != livello:
                    continue
                n, mf, t = _stat(self._ann[f["id"]], mtr)
                if n >= MIN_TRADE_TRAIN and t is not None and t >= T_MIN and mc is not None and mf > mc and t > tmax:
                    migliore, tmax = f, t
            if migliore is None:
                if livello == "L2":
                    continue
                break
            cur = migliore
        return cur

    def walkforward(self, radice: dict) -> dict:
        anni = np.array(self.ctx.anni)
        righe, tot = [], np.zeros(3)
        for y in range(max(WF_PRIMO_ANNO, anni[0] + 1), anni[-1] + 1):
            scelto = self.procedura(radice, anni < y)
            a = self._ann[scelto["id"]][anni == y][0]
            tot += a
            righe.append({"anno": y, "nodo": scelto["id"], "etichetta": scelto["etichetta"], "n": int(a[0]),
                          "media_esc": _r(a[1] / a[0]) if a[0] else None})
        return {"anni": righe, "n": int(tot[0]), "media_esc": _r(tot[1] / tot[0]) if tot[0] else None}

    # -- esecuzione
    # -- ampiezza: molte regole semplici, poi la scelta delle radici
    def ampiezza(self, log=print) -> list[dict]:
        """Prova ogni combinazione della griglia di `ampiezza` come radice (L0), poi sceglie fino a `max_radici` radici
        fra quelle che passano, in ordine di punteggio e saltando quelle troppo simili a una già scelta (correlazione
        dei risultati giornalieri oltre `correlazione_max`)."""
        a = self.spec["ampiezza"]
        chiavi = list(a["griglia"])
        combinazioni = list(product(*(a["griglia"][k] for k in chiavi)))
        self.nota("ampiezza", f"{len(combinazioni)} regole semplici da provare", len(combinazioni))
        nodi = []
        for valori in combinazioni:
            reg = copy.deepcopy(a["base"])
            for k, v in zip(chiavi, valori):
                if k == "ingresso":
                    reg["da"] = reg["a"] = v
                else:
                    reg[k] = copy.deepcopy(v)
            nd = self.nodo(reg, "L0", None, descrivi(reg, self.ctx.barre), 0, leggero=True)
            if nd is None:
                break
            nd["ampiezza"] = True
            self._chiudi(nd, porte_radice(nd["misure"], nd["cpcv"]))
            nodi.append(nd)
        passano = sorted([n for n in nodi if n["esito"] != "scartato"], key=lambda n: -n["punteggio"])
        self.nota("ampiezza", f"{len(passano)} su {len(nodi)} passano il primo livello (guadagno o margine, t >= 2, fuori campione CPCV positivo)",
                  len(nodi), len(passano))
        cmax, kmax = float(a.get("correlazione_max", 0.7)), int(a.get("max_radici", 10))
        scelte, serie = [], []
        for n in passano:
            g = self.ctx.giornaliera(self.trade(n["id"]))
            simile = next((s_ for s_, gs in zip(scelte, serie) if np.corrcoef(g, gs)[0, 1] > cmax), None)
            if simile is not None:
                n["scelta"] = f"simile a {simile['etichetta']}"
            elif len(scelte) >= kmax:
                n["scelta"] = f"oltre le prime {kmax}"
            else:
                n["scelta"] = "radice"
                scelte.append(n)
                serie.append(g)
        self.nota("radici", f"{len(scelte)} radici scelte (le migliori, saltando quelle simili fra loro)", len(passano), len(scelte))
        return scelte

    def profondita(self, rad: dict, log=print) -> list[dict]:
        """L2 e L3 su una radice che ha passato L1: ingressi in due giri, poi le uscite sui rami migliori."""
        spec = self.spec
        candidati = [rad] if rad["esito"] == "pronto" else []
        frontiera = [rad] if (rad["misure"].get("M") or 0) >= M_MIN else []
        for _ in range(int(spec.get("max_condizioni", 2))):
            nuova = []
            for p in frontiera:
                ok = sorted(self.figli(p), key=lambda n: -n["punteggio"])
                nuova += ok[: int(spec.get("rami_per_livello", 3))]
                log(f"  {p['etichetta']}: {len(ok)} figli passano" + (" (budget esaurito)" if self.esaurito else ""))
            candidati += nuova
            frontiera = [n for n in nuova if n["misure"].get("trade_anno", 0) >= TRADE_ANNO_RAMO and (n["misure"].get("M") or 0) >= 1]
            if self.esaurito:
                break
        if not candidati:
            candidati = [rad]
        candidati.sort(key=lambda n: ((n["misure"].get("G") or 0) >= 1, n["punteggio"]), reverse=True)   # prima i pronti
        finali = [self.uscite(c) for c in candidati[: int(spec.get("foglie_per_radice", 3))]]
        return list({f["id"]: f for f in finali}.values())

    def esegui(self, log=print) -> dict:
        t0 = time.time()
        spec = self.spec
        radici = []
        for r in spec.get("radici", []):
            rad = self.radice(r)
            if rad is None:
                break
            log(f"{rad['etichetta']}: {rad['esito']}" + (f" ({rad['motivo']})" if rad["motivo"] else ""))
            radici.append(rad)
        if spec.get("ampiezza"):
            for rad in self.ampiezza(log):
                self.livello1(rad)
                log(f"{rad['etichetta']}: {rad['esito']}" + (f" ({rad['motivo']})" if rad["motivo"] else ""))
                radici.append(rad)
        vive = [r for r in radici if r["esito"] != "scartato"]
        self.nota("radice", f"{len(vive)} radici su {len(radici)} reggono gemello, due metà del periodo e segnale isolato", len(radici), len(vive))
        foglie_per_radice = []
        for rad in vive:
            if self.esaurito:
                break
            foglie_per_radice.append((rad, self.profondita(rad, log)))
        l2 = [n for n in self.nodi if n["livello"] == "L2"]
        l3 = [n for n in self.nodi if n["livello"] == "L3"]
        self.nota("ingressi", f"{len(l2)} condizioni aggiunte alle radici, {sum(n['esito'] != 'scartato' for n in l2)} battono il caso e il genitore",
                  len(l2), sum(n["esito"] != "scartato" for n in l2))
        self.nota("uscite", f"{len(l3)} uscite provate, {sum(n['esito'] != 'scartato' for n in l3)} migliorano utile/drawdown",
                  len(l3), sum(n["esito"] != "scartato" for n in l3))
        if self.esaurito:
            self.nota("budget", f"budget di {self.budget} prove esaurito: la ricerca si ferma qui")
        foglie = []
        self.wf_ricerca = self.wf_esterno or (self.walkforward_ricerca() if spec.get("ampiezza") else None)
        for rad, finali in foglie_per_radice:
            wf = self.wf_ricerca or self.walkforward(rad)
            for f in finali:
                foglie.append(self.verifica(f, wf))
        self.nota("verifica", f"{len(foglie)} sistemi finali verificati (minuto per minuto, costi doppi, gemello, DSR, walk-forward), "
                              f"{sum(f['passa_scoperta'] for f in foglie)} passano", len(foglie), sum(f["passa_scoperta"] for f in foglie))
        return {"durata_s": round(time.time() - t0, 1), "foglie": foglie}

    def walkforward_ricerca(self) -> dict:
        """Walk-forward dell'intera ricerca: per ogni anno sceglie la radice migliore con gli anni precedenti (stesso
        punteggio dell'ampiezza, calcolato solo su quegli anni), poi ripete le scelte dell'albero su quella radice."""
        anni = np.array(self.ctx.anni)
        radici = [n for n in self.nodi if n["livello"] == "L0"]
        righe, tot = [], np.zeros(3)
        for y in range(max(WF_PRIMO_ANNO, anni[0] + 1), anni[-1] + 1):
            mtr = anni < y
            migliore, smax = None, -math.inf
            for r in radici:
                n, m, t = _stat(self._ann[r["id"]], mtr)
                ric = r["misure"].get("richiesto")
                if n < MIN_TRADE_TRAIN or t is None or t < T_MIN or m <= 0 or not ric or self.ctx.euro_esc is None:
                    continue
                sc = m * self.ctx.euro_esc / ric * min(1.0, t / 3)
                if sc > smax:
                    migliore, smax = r, sc
            if migliore is None:
                righe.append({"anno": y, "nodo": None, "etichetta": "nessuna radice", "n": 0, "media_esc": None})
                continue
            scelto = self.procedura(migliore, mtr)
            a = self._ann[scelto["id"]][anni == y][0]
            tot += a
            righe.append({"anno": y, "nodo": scelto["id"], "etichetta": scelto["etichetta"], "n": int(a[0]),
                          "media_esc": _r(a[1] / a[0]) if a[0] else None})
        return {"anni": righe, "n": int(tot[0]), "media_esc": _r(tot[1] / tot[0]) if tot[0] else None, "intera_ricerca": True}

    # -- L4
    def verifica(self, foglia: dict, wf: dict) -> dict:
        ctx = self.ctx
        reg = foglia["regola"]
        m1 = getattr(self, "_m1", None)
        if m1 is None:
            m1 = self._m1 = dati.minuti(ctx.prodotto)
        _, tm = backtest.simula(ctx.prodotto, ctx.barre, reg, ctx.tab, m1)
        mm = misure(ctx, tm)
        doppi = misure(ctx, ctx.trade(reg, molt_costi=2.0))
        gem = self._gemello(reg) if self.spec.get("gemello") else {}
        g = ctx.giornaliera(tm)
        mc = metriche.montecarlo(g, n=2000)
        srs = [n["misure"].get("sharpe") for n in self.nodi if n["misure"].get("sharpe") is not None]
        n_prove = self.prove + int(self.spec.get("prove_pregresse", 0)) + int(self.prove_esterne or 0)
        var_sr = self.var_sr_esterna if self.var_sr_esterna is not None else (float(np.var(srs, ddof=1)) if len(srs) > 1 else 0.0)
        dsr = float(metriche.dsr(g, n_prove, var_sr)) if g.std() > 0 else None
        eff = (wf["media_esc"] / mm["media_esc"]) if wf.get("media_esc") is not None and mm.get("media_esc") else None
        d = differenziale(ctx, reg, tm, int(reg["lato"]))
        porte = [
            _porta("Guadagno medio in euro di oggi (G >= 1)", mm.get("euro_oggi"), f">= {mm.get('richiesto', 0):g} € (durata {(mm.get('ore_medie') or 0):.1f} ore)",
                   None if mm.get("G") is None else mm["G"] >= 1),
            _porta("Trade l'anno", mm.get("trade_anno"), f">= {TRADE_ANNO_FOGLIA:g}", mm.get("trade_anno", 0) >= TRADE_ANNO_FOGLIA),
            _porta("t del guadagno medio", mm.get("t"), f">= {T_MIN:g}", None if mm.get("t") is None else mm["t"] >= T_MIN),
            _porta("Regolarità (R²)", mm.get("r2"), f">= {R2_MIN}", None if mm.get("r2") is None else mm["r2"] >= R2_MIN),
            _porta("Anni positivi", mm.get("anni_positivi"), f">= {ANNI_POSITIVI_MIN:.0%}", None if mm.get("anni_positivi") is None else mm["anni_positivi"] >= ANNI_POSITIVI_MIN),
            _porta("Costi doppi: guadagno medio", doppi.get("media_esc"), "> 0", None if doppi.get("media_esc") is None else doppi["media_esc"] > 0),
            *([_porta(f"Gemello {gem.get('prodotto')}", gem.get("media_esc"), "> 0", None if gem.get("media_esc") is None else gem["media_esc"] > 0)] if gem else []),
            *porte_differenziale(d),
            _porta("DSR sulle prove fatte", dsr, f">= {DSR_MIN} ({n_prove} prove)", None if dsr is None else dsr >= DSR_MIN),
            _porta("Walk-forward della procedura (efficienza)", eff, f">= {WF_EFFICIENZA_MIN:g}", None if eff is None else eff >= WF_EFFICIENZA_MIN),
            _porta("Drawdown a blocchi / rimescolato", mc.get("rapporto_dd"), "informativo", None, info=True),
        ]
        mot = _motivo(porte)
        return {"id": foglia["id"], "etichetta": foglia["etichetta"], "regola": reg, "misure_minuto": mm, "costi_doppi": doppi,
                "gemello": gem, "differenziale": d, "dsr": dsr, "n_prove": n_prove, "walkforward": wf, "efficienza_wf": eff,
                "montecarlo": {"rapporto_dd": mc.get("rapporto_dd"), "dd_p95_esc": metriche._num(mc["blocchi"]["drawdown"]["p95"]) if mc.get("blocchi") else None},
                "porte": porte, "passa_scoperta": mot is None, "motivo": mot, "_trade": tm}


# ---------------------------------------------------------------- descrizioni

NOMI_GRANDEZZE = {"dal_close_ieri": "dalla chiusura di ieri", "gap": "apertura su chiusura di ieri", "rsi": "RSI",
                  "dal_massimo_seduta": "dal massimo di oggi", "dal_minimo_ieri": "dal minimo di ieri",
                  "pos_chiusura_ieri": "chiusura di ieri nel suo intervallo", "dist_media": "distanza dalla media",
                  "escursione_oggi": "escursione di oggi", "vol_relativa": "volatilità del periodo", "dal_1530": "dalle 15:30",
                  "giorno_mese": "giorno del mese", "terzo_venerdi": "terzo venerdì", "dist_apertura": "dall'apertura"}


def descrivi(regola: dict, barre: int) -> str:
    """Nome leggibile di una regola: ora d'ingresso, condizioni, uscita."""
    cond = " e ".join(f"{NOMI_GRANDEZZE.get(c[0].split(':')[0], c[0])} {c[1]} {c[2]:g}" for c in regola.get("cond", []))
    u = regola.get("uscita") or {}
    if u.get("barre") is not None:
        usc = f"esce dopo {(int(u['barre']) + 2) * barre} min"
    elif u.get("ora"):
        usc = f"esce alle {u['ora']}"
    elif u.get("giorni"):
        usc = "esce il giorno dopo all'apertura" if int(u["giorni"]) == 1 else f"esce dopo {u['giorni']} giorni"
    else:
        usc = "uscita"
    stop = f", stop {regola['stop']:g}" if regola.get("stop") else ""
    return f"{regola.get('da', '')}{', ' + cond if cond else ''} → {usc}{stop}"


# ---------------------------------------------------------------- file d'esperimento

def carica(file) -> dict:
    return json.loads(Path(file).read_text(encoding="utf-8"))


def controlla(file) -> dict:
    """Errori di forma del file e numero massimo di prove prevedibile."""
    e = carica(file)
    errori = [f"manca o è sbagliato '{k}'" for k, tp in OBBLIGATORI.items() if not isinstance(e.get(k), tp)]
    if e.get("tipo") not in ("ricerca", "albero"):
        errori.append("tipo deve essere 'ricerca'")
    if not e.get("radici") and not e.get("ampiezza"):
        errori.append("servono 'radici' o 'ampiezza'")
    a = e.get("ampiezza")
    n_amp = 0
    if a:
        if not isinstance(a.get("base"), dict) or not isinstance(a.get("griglia"), dict):
            errori.append("ampiezza: servono 'base' e 'griglia'")
        else:
            n_amp = math.prod(len(v) for v in a["griglia"].values())
            for cond in (c for v in a["griglia"].get("cond", []) for c in v):
                try:
                    condizioni.grandezza(cond[0], 1)
                except (KeyError, ValueError):
                    errori.append(f"ampiezza: grandezza sconosciuta {cond[0]}")
    for ip in e.get("ingressi", []):
        for k in ("nome", "meccanismo", "direzione", "grandezza", "op", "soglie"):
            if k not in ip:
                errori.append(f"ingresso {ip.get('nome', '?')}: manca '{k}'")
        try:
            condizioni.grandezza(ip.get("grandezza", ""), 1)
        except (KeyError, ValueError):
            errori.append(f"ingresso {ip.get('nome', '?')}: grandezza sconosciuta {ip.get('grandezza')}")
    try:
        catalogo.prodotto(e.get("prodotto", ""))
    except KeyError:
        errori.append(f"prodotto sconosciuto {e.get('prodotto')}")
    n_ip = sum(len(ip.get("soglie", [])) for ip in e.get("ingressi", []))
    rami = int(e.get("rami_per_livello", 3))
    n_rad = len(e.get("radici", [])) + (int(a.get("max_radici", 10)) if a else 0)
    stima = n_amp + n_rad * (n_ip + rami * n_ip + int(e.get("foglie_per_radice", 3)) * (len(e.get("uscite", [])) + 1))
    return {"file": str(file), "ok": not errori, "errori": errori, "prove_ampiezza": n_amp, "prove_massime_stimate": stima,
            "budget": e.get("budget")}


def _mini(ctx: Contesto, trade: pl.DataFrame, punti: int = 60) -> list:
    if ctx.euro_esc is None or not trade.height:
        return []
    c = np.cumsum(ctx.giornaliera(trade)) * ctx.euro_esc
    idx = np.unique(np.linspace(0, len(c) - 1, punti).round().astype(int))
    return [round(float(c[i]), 1) for i in idx]


def _curva_foglia(ctx: Contesto, ver: dict, holdout: pl.DataFrame | None) -> dict:
    """Curva della foglia in euro di oggi: holdout all'indietro, scoperta (con il riferimento D2 sugli stessi trade e
    gli anni del walk-forward), holdout in avanti. Holdout convertiti con la stessa escursione di oggi."""
    tm = ver["_trade"]
    e = ctx.euro_esc or 0.0
    g = ctx.giornaliera(tm) * e
    rif_netto = (ver["differenziale"].get("rif_netto") or 0.0) * e
    r = np.bincount(np.minimum(np.searchsorted(ctx.date, tm["uscita"].dt.date().to_numpy().astype("datetime64[D]")), len(ctx.date) - 1),
                    minlength=len(ctx.date)) * rif_netto
    parti = []
    if holdout is not None and holdout.height and "netto" in holdout.columns:
        for p in ("antico", "vicino", "avanti"):
            x = holdout.filter(pl.col("periodo") == p).sort("data")
            if x.height:
                parti.append((p, x["data"].to_numpy().astype("datetime64[D]"), x["netto"].to_numpy() * e, None))
    parti.append(("scoperta", ctx.date, g, r))
    parti.sort(key=lambda q: q[1][0])
    date, cum, rif, seg, base, base_r = [], [], [], [], 0.0, 0.0
    for p, d, x, rr in parti:
        c = base + np.cumsum(x)
        seg.append([p, len(date), len(date) + len(c) - 1])
        date += [str(v) for v in d]
        cum += np.round(c, 1).tolist()
        if rr is not None:
            cr = base + np.cumsum(rr)
            rif += np.round(cr, 1).tolist()
            base_r = float(cr[-1])
        else:
            rif += [None] * len(c)
        base = float(c[-1])
    wf = [a["anno"] for a in ver["walkforward"]["anni"]]
    # riduzione a circa 700 punti per il grafico
    passo = max(1, len(cum) // 700)
    idx = sorted(set(range(0, len(cum), passo)) | {s[1] for s in seg} | {s[2] for s in seg})
    pos = {i: k for k, i in enumerate(idx)}
    return {"date": [date[i] for i in idx], "cum": [cum[i] for i in idx], "rif": [rif[i] for i in idx],
            "segmenti": [[p, pos[a], pos[b]] for p, a, b in seg], "anni_wf": wf, "unita": "euro di oggi"}


def _scrivi_stato(cart: Path, stato: dict) -> None:
    tmp = cart / "stato.json.tmp"
    tmp.write_text(json.dumps(stato, ensure_ascii=False), encoding="utf-8")
    tmp.replace(cart / "stato.json")


def imbuto(al: "Albero", foglie: list[dict]) -> list[dict]:
    """Quante regole entrano e quante passano a ogni strato, per il diagramma del cruscotto."""
    l0 = [n for n in al.nodi if n["livello"] == "L0"]
    radici = [n for n in l0 if n.get("livello1")]
    l2 = [n for n in al.nodi if n["livello"] == "L2"]
    l3 = [n for n in al.nodi if n["livello"] == "L3"]
    ver = [f for f in foglie if f["passa_scoperta"]]
    return [
        {"strato": "ampiezza", "nome": "Regole semplici provate", "n": len(l0)},
        {"strato": "L0", "nome": "Guadagno o margine, non caso",
         "n": sum(1 for n in l0 if n.get("scelta") or (not n.get("ampiezza") and n.get("livello1")))},
        {"strato": "radici", "nome": "Radici scelte, diverse fra loro", "n": len(radici)},
        {"strato": "L1", "nome": "Reggono gemello, metà del periodo, segnale isolato", "n": sum(n["esito"] != "scartato" for n in radici)},
        {"strato": "L2", "nome": "Ingressi che battono il caso", "n": sum(n["esito"] != "scartato" for n in l2), "provati": len(l2)},
        {"strato": "L3", "nome": "Uscite che migliorano", "n": sum(n["esito"] != "scartato" for n in l3), "provati": len(l3)},
        {"strato": "L4", "nome": "Sistemi finali che passano la verifica", "n": len(ver), "provati": len(foglie)},
        {"strato": "finale", "nome": "Passano 2024-2025 e il passato: da provare su ProRealTime", "n": sum(f["esito"] == "candidato" for f in foglie)},
    ]


def lancia(file, log=print) -> dict:
    """Esegue la ricerca (ampiezza e profondità), registra le prove, fa la prova finale una volta sola sulle foglie che
    passano tutto e scrive `risultati/ricerche/<nome>/ricerca.json`; durante il lavoro aggiorna `stato.json`.
    Una ricerca già lanciata non si rilancia."""
    c = controlla(file)
    if not c["ok"]:
        raise ValueError("; ".join(c["errori"]))
    spec = carica(file)
    cart = CARTELLA / spec["nome"]
    if (cart / "ricerca.json").exists() or (cart / "albero.json").exists():
        raise ValueError(f"ricerca {spec['nome']} già lanciata: la prova finale si usa una volta sola (cambiare nome per una ricerca nuova)")
    cart.mkdir(parents=True, exist_ok=True)
    inizio = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _scrivi_stato(cart, {"stato": "in corso", "inizio": inizio, "prove": 0, "budget": spec["budget"], "fase": "preparazione"})
    al = Albero(spec)
    ultimo = [0.0]

    def osserva(fatte, budget):
        if time.time() - ultimo[0] > 2:
            ultimo[0] = time.time()
            _scrivi_stato(cart, {"stato": "in corso", "inizio": inizio, "prove": fatte, "budget": budget,
                                 "fase": al.diario[-1]["testo"] if al.diario else "", "diario": al.diario})
    al.osserva = osserva
    try:
        ris = al.esegui(log)
    except Exception as ex:
        _scrivi_stato(cart, {"stato": "fallita", "inizio": inizio, "errore": f"{type(ex).__name__}: {ex}", "diario": al.diario})
        raise
    return concludi(al, ris, spec, cart, inizio)


def concludi(al: "Albero", ris: dict, spec: dict, cart: Path, inizio: str, extra: dict | None = None) -> dict:
    """Registro, prova finale una volta sola sulle foglie che passano la scoperta, scrittura di `ricerca.json`."""
    ctx = al.ctx
    fam = f"ricerca:{spec['nome']}"
    prove = [({"nodo": n["id"], "regola": n["regola"]}, ctx.giornaliera(al.trade(n["id"]))) for n in al.nodi]
    ids = dict(zip([n["id"] for n in al.nodi], validazione.registra_molti(spec["nome"], fam, ctx.prodotto, prove, ctx.date)))
    for n in al.nodi:
        n["registro"] = ids[n["id"]]
    al.nota("registro", f"{al.prove} prove scritte nel registro (contano per il DSR delle ricerche future)")
    foglie = []
    for v in ris["foglie"]:
        pf, hold = None, None
        if v["passa_scoperta"]:
            fh = cart / f"{v['id']}_holdout.parquet"
            pf = prova_finale.esegui(ctx.prodotto, ctx.barre, v["regola"], ids[v["id"]], salva_in=fh)
            hold = pl.read_parquet(fh) if fh.exists() else None
        mm = v["misure_minuto"]
        voci_pf = giudizio.prova_finale_voci(pf, mm.get("euro_oggi"), mm) if pf else None
        mot = v["motivo"] or (giudizio._motivo(voci_pf) if voci_pf else None)
        v["curva"] = _curva_foglia(ctx, v, hold)
        v.pop("_trade")
        tr = uscita.traduci(v["regola"], ctx.prodotto, ctx.barre)
        foglie.append({**v, "prova_finale": pf, "voci_prova_finale": voci_pf, "prorealcode": tr,
                       "esito": "candidato" if v["passa_scoperta"] and mot is None else "scartato",
                       "motivo": mot or "passa tutte le porte e la prova finale"})
    n_pf = sum(f["prova_finale"] is not None for f in foglie)
    al.nota("prova finale", f"prova finale (2024-2025, 2011-2013, prima del 2011) eseguita su {n_pf} sistemi; "
                            f"{sum(f['esito'] == 'candidato' for f in foglie)} la passano", n_pf, sum(f["esito"] == "candidato" for f in foglie))
    for n in al.nodi:
        n["mini"] = _mini(ctx, al.trade(n["id"]))
    out = {"intestazione": spec, "quando": inizio, "fine": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "prove": al.prove, "budget": al.budget, "budget_esaurito": al.esaurito, "durata_s": ris["durata_s"],
           "anni": list(SCOPERTA), "euro_per_escursione_oggi": _r(ctx.euro_esc, 2), "esc_oggi_punti": _r(ctx.esc_oggi, 1),
           "imbuto": imbuto(al, foglie), "diario": al.diario, "walkforward_ricerca": al.wf_ricerca,
           "nodi": al.nodi, "livelli": al.livelli, "foglie": foglie, **(extra or {})}
    if extra and "imbuto_cicli" in extra:
        out["imbuto"] = extra["imbuto_cicli"] + [x for x in imbuto(al, foglie) if x["strato"] in ("L1", "L3", "L4", "finale")]
        out["prove"] = al.prove + extra.get("prove_cicli", 0)
        out["durata_s"] = round(ris["durata_s"] + extra.get("durata_cicli_s", 0), 1)
    (cart / "ricerca.json").write_text(json.dumps(metriche.pulisci(out), ensure_ascii=False, indent=1), encoding="utf-8")
    _scrivi_stato(cart, {"stato": "finita", "inizio": inizio, "fine": out["fine"], "prove": out["prove"], "budget": al.budget})
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    comando, file = sys.argv[1], sys.argv[2]
    if comando == "controlla":
        print(json.dumps(controlla(file), ensure_ascii=False, indent=1))
    elif comando == "lancia":
        r = lancia(file)
        print(f"{r['prove']} prove in {r['durata_s']} s")
        for f in r["foglie"]:
            print(f"{f['id']} {f['etichetta']}: {f['esito']} — {f['motivo']}")
    else:
        raise SystemExit("uso: python -m motore.albero controlla|lancia <file.json>")
