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
from scipy.stats import norm

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


def cpcv_selezione(matrice, date, k: int = 2, embargo_giorni: int = 5, veloce: bool | None = None) -> dict:
    """CPCV (A3): per ogni combinazione sceglie la variante col miglior Sharpe nel training e ne
    registra lo Sharpe sui k anni di test.

    I giorni di training entro `embargo_giorni` di calendario prima dell'inizio e dopo la fine di
    un blocco di test sono scartati (versione giornaliera di purga ed embargo: la durata massima di un
    trade è 5 giorni). Uscita: mediana, 10° percentile e quota positiva degli Sharpe fuori campione,
    e quante volte è stata scelta ciascuna variante.

    Con molte varianti (`veloce`, di norma da 500 colonne) le somme del training si ottengono dalle somme
    dell'intero periodo togliendo i giorni esclusi, invece di rielaborare ogni volta tutta la matrice;
    i risultati sono gli stessi (le colonne si centrano prima, così quelle costanti restano a zero).
    """
    m, d = np.asarray(matrice, dtype=float), np.asarray(date).astype("datetime64[D]")
    if veloce is None:
        veloce = m.shape[1] >= 500
    anni = _anni(d)
    emb = np.timedelta64(int(embargo_giorni), "D")
    scelte = np.zeros(m.shape[1], dtype=int)
    oos = []
    if veloce:
        mu = m.mean(axis=0)
        mc = m - mu
        tot1, tot2 = mc.sum(axis=0), np.einsum("ij,ij->j", mc, mc)
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
        if veloce:
            fuori = mc[~tr]
            n = int(tr.sum())
            s1, s2 = tot1 - fuori.sum(axis=0), tot2 - np.einsum("ij,ij->j", fuori, fuori)
            var = np.maximum(s2 - s1 ** 2 / n, 0) / (n - 1)
            with np.errstate(divide="ignore", invalid="ignore"):
                sr = np.where(var > 1e-12, (s1 / n + mu) / np.sqrt(var), -np.inf)
            best = int(np.argmax(sr))
        else:
            best = int(np.argmax(_sharpe_colonne(m[tr])))
        scelte[best] += 1
        oos.append(_sharpe_colonne(m[in_test, best][:, None])[0])
    o = np.array(oos)
    return {"n_combinazioni": len(o), "mediana": _r(np.median(o)), "p10": _r(np.percentile(o, 10)),
            "quota_positiva": _r(np.mean(o > 0)), "scelte": scelte.tolist()}


def _r(x):
    x = float(x)
    return round(x, 4) if math.isfinite(x) else None


# ---------------------------------------------------------------- PBO (CSCV)

