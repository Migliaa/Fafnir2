"""Validazione fuori campione e registro unico dei tentativi. Fonti: `fonti/paper/validazione-e-metriche.md`, parte A.

Le funzioni ricevono array (`matrice` = giorni x varianti, zeri inclusi; `date` = datetime64[D]) e non
leggono dati di mercato. Solo il registro scrive su disco, in `risultati/registro/`.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from itertools import combinations

import numpy as np
import polars as pl
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from scipy.stats import norm, rankdata

from . import metriche
from .config import RISULTATI

CARTELLA = RISULTATI / "registro"  # i test la sostituiscono con una cartella temporanea


def _anni(date) -> np.ndarray:
    return np.asarray(date).astype("datetime64[Y]").astype(int) + 1970


def _sharpe_colonne(m: np.ndarray) -> np.ndarray:
    """Sharpe annualizzato di ogni colonna; -inf dove la deviazione standard è zero."""
    s = m.std(axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        sr = m.mean(axis=0) / s * math.sqrt(metriche.GIORNI_ANNO)
    return np.where(s > 0, sr, -np.inf)


# ---------------------------------------------------------------- CPCV

def blocchi_cpcv(anni, k: int = 2) -> list[tuple[list[int], list[int]]]:
    """Tutte le combinazioni di k anni di test (13 anni, k=2: 78) come (anni di training, anni di test)."""
    tutti = sorted({int(a) for a in anni})
    return [([a for a in tutti if a not in test], list(test)) for test in combinations(tutti, k)]


def purga(trade_inizio, trade_fine, anni_test, embargo_giorni: int) -> np.ndarray:
    """Maschera dei trade di training da tenere (López de Prado 2018, cap. 7, A3).

    Si scartano i trade che si sovrappongono a un anno di test, allargato di `embargo_giorni`
    dopo la sua fine. `trade_inizio` e `trade_fine` sono datetime64.
    """
    ini, fin = np.asarray(trade_inizio, dtype="datetime64[s]"), np.asarray(trade_fine, dtype="datetime64[s]")
    tieni = np.ones(len(ini), dtype=bool)
    for a in anni_test:
        da = np.datetime64(f"{int(a)}-01-01", "s")
        a_ = np.datetime64(f"{int(a) + 1}-01-01", "s") + np.timedelta64(int(embargo_giorni), "D")
        tieni &= ~((ini < a_) & (fin >= da))
    return tieni


def cpcv_selezione(matrice, date, k: int = 2, embargo_giorni: int = 5) -> dict:
    """CPCV (A3): per ogni combinazione sceglie la variante col miglior Sharpe nel training e ne
    registra lo Sharpe sui k anni di test.

    I giorni di training entro `embargo_giorni` di calendario prima dell'inizio e dopo la fine di
    un blocco di test sono scartati (versione giornaliera di purga ed embargo: la durata massima di un
    trade è 5 giorni). Uscita: mediana, 10° percentile e quota positiva degli Sharpe fuori campione,
    e quante volte è stata scelta ciascuna variante.
    """
    m, d = np.asarray(matrice, dtype=float), np.asarray(date).astype("datetime64[D]")
    anni = _anni(d)
    emb = np.timedelta64(int(embargo_giorni), "D")
    scelte = np.zeros(m.shape[1], dtype=int)
    oos = []
    for train, test in blocchi_cpcv(anni, k):
        in_test = np.isin(anni, test)
        vicino = np.zeros(len(d), dtype=bool)
        for a in test:
            da = np.datetime64(f"{a}-01-01", "D")
            a_ = np.datetime64(f"{a + 1}-01-01", "D")
            vicino |= (d >= da - emb) & (d < a_ + emb)
        tr = np.isin(anni, train) & ~vicino
        if tr.sum() < 3 or in_test.sum() < 3:
            continue
        best = int(np.argmax(_sharpe_colonne(m[tr])))
        scelte[best] += 1
        oos.append(_sharpe_colonne(m[in_test][:, [best]])[0])
    o = np.array(oos)
    return {"n_combinazioni": len(o), "mediana": _r(np.median(o)), "p10": _r(np.percentile(o, 10)),
            "quota_positiva": _r(np.mean(o > 0)), "scelte": scelte.tolist()}


def _r(x):
    x = float(x)
    return round(x, 4) if math.isfinite(x) else None


# ---------------------------------------------------------------- PBO (CSCV)

def pbo(matrice, s: int = 16) -> dict:
    """Probability of Backtest Overfitting con CSCV (Bailey, Borwein, López de Prado, Zhu 2017, A4).

    Il tempo è diviso in `s` blocchi contigui; per ognuna delle C(s, s/2) combinazioni la metà
    in-sample sceglie la variante con lo Sharpe migliore e si guarda il suo rango relativo
    omega = rango/(N+1) sull'altra metà; logit = ln(omega/(1-omega)); PBO = quota di logit <= 0.
    Uscita anche: mediana dei logit, `prob_perdita_oos` (quota di combinazioni dove la scelta ha Sharpe
    fuori campione negativo) e `degrado_pendenza` (pendenza della regressione dello Sharpe fuori campione
    su quello in-sample della variante scelta; 1 = nessun degrado, 0 o meno = nessun legame).
    """
    m = np.asarray(matrice, dtype=float)
    if s % 2:
        raise ValueError("s deve essere pari")
    n = m.shape[1]
    parti = np.array_split(m, s)
    cnt = np.array([len(p) for p in parti], dtype=float)[:, None]
    s1 = np.array([p.sum(axis=0) for p in parti])
    s2 = np.array([(p ** 2).sum(axis=0) for p in parti])
    comb = np.array(list(combinations(range(s), s // 2)))
    tutte = np.arange(s)
    comp = np.array([np.setdiff1d(tutte, c) for c in comb])

    def sharpe_gruppi(idx):
        c, a, b = cnt[idx].sum(axis=1), s1[idx].sum(axis=1), s2[idx].sum(axis=1)
        media = a / c
        var = np.maximum(b / c - media ** 2, 0) * c / (c - 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(var > 0, media / np.sqrt(var), -np.inf)

    sr_is, sr_oos = sharpe_gruppi(comb), sharpe_gruppi(comp)
    best = np.argmax(sr_is, axis=1)
    righe = np.arange(len(comb))
    rango = rankdata(sr_oos, axis=1)[righe, best]
    omega = rango / (n + 1)
    logit = np.log(omega / (1 - omega))
    x, y = sr_is[righe, best], sr_oos[righe, best]
    pend = np.cov(x, y)[0, 1] / np.var(x, ddof=1) if np.var(x) > 0 else float("nan")
    return {"pbo": _r(np.mean(logit <= 0)), "mediana_logit": _r(np.median(logit)),
            "prob_perdita_oos": _r(np.mean(y < 0)), "degrado_pendenza": _r(pend),
            "n_combinazioni": len(comb)}


# ---------------------------------------------------------------- SPA e Romano-Wolf

def _bootstrap_medie(m: np.ndarray, b: int, lungh_blocco, seed: int):
    """Medie dei ricampionamenti e lunghezza del blocco (mediana di Politis-White sulle colonne)."""
    if lungh_blocco is None:
        lungh_blocco = float(np.median([metriche.lunghezza_blocco(m[:, j]) for j in range(m.shape[1])]))
    return metriche.medie_bootstrap(np.ascontiguousarray(m), b, 1.0 / lungh_blocco, seed), lungh_blocco


def spa(matrice, b: int = 2000, lungh_blocco=None, seed: int = 0) -> dict:
    """Test SPA di Hansen (2005, A7) contro rendimento zero, con bootstrap stazionario.

    Statistica T = max(max_k sqrt(n) d_k / w_k, 0) con w_k scarto del bootstrap; i valori sotto
    ipotesi nulla sono ricentrati con la versione consistente di Hansen (media corretta solo per le
    varianti con t < -sqrt(2 ln ln n)). p-value = (1 + #{T* >= T}) / (1 + b).
    """
    m = np.asarray(matrice, dtype=float)
    n = len(m)
    dbar = m.mean(axis=0)
    mb, lb = _bootstrap_medie(m, b, lungh_blocco, seed)
    omega = np.sqrt(n) * mb.std(axis=0, ddof=1)
    omega = np.where(omega > 0, omega, np.inf)
    t = np.sqrt(n) * dbar / omega
    stat = max(float(t.max()), 0.0)
    ricentra = np.where(t <= -math.sqrt(2 * math.log(math.log(n))), dbar, 0.0)
    tstar = np.sqrt(n) * (mb - dbar + ricentra) / omega
    stat_b = np.maximum(tstar.max(axis=1), 0.0)
    return {"p": _r((1 + np.sum(stat_b >= stat)) / (1 + b)), "statistica": _r(stat),
            "lungh_blocco": _r(lb), "migliore": int(np.argmax(t))}


def romano_wolf(matrice, b: int = 2000, lungh_blocco=None, seed: int = 0) -> dict:
    """Stepdown di Romano, Wolf (2005, A7): p-value aggiustati per ogni variante (rendimento medio > 0).

    Statistiche t studentizzate col bootstrap stazionario congiunto; al passo j si confronta la t della
    j-esima variante con il massimo, per ricampionamento, delle t delle varianti non ancora respinte;
    i p-value sono resi non decrescenti. p = (1 + conteggio) / (1 + b).
    """
    m = np.asarray(matrice, dtype=float)
    n = len(m)
    dbar = m.mean(axis=0)
    mb, lb = _bootstrap_medie(m, b, lungh_blocco, seed)
    omega = mb.std(axis=0, ddof=1)
    omega = np.where(omega > 0, omega, np.inf)
    t = dbar / omega
    tstar = (mb - dbar) / omega
    ordine = np.argsort(-t)
    # massimo dei t* sulle varianti dalla j-esima in poi (le non ancora respinte), per ogni ricampionamento
    mass = np.maximum.accumulate(tstar[:, ordine][:, ::-1], axis=1)[:, ::-1]
    p_ord = (1 + np.sum(mass >= t[ordine][None, :], axis=0)) / (1 + b)
    p_ord = np.maximum.accumulate(p_ord)
    p = np.empty(len(t))
    p[ordine] = p_ord
    return {"p": [_r(x) for x in p], "lungh_blocco": _r(lb)}


# ---------------------------------------------------------------- haircut dello Sharpe

def haircut(sr_annuo: float, anni: float, n_prove: int, metodo: str = "bhy", rango: int = 1) -> dict:
    """Sharpe corretto per prove multiple, Harvey e Liu (2015, A8).

    t = SR sqrt(anni), p a due code. Il p-value della strategia è il `rango`-esimo (1 = il migliore delle
    n_prove, il caso della selezione). Bonferroni: min(M p, 1); Holm: min((M - rango + 1) p, 1);
    BHY: min(M c(M) p / rango, 1) con c(M) = somma 1/i. Il p-value corretto si riconverte in t e in Sharpe.
    Le fonti non danno i p-value delle altre prove: per questo il rango è un'ipotesi esplicita.
    `sr_corretto` e `haircut` si riferiscono a `metodo` ("bonferroni", "holm", "bhy").
    """
    if metodo not in ("bonferroni", "holm", "bhy"):
        raise ValueError(metodo)
    t = sr_annuo * math.sqrt(anni)
    p = 2 * (1 - norm.cdf(abs(t)))
    mm = int(n_prove)
    c = sum(1 / i for i in range(1, mm + 1))
    padj = {"bonferroni": min(mm * p, 1.0), "holm": min((mm - rango + 1) * p, 1.0),
            "bhy": min(mm * c * p / rango, 1.0)}
    out = {}
    for nome, pa in padj.items():
        sr_c = norm.ppf(1 - pa / 2) / math.sqrt(anni) if pa < 1 else 0.0
        out[nome] = {"p_corretto": _r(pa), "sr_corretto": _r(sr_c), "haircut": _r(1 - sr_c / sr_annuo)}
    out["metodo"] = metodo
    out["sr_corretto"] = out[metodo]["sr_corretto"]
    out["haircut"] = out[metodo]["haircut"]
    return out


# ---------------------------------------------------------------- numero di prove indipendenti

def n_indipendenti(matrice, soglia_corr: float = 0.5) -> dict:
    """Numero effettivo di prove (Bailey et al. 2014 suggeriscono PCA o clustering, A5).

    `autovalori` = (somma l)^2 / somma l^2 sugli autovalori della matrice di correlazione;
    `cluster` = numero di gruppi con legame medio e distanza 1 - correlazione <= `soglia_corr`.
    Le colonne costanti si escludono.
    """
    m = np.asarray(matrice, dtype=float)
    m = m[:, m.std(axis=0) > 0]
    k = m.shape[1]
    if k < 2:
        return {"autovalori": float(k), "cluster": k}
    corr = np.corrcoef(m, rowvar=False)
    lam = np.clip(np.linalg.eigvalsh(corr), 0, None)
    dist = np.clip(1 - corr, 0, None)
    np.fill_diagonal(dist, 0)
    gruppi = fcluster(linkage(squareform(dist, checks=False), "average"), soglia_corr, "distance")
    return {"autovalori": float(lam.sum() ** 2 / np.sum(lam ** 2)), "cluster": int(len(np.unique(gruppi)))}


# ---------------------------------------------------------------- registro dei tentativi

def _nome_file(famiglia: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", famiglia)


def _righe() -> list[dict]:
    f = CARTELLA / "tentativi.jsonl"
    if not f.exists():
        return []
    return [json.loads(r) for r in f.read_text(encoding="utf-8").splitlines() if r.strip()]


def registra(esperimento: str, famiglia: str, prodotto: str, parametri: dict, giorn, date) -> str:
    """Aggiunge un tentativo a `tentativi.jsonl` e la sua serie giornaliera a `curve/<famiglia>.parquet`
    (una colonna per tentativo, righe = date, zero dove il tentativo non ha il giorno). Restituisce l'id."""
    CARTELLA.mkdir(parents=True, exist_ok=True)
    (CARTELLA / "curve").mkdir(exist_ok=True)
    g, d = np.asarray(giorn, dtype=float), np.asarray(date).astype("datetime64[D]")
    id_ = f"t{len(_righe()) + 1:06d}"
    riga = {"id": id_, "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "esperimento": esperimento, "famiglia": famiglia, "prodotto": prodotto, "parametri": parametri,
            "sharpe": _r(metriche.sharpe(g)), "giorni": int(len(g))}
    with open(CARTELLA / "tentativi.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    nuova = pl.DataFrame({"data": d.astype("datetime64[D]"), id_: g}).with_columns(pl.col("data").cast(pl.Date))
    pq = CARTELLA / "curve" / f"{_nome_file(famiglia)}.parquet"
    if pq.exists():
        nuova = pl.read_parquet(pq).join(nuova, on="data", how="full", coalesce=True).sort("data")
    nuova.write_parquet(pq)
    return id_


def conteggio(famiglia: str | None = None) -> dict:
    """Numero di prove, numero effettivo, varianza degli Sharpe: ingressi di DSR e MinBTL.

    Il numero effettivo si calcola sulle serie giornaliere dei tentativi (giorni mancanti = 0), in due
    versioni (`n_effettivo_autovalori`, `n_effettivo_cluster`, vedi `n_indipendenti`).
    `var_sharpe` è la varianza (ddof=1) degli Sharpe annualizzati dei tentativi; None con meno di due.
    """
    righe = [r for r in _righe() if famiglia is None or r["famiglia"] == famiglia]
    out = {"famiglia": famiglia, "n_prove": len(righe), "famiglie": sorted({r["famiglia"] for r in righe}),
           "n_effettivo_autovalori": None, "n_effettivo_cluster": None, "var_sharpe": None}
    if not righe:
        return out
    sr = [r["sharpe"] for r in righe if r["sharpe"] is not None]
    out["var_sharpe"] = _r(np.var(sr, ddof=1)) if len(sr) > 1 else None
    ids = {r["id"] for r in righe}
    serie = []
    for fam in out["famiglie"]:
        pq = CARTELLA / "curve" / f"{_nome_file(fam)}.parquet"
        if pq.exists():
            df = pl.read_parquet(pq)
            serie.append(df.select("data", *[c for c in df.columns if c in ids]))
    if serie:
        tot = serie[0]
        for s in serie[1:]:
            tot = tot.join(s, on="data", how="full", coalesce=True)
        mat = tot.fill_null(0.0).drop("data").to_numpy()
        ni = n_indipendenti(mat)
        out["n_effettivo_autovalori"], out["n_effettivo_cluster"] = _r(ni["autovalori"]), ni["cluster"]
    return out