def pbo(matrice, s: int = 16, blocco: int = 256) -> dict:
    """Probability of Backtest Overfitting con CSCV (Bailey, Borwein, López de Prado, Zhu 2017, A4).

    Il tempo è diviso in `s` blocchi contigui; per ognuna delle C(s, s/2) combinazioni la metà
    in-sample sceglie la variante con lo Sharpe migliore e si guarda il suo rango relativo
    omega = rango/(N+1) sull'altra metà; logit = ln(omega/(1-omega)); PBO = quota di logit <= 0.
    Uscita anche: mediana dei logit, `prob_perdita_oos` (quota di combinazioni dove la scelta ha Sharpe
    fuori campione negativo) e `degrado_pendenza` (pendenza della regressione dello Sharpe fuori campione
    su quello in-sample della variante scelta; 1 = nessun degrado, 0 o meno = nessun legame).

    Le combinazioni si elaborano a gruppi di `blocco` (somme dei blocchi per prodotto matriciale) e il
    rango si conta senza ordinare: la memoria resta limitata anche con decine di migliaia di varianti.
    """
    m = np.asarray(matrice, dtype=float)
    if s % 2:
        raise ValueError("s deve essere pari")
    n = m.shape[1]
    parti = np.array_split(m, s)
    cnt = np.array([len(p) for p in parti], dtype=float)
    s1 = np.array([p.sum(axis=0) for p in parti])
    s2 = np.array([(p ** 2).sum(axis=0) for p in parti])
    comb = np.array(list(combinations(range(s), s // 2)))
    ind = np.zeros((len(comb), s))
    ind[np.arange(len(comb))[:, None], comb] = 1.0

    def sharpe_gruppi(w):
        c, a, b = w @ cnt, w @ s1, w @ s2
        media = a / c[:, None]
        var = np.maximum(b / c[:, None] - media ** 2, 0) * (c / (c - 1))[:, None]
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(var > 0, media / np.sqrt(var), -np.inf)

    x, y, rango = [], [], []
    for i in range(0, len(comb), blocco):
        w = ind[i:i + blocco]
        sr_is, sr_oos = sharpe_gruppi(w), sharpe_gruppi(1.0 - w)
        best = np.argmax(sr_is, axis=1)
        righe = np.arange(len(w))
        scelto = sr_oos[righe, best]
        # rango medio (come rankdata) senza ordinare: quanti sono sotto e quanti uguali
        sotto, uguali = (sr_oos < scelto[:, None]).sum(axis=1), (sr_oos == scelto[:, None]).sum(axis=1)
        rango.append(sotto + (uguali + 1) / 2)
        x.append(sr_is[righe, best])
        y.append(scelto)
    x, y, rango = np.concatenate(x), np.concatenate(y), np.concatenate(rango)
    omega = rango / (n + 1)
    logit = np.log(omega / (1 - omega))
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

MAX_CAMPIONE_CLUSTER = 2000


def _gruppi(corr: np.ndarray, soglia_corr: float) -> np.ndarray:
    dist = np.clip(1 - corr, 0, None)
    np.fill_diagonal(dist, 0)
    return fcluster(linkage(squareform(dist, checks=False), "average"), soglia_corr, "distance")


def _cluster_grandi(z: np.ndarray, soglia_corr: float, max_campione: int, seme: int) -> int:
    """Gruppi di serie standardizzate (colonne di `z`, ddof=1) quando sono troppe per il legame medio.

    Il raggruppamento gerarchico si fa su un campione casuale (seme fisso) di `max_campione` colonne; le altre
    entrano nel gruppo del cui centroide hanno correlazione >= 1 - soglia, e quelle che non entrano in nessuno
    si raggruppano di nuovo allo stesso modo. Scalare il numero di gruppi del campione per N / campione
    sovrastimerebbe: un gruppo di serie quasi uguali compare per intero anche in un campione."""
    t, k = z.shape
    if k <= max_campione:
        return int(len(np.unique(_gruppi(z.T @ z / (t - 1), soglia_corr)))) if k > 1 else k
    rng = np.random.default_rng(seme)
    scelte = np.zeros(k, dtype=bool)
    scelte[rng.choice(k, max_campione, replace=False)] = True
    zs = z[:, scelte]
    et = _gruppi(zs.T @ zs / (t - 1), soglia_corr)
    etichette = np.unique(et)
    cen = np.column_stack([zs[:, et == e].mean(axis=1) for e in etichette])
    cen = (cen - cen.mean(axis=0)) / cen.std(axis=0, ddof=1)
    resto = z[:, ~scelte]
    migliore = (resto.T @ cen / (t - 1)).max(axis=1)
    fuori = resto[:, migliore < 1 - soglia_corr]
    return int(len(etichette)) + (_cluster_grandi(fuori, soglia_corr, max_campione, seme + 1) if fuori.shape[1] else 0)


def n_indipendenti(matrice, soglia_corr: float = 0.5, max_campione: int = MAX_CAMPIONE_CLUSTER, seme: int = 0) -> dict:
    """Numero effettivo di prove (Bailey et al. 2014 suggeriscono PCA o clustering, A5).

    `autovalori` = (somma l)^2 / somma l^2 sugli autovalori della matrice di correlazione;
    `cluster` = numero di gruppi con legame medio e distanza 1 - correlazione <= `soglia_corr`.
    Le colonne costanti si escludono.

    Con più colonne che giorni gli autovalori non nulli sono quelli della matrice giorni x giorni
    (stessi della SVD della matrice standardizzata), senza costruire la correlazione N x N. Con più di
    `max_campione` colonne il raggruppamento usa un campione con seme fisso (vedi `_cluster_grandi`);
    il risultato dice quando è successo (`campione`, il numero di colonne del campione, altrimenti None).
    """
    m = np.asarray(matrice, dtype=float)
    m = m[:, m.std(axis=0) > 0]
    t, k = m.shape
    if k < 2:
        return {"autovalori": float(k), "cluster": k, "campione": None}
    z = (m - m.mean(axis=0)) / m.std(axis=0, ddof=1)
    if k <= t:
        lam = np.clip(np.linalg.eigvalsh(z.T @ z / (t - 1)), 0, None)
    else:
        lam = np.clip(np.linalg.eigvalsh(z @ z.T / (t - 1)), 0, None)
    out = {"autovalori": float(lam.sum() ** 2 / np.sum(lam ** 2)),
           "cluster": _cluster_grandi(z, soglia_corr, max_campione, seme),
           "campione": max_campione if k > max_campione else None}
    return out


# ---------------------------------------------------------------- registro dei tentativi

def _nome_file(famiglia: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", famiglia)


def _righe() -> list[dict]:
    f = CARTELLA / "tentativi.jsonl"
    if not f.exists():
        return []
    return [json.loads(r) for r in f.read_text(encoding="utf-8").splitlines() if r.strip()]


def _scrivi_righe(righe: list[dict]) -> None:
    tmp = CARTELLA / "tentativi.jsonl.tmp"
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in righe), encoding="utf-8")
    tmp.replace(CARTELLA / "tentativi.jsonl")


def registra_molti(esperimento: str, famiglia: str, prodotto: str, prove: list, date) -> list[str]:
    """Registra molti tentativi della stessa famiglia e dello stesso prodotto con una sola scrittura per file.

    `prove` è la lista di (parametri, serie giornaliera); `date` le date comuni. Aggiunge le righe a
    `tentativi.jsonl` e le colonne a `curve/<famiglia>.parquet` (una colonna per tentativo, righe = date,
    zero dove il tentativo non ha il giorno). Restituisce gli id, nell'ordine delle prove."""
    CARTELLA.mkdir(parents=True, exist_ok=True)
    (CARTELLA / "curve").mkdir(exist_ok=True)
    d = np.asarray(date).astype("datetime64[D]")
    prima = len(_righe())
    ids = [f"t{prima + i + 1:06d}" for i in range(len(prove))]
    quando = datetime.now(timezone.utc).isoformat(timespec="seconds")
    mat = np.column_stack([np.asarray(g, dtype=float) for _, g in prove]) if prove else np.zeros((len(d), 0))
    righe = [{"id": i, "quando": quando, "esperimento": esperimento, "famiglia": famiglia, "prodotto": prodotto,
              "parametri": par, "sharpe": _r(metriche.sharpe(mat[:, j])), "giorni": int(len(d))}
             for j, (i, (par, _)) in enumerate(zip(ids, prove))]
    with open(CARTELLA / "tentativi.jsonl", "a", encoding="utf-8") as f:
        f.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in righe))
    nuova = pl.from_numpy(mat, schema=ids, orient="row").with_columns(
        pl.Series("data", d).cast(pl.Date)).select("data", *ids)
    pq = CARTELLA / "curve" / f"{_nome_file(famiglia)}.parquet"
    if pq.exists():
        nuova = pl.read_parquet(pq).join(nuova, on="data", how="full", coalesce=True).sort("data")
    nuova.write_parquet(pq)
    return ids


def registra(esperimento: str, famiglia: str, prodotto: str, parametri: dict, giorn, date) -> str:
    """Un solo tentativo (vedi `registra_molti`). Restituisce l'id."""
    return registra_molti(esperimento, famiglia, prodotto, [(parametri, giorn)], date)[0]


def holdout_usato(id_: str) -> dict | None:
    """Il segno lasciato da `segna_holdout` sul tentativo (None se la prova finale non è stata fatta)."""
    for r in _righe():
        if r["id"] == id_:
            return r.get("holdout_usato")
    return None


def segna_holdout(id_: str, info: dict) -> None:
    """Segna che il tentativo ha consumato la prova finale (campo `holdout_usato`). Una volta sola."""
    righe = _righe()
    trovato = [r for r in righe if r["id"] == id_]
    if not trovato:
        raise KeyError(id_)
    if trovato[0].get("holdout_usato"):
        raise ValueError(f"{id_}: prova finale già usata")
    trovato[0]["holdout_usato"] = info
    _scrivi_righe(righe)


def conteggio(famiglia: str | None = None) -> dict:
    """Numero di prove, numero effettivo, varianza degli Sharpe: ingressi di DSR e MinBTL.

    Il numero effettivo si calcola sulle serie giornaliere dei tentativi (giorni mancanti = 0), in due
    versioni (`n_effettivo_autovalori`, `n_effettivo_cluster`, vedi `n_indipendenti`).
    `var_sharpe` è la varianza (ddof=1) degli Sharpe annualizzati dei tentativi; None con meno di due.
    """
    righe = [r for r in _righe() if famiglia is None or r["famiglia"] == famiglia]
    out = {"famiglia": famiglia, "n_prove": len(righe), "famiglie": sorted({r["famiglia"] for r in righe}),
           "n_effettivo_autovalori": None, "n_effettivo_cluster": None, "campione_cluster": None,
           "var_sharpe": None}
    if not righe:
        return out
    sr = [r["sharpe"] for r in righe if r["sharpe"] is not None]
    out["var_sharpe"] = _r(np.var(sr, ddof=1)) if len(sr) > 1 else None
    ids = {r["id"] for r in righe}
    serie = []
    for fam in out["famiglie"]:
        pq = CARTELLA / "curve" / f"{_nome_file(fam)}.parquet"
        if pq.exists():
            colonne = [c for c in pl.read_parquet_schema(pq) if c in ids]
            serie.append(pl.read_parquet(pq, columns=["data", *colonne]))
    if serie:
        tot = serie[0]
        for s in serie[1:]:
            tot = tot.join(s, on="data", how="full", coalesce=True)
        mat = tot.fill_null(0.0).drop("data").to_numpy()
        ni = n_indipendenti(mat)
        out["n_effettivo_autovalori"], out["n_effettivo_cluster"] = _r(ni["autovalori"]), ni["cluster"]
        out["campione_cluster"] = ni.get("campione")
    return out
