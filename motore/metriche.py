"""Metriche di affidabilità e regolarità. Formule e fonti: `fonti/paper/validazione-e-metriche.md`, parte B.

Convenzioni
- `giorn`: profitti giornalieri in punti (o escursioni medie), zeri inclusi; `date`: datetime64[D].
- Le funzioni non convertono mai in % del prezzo e non leggono dati.
- Le uscite dei riassunti sono numeri o dict serializzabili in JSON (4 cifre, None al posto di NaN).
- Annualizzazione con 252 giorni. Generatori casuali con `seed` esplicito.
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit
from scipy.stats import norm

GIORNI_ANNO = 252
EULERO = 0.5772156649015329


# ---------------------------------------------------------------- utilità

def _num(x, cifre=4):
    """Float arrotondato, None se non finito."""
    x = float(x)
    return round(x, cifre) if math.isfinite(x) else None


def pulisci(o):
    """Converte ricorsivamente tipi numpy in tipi JSON; NaN e infiniti diventano None."""
    if isinstance(o, dict):
        return {str(k): pulisci(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [pulisci(v) for v in o]
    if isinstance(o, np.ndarray):
        return pulisci(o.tolist())
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return _num(o)
    return o


def _arr(x) -> np.ndarray:
    return np.asarray(x, dtype=float)


# ---------------------------------------------------------------- Sharpe

def sharpe(giorn) -> float:
    """Sharpe annualizzato (media/dev. standard dei giorni, zeri inclusi, per radice di 252)."""
    g = _arr(giorn)
    s = g.std(ddof=1)
    return float("nan") if s == 0 else float(g.mean() / s * math.sqrt(GIORNI_ANNO))


def _autocorr(g: np.ndarray, kmax: int) -> np.ndarray:
    gc = g - g.mean()
    v = gc @ gc
    return np.array([(gc[k:] @ gc[:-k]) / v for k in range(1, kmax + 1)])


def sharpe_lo(giorn, q: int | None = None, aggrega: int = GIORNI_ANNO) -> float:
    """Sharpe annuo corretto per autocorrelazione (Lo 2002, parte B2 delle fonti).

    SR(aggrega) = eta * SR_giornaliero, eta = aggrega / sqrt(aggrega + 2 * somma_k (aggrega-k) rho_k).
    Le rho_k si stimano fino al ritardo `q` (default floor(252^(1/3)) = 6, perché con 251 ritardi
    la stima è rumore) e si pongono a zero oltre: con q=0 si ottiene lo Sharpe semplice.
    """
    g = _arr(giorn)
    q = int(GIORNI_ANNO ** (1 / 3)) if q is None else q
    s = g.std(ddof=1)
    if s == 0:
        return float("nan")
    q = min(q, aggrega - 1, len(g) - 2)
    rho = _autocorr(g, q) if q > 0 else np.array([])
    k = np.arange(1, len(rho) + 1)
    den = aggrega + 2 * float(np.sum((aggrega - k) * rho))
    if den <= 0:
        return float("nan")
    return float(aggrega / math.sqrt(den) * g.mean() / s)


# ---------------------------------------------------------------- PSR, DSR, MinBTL

def psr(giorn, sr_rif: float = 0.0) -> float:
    """Probabilistic Sharpe Ratio (Bailey, López de Prado 2012, A6).

    `sr_rif` annualizzato; internamente si usa lo Sharpe giornaliero con asimmetria e curtosi
    (non in eccesso) dei giorni. Probabilità che lo Sharpe vero superi `sr_rif`.
    """
    g = _arr(giorn)
    t = len(g)
    s = g.std(ddof=1)
    if t < 3 or s == 0:
        return float("nan")
    sr = g.mean() / s
    z = (g - g.mean()) / g.std(ddof=0)
    g3 = float(np.mean(z ** 3))
    g4 = float(np.mean(z ** 4))
    rif = sr_rif / math.sqrt(GIORNI_ANNO)
    den = 1 - g3 * sr + (g4 - 1) / 4 * sr ** 2
    if den <= 0:
        return float("nan")
    return float(norm.cdf((sr - rif) * math.sqrt(t - 1) / math.sqrt(den)))


def sr_atteso_massimo(n_prove: float, var_sr_prove: float) -> float:
    """Sharpe massimo atteso da `n_prove` prove senza vantaggio (Bailey, López de Prado 2014, A6).

    `var_sr_prove` è la varianza degli Sharpe annualizzati delle prove; il risultato è annualizzato.
    Con una prova sola vale 0.
    """
    if n_prove <= 1:
        return 0.0
    n = float(n_prove)
    return math.sqrt(var_sr_prove) * ((1 - EULERO) * norm.ppf(1 - 1 / n)
                                      + EULERO * norm.ppf(1 - 1 / (n * math.e)))


def dsr(giorn, n_prove: float, var_sr_prove: float) -> float:
    """Deflated Sharpe Ratio: PSR contro lo Sharpe massimo atteso dal caso (soglia usuale 0,95)."""
    return psr(giorn, sr_atteso_massimo(n_prove, var_sr_prove))


def min_btl(n_prove: float, sr_annuo: float) -> float:
    """Anni minimi di dati perché `n_prove` prove non producano da sole uno Sharpe `sr_annuo`.

    Limite di Bailey et al. 2014 (A5): MinBTL < 2 ln N / SR^2, con SR lo Sharpe in-sample cercato.
    """
    return 2 * math.log(n_prove) / sr_annuo ** 2


def prove_ammesse(anni: float, sr_annuo: float) -> float:
    """Inversa di `min_btl`: N massimo = exp(anni * SR^2 / 2)."""
    return math.exp(anni * sr_annuo ** 2 / 2)


# ---------------------------------------------------------------- regolarità della curva

def curva(giorn) -> np.ndarray:
    return np.cumsum(_arr(giorn))


def _regressione(y: np.ndarray):
    """Pendenza, errore standard della pendenza e R^2 della regressione di y sul tempo."""
    n = len(y)
    t = np.arange(n, dtype=float)
    tc = t - t.mean()
    sxx = tc @ tc
    b = (tc @ (y - y.mean())) / sxx
    res = y - y.mean() - b * tc
    sse = res @ res
    sst = (y - y.mean()) @ (y - y.mean())
    se = math.sqrt(sse / (n - 2) / sxx) if n > 2 else float("nan")
    r2 = 1 - sse / sst if sst > 0 else float("nan")
    return b, se, r2


def r2(giorn) -> float:
    """R^2 della regressione lineare della curva (somma cumulata) sul tempo."""
    return float(_regressione(curva(giorn))[2])


def k_ratio(giorn) -> float:
    """K-ratio di Kestner 2003: pendenza / (errore standard della pendenza * radice di n).

    La regressione è sulla curva cumulata in punti (profitto fisso per trade), non su ln(VAMI):
    le fonti divergono sulle versioni del 2003 e del 2013, qui si usa quella del 2003.
    """
    b, se, _ = _regressione(curva(giorn))
    n = len(giorn)
    return float(b / (se * math.sqrt(n))) if se and se > 0 else float("nan")


def pendenze_annue(giorn, date) -> dict:
    """Pendenza della curva (punti per anno di 252 giorni) in ogni anno di calendario (B1).

    Uscita: pendenze per anno, coefficiente di variazione sd/media (None se la media non è positiva)
    e quota di anni con pendenza positiva.
    """
    g, anni = _arr(giorn), np.asarray(date).astype("datetime64[Y]").astype(int) + 1970
    pend = {}
    for a in np.unique(anni):
        y = np.cumsum(g[anni == a])
        pend[int(a)] = float(_regressione(y)[0] * GIORNI_ANNO) if len(y) > 2 else float("nan")
    v = np.array([x for x in pend.values() if math.isfinite(x)])
    media = v.mean() if len(v) else float("nan")
    cv = float(v.std(ddof=1) / media) if len(v) > 1 and media > 0 else None
    return {"pendenze": pend, "cv": cv, "quota_positivi": float(np.mean(v > 0)) if len(v) else None}


def _dd_serie(g: np.ndarray) -> np.ndarray:
    """Drawdown in punti (valori <= 0) della curva cumulata, con il massimo iniziale a zero."""
    c = np.cumsum(g)
    return c - np.maximum.accumulate(np.maximum(c, 0.0))


def ulcer(giorn) -> float:
    """Ulcer Index (Martin, McCann 1989) sul drawdown in punti: radice della media dei quadrati."""
    d = _dd_serie(_arr(giorn))
    return float(np.sqrt(np.mean(d ** 2)))


def drawdown(giorn) -> dict:
    """Massimo drawdown (positivo, in punti), durata massima in giorni e quota di giorni sott'acqua."""
    d = _dd_serie(_arr(giorn))
    sotto = d < 0
    durata = corsa = 0
    for s in sotto:
        corsa = corsa + 1 if s else 0
        durata = max(durata, corsa)
    return {"massimo": float(-d.min()), "durata_max": int(durata), "quota_sott_acqua": float(sotto.mean())}


def trimestri_positivi(giorn, date) -> float:
    """Quota di trimestri di calendario con profitto positivo."""
    mesi = np.asarray(date).astype("datetime64[M]").astype(int)
    _, inv = np.unique(mesi // 3, return_inverse=True)
    somme = np.bincount(inv, weights=_arr(giorn))
    return float(np.mean(somme > 0))


def sharpe_mobile(giorn, finestra: int = GIORNI_ANNO, passo: int = 21) -> dict | None:
    """Sharpe annualizzato su finestre mobili (B1): minimo, mediana, quota positiva."""
    g = _arr(giorn)
    if len(g) < finestra:
        return None
    w = np.lib.stride_tricks.sliding_window_view(g, finestra)[::passo]
    s = w.std(axis=1, ddof=1)
    ok = s > 0
    sr = w.mean(axis=1)[ok] / s[ok] * math.sqrt(GIORNI_ANNO)
    if not len(sr):
        return None
    return {"minimo": float(sr.min()), "mediana": float(np.median(sr)),
            "quota_positiva": float(np.mean(sr > 0)), "n_finestre": int(len(sr))}


# ---------------------------------------------------------------- robustezza e sequenze

def senza_migliori(trade, k: int = 10) -> float:
    """Profitto totale togliendo i `k` trade migliori."""
    t = np.sort(_arr(trade))
    return float(t[:-k].sum()) if k > 0 else float(t.sum())


def simmetria(giorn_long, giorn_short) -> dict:
    """Sharpe dei due lati della stessa regola specchiata e rapporto min/max (B5).

    Il rapporto è negativo se i segni sono discordi; `concordi` dice se entrambi sono positivi
    o entrambi negativi.
    """
    a, b = sharpe(giorn_long), sharpe(giorn_short)
    mx = max(a, b)
    return {"sharpe_long": a, "sharpe_short": b, "rapporto": min(a, b) / mx if mx > 0 else None,
            "concordi": bool(a * b > 0)}


def z_wald_wolfowitz(trade) -> dict:
    """Test delle sequenze di Wald e Wolfowitz (1940) su vincenti (>0) e perdenti (B3).

    Sotto indipendenza E[R] = 2WL/N + 1, Var[R] = 2WL(2WL-N)/(N^2 (N-1)). Segno standard:
    z negativo = poche sequenze (vincenti e perdenti raggruppati), z positivo = alternanza.
    Il segno è l'opposto di quello descritto per ProRealTime.
    """
    esito = _arr(trade) > 0
    n = len(esito)
    w = int(esito.sum())
    l = n - w
    if w == 0 or l == 0 or n < 3:
        return {"n": n, "vincenti": w, "perdenti": l, "sequenze": None, "attese": None, "z": None,
                "significato": "non calcolabile: serve almeno un vincente e un perdente"}
    r = 1 + int(np.sum(esito[1:] != esito[:-1]))
    attese = 2 * w * l / n + 1
    var = 2 * w * l * (2 * w * l - n) / (n ** 2 * (n - 1))
    z = (r - attese) / math.sqrt(var) if var > 0 else float("nan")
    if not math.isfinite(z) or abs(z) < 1.96:
        sig = "compatibile col caso (|z| < 1,96)"
    elif z < 0:
        sig = "z negativo: vincenti e perdenti raggruppati (poche sequenze)"
    else:
        sig = "z positivo: vincenti e perdenti alternati (troppe sequenze)"
    return {"n": n, "vincenti": w, "perdenti": l, "sequenze": r, "attese": attese, "z": z, "significato": sig}


# ---------------------------------------------------------------- bootstrap stazionario e Monte Carlo

def lunghezza_blocco(x) -> float:
    """Lunghezza media ottima del blocco per il bootstrap stazionario.

    Politis, White (2004) con la correzione di Patton, Politis, White (2009): finestra a trapezio
    piatto, M = 2 m con m primo ritardo oltre il quale Kn autocorrelazioni consecutive sono
    non significative, b = (g^2 / g0^2)^(1/3) n^(1/3) con g = somma lam(k/M) |k| R(k) e
    g0 = somma lam(k/M) R(k). Limitata tra 1 e min(3 sqrt(n), n/3).
    """
    x = _arr(x)
    n = len(x)
    if n < 30 or x.std() == 0:
        return 1.0
    xc = x - x.mean()
    kn = max(5, int(math.log10(n)))
    mmax = int(math.ceil(math.sqrt(n))) + kn
    bmax = math.ceil(min(3 * math.sqrt(n), n / 3))
    acv = np.array([xc[k:] @ xc[:n - k] / n for k in range(mmax + 1)])
    soglia = 2 * math.sqrt(math.log10(n) / n)
    rho = np.abs(acv[1:] / acv[0])
    m = mmax - kn
    for j in range(mmax - kn + 1):
        if np.all(rho[j:j + kn] < soglia):
            m = j
            break
    big_m = min(2 * max(m, 1), mmax)
    k = np.arange(1, big_m + 1)
    s = k / big_m
    lam = np.where(s <= 0.5, 1.0, 2 * (1 - s))
    g = 2 * float(np.sum(lam * k * acv[1:big_m + 1]))
    g0 = acv[0] + 2 * float(np.sum(lam * acv[1:big_m + 1]))
    if g0 <= 0:
        return 1.0
    b = (abs(g) / g0) ** (2 / 3) * n ** (1 / 3)
    return float(min(max(b, 1.0), bmax))


@njit(cache=True)
def _stat_percorso(buf):
    cum = 0.0
    picco = 0.0
    dd = 0.0
    serie = 0
    peggio = 0
    for v in buf:
        cum += v
        if cum > picco:
            picco = cum
        if picco - cum > dd:
            dd = picco - cum
        if v < 0:
            serie += 1
            if serie > peggio:
                peggio = serie
        elif v > 0:
            serie = 0
    return dd, peggio, cum


@njit(cache=True)
def _mc_blocchi(x, n, p, seed):
    """Bootstrap stazionario (Politis, Romano 1994): n percorsi lunghi quanto x, blocchi di media 1/p."""
    np.random.seed(seed)
    t_tot = len(x)
    out = np.empty((n, 3))
    buf = np.empty(t_tot)
    for i in range(n):
        idx = np.random.randint(0, t_tot)
        for t in range(t_tot):
            if t > 0:
                if np.random.random() < p:
                    idx = np.random.randint(0, t_tot)
                else:
                    idx = (idx + 1) % t_tot
            buf[t] = x[idx]
        out[i, 0], out[i, 1], out[i, 2] = _stat_percorso(buf)
    return out


@njit(cache=True)
def _mc_rimescolato(x, n, seed):
    np.random.seed(seed)
    out = np.empty((n, 3))
    for i in range(n):
        out[i, 0], out[i, 1], out[i, 2] = _stat_percorso(np.random.permutation(x))
    return out


@njit(cache=True)
def _mc_regimi(x, lab, n_reg, n, p, seed):
    """Come _mc_blocchi, ma il regime di ogni giorno è quello storico e i giorni si pescano
    a blocchi dentro il pool dei giorni dello stesso regime."""
    np.random.seed(seed)
    t_tot = len(x)
    conta = np.zeros(n_reg, dtype=np.int64)
    for t in range(t_tot):
        conta[lab[t]] += 1
    inizio = np.zeros(n_reg + 1, dtype=np.int64)
    for r in range(n_reg):
        inizio[r + 1] = inizio[r] + conta[r]
    pool = np.empty(t_tot, dtype=np.int64)
    riemp = np.zeros(n_reg, dtype=np.int64)
    for t in range(t_tot):
        r = lab[t]
        pool[inizio[r] + riemp[r]] = t
        riemp[r] += 1
    out = np.empty((n, 3))
    buf = np.empty(t_tot)
    pos = np.zeros(n_reg, dtype=np.int64)
    for i in range(n):
        nuovo = np.ones(n_reg, dtype=np.bool_)
        for t in range(t_tot):
            r = lab[t]
            if nuovo[r] or np.random.random() < p:
                pos[r] = np.random.randint(0, conta[r])
                nuovo[r] = False
            else:
                pos[r] = (pos[r] + 1) % conta[r]
            buf[t] = x[pool[inizio[r] + pos[r]]]
        out[i, 0], out[i, 1], out[i, 2] = _stat_percorso(buf)
    return out


@njit(cache=True)
def medie_bootstrap(x, n, p, seed):
    """Medie per colonna di n ricampionamenti con bootstrap stazionario di x (T x N); serve a SPA e
    Romano-Wolf. Le righe sono ricampionate insieme, per tenere la dipendenza fra varianti."""
    np.random.seed(seed)
    t_tot, k = x.shape
    out = np.zeros((n, k))
    for i in range(n):
        idx = np.random.randint(0, t_tot)
        for t in range(t_tot):
            if t > 0:
                if np.random.random() < p:
                    idx = np.random.randint(0, t_tot)
                else:
                    idx = (idx + 1) % t_tot
            for j in range(k):
                out[i, j] += x[idx, j]
        for j in range(k):
            out[i, j] /= t_tot
    return out


def _percentili(v: np.ndarray) -> dict:
    p5, p50, p95 = np.percentile(v, [5, 50, 95])
    return {"p5": _num(p5), "p50": _num(p50), "p95": _num(p95)}


def _riassunto(stat: np.ndarray) -> dict:
    return {"drawdown": _percentili(stat[:, 0]), "serie_perdite": _percentili(stat[:, 1]),
            "profitto": _percentili(stat[:, 2])}


def montecarlo(giorn, trade=None, regimi=None, n: int = 5000, seed: int = 0) -> dict:
    """Monte Carlo del drawdown, della serie di perdite e del profitto finale (B4).

    Metodi: `blocchi` (bootstrap stazionario dei giorni), `regimi` (solo se date le etichette),
    `rimescolato_giorni` (permutazione dei giorni) e, se c'è `trade`, `rimescolato_trade`
    (serie di perdite in trade). Il drawdown è positivo, in punti; la serie di perdite
    conta i giorni (o trade) negativi consecutivi, saltando gli zeri.

    La lunghezza media del blocco è il massimo fra Politis-White sui giorni e sui loro valori
    assoluti: i giorni con volatilità a grappoli hanno rendimenti non correlati ma valori assoluti
    molto correlati, e solo il secondo la rivela.
    `rapporto_dd` = drawdown mediano a blocchi / drawdown mediano rimescolato (giorni);
    con `regimi` anche `rapporto_dd_regimi`.
    """
    g = _arr(giorn)
    b_ret, b_abs = lunghezza_blocco(g), lunghezza_blocco(np.abs(g))
    b = max(b_ret, b_abs)
    p = 1.0 / b
    out = {"lungh_blocco": _num(b),
           "lungh_blocco_origine": "Politis-White (correzione di Patton et al. 2009): massimo fra "
                                   f"rendimenti ({_num(b_ret)}) e valori assoluti ({_num(b_abs)})"}
    st_bl = _mc_blocchi(g, n, p, seed)
    st_rim = _mc_rimescolato(g, n, seed + 1)
    out["blocchi"] = _riassunto(st_bl)
    out["rimescolato_giorni"] = _riassunto(st_rim)
    dd_rim = float(np.median(st_rim[:, 0]))
    out["rapporto_dd"] = _num(np.median(st_bl[:, 0]) / dd_rim) if dd_rim > 0 else None
    if trade is not None:
        out["rimescolato_trade"] = _riassunto(_mc_rimescolato(_arr(trade), n, seed + 2))
    if regimi is not None:
        _, lab = np.unique(np.asarray(regimi), return_inverse=True)
        lab = lab.astype(np.int64)
        st_reg = _mc_regimi(g, lab, int(lab.max()) + 1, n, p, seed + 3)
        out["regimi"] = _riassunto(st_reg)
        out["rapporto_dd_regimi"] = _num(np.median(st_reg[:, 0]) / dd_rim) if dd_rim > 0 else None
    return out


# ---------------------------------------------------------------- portafoglio

def correlazioni(matrice) -> dict:
    """Correlazione di Pearson fra colonne e correlazione di coda (B6).

    Coda: correlazione della coppia sui giorni in cui almeno uno dei due è sotto il proprio
    10° percentile (None con meno di 3 giorni).
    """
    m = _arr(matrice)
    k = m.shape[1]
    q = np.percentile(m, 10, axis=0)
    coda = np.full((k, k), np.nan)
    for i in range(k):
        for j in range(k):
            sel = (m[:, i] < q[i]) | (m[:, j] < q[j])
            if sel.sum() >= 3 and m[sel, i].std() > 0 and m[sel, j].std() > 0:
                coda[i, j] = np.corrcoef(m[sel, i], m[sel, j])[0, 1]
    return {"normale": np.corrcoef(m, rowvar=False).reshape(k, k), "coda": coda}


def sovrapposizione_dd(a, b) -> dict:
    """Quota di giorni sott'acqua insieme / (quota di a * quota di b): 1 se indipendenti (B6)."""
    sa, sb = _dd_serie(_arr(a)) < 0, _dd_serie(_arr(b)) < 0
    qa, qb, qab = sa.mean(), sb.mean(), (sa & sb).mean()
    return {"quota_a": float(qa), "quota_b": float(qb), "quota_insieme": float(qab),
            "rapporto": float(qab / (qa * qb)) if qa * qb > 0 else None}


def cdar(giorn, alfa: float = 0.95) -> float:
    """Conditional Drawdown at Risk (Chekhlov, Uryasev, Zabarankin 2005): media dei drawdown giornalieri
    (positivi, in punti) nella coda peggiore di probabilità 1-alfa."""
    d = -_dd_serie(_arr(giorn))
    soglia = np.quantile(d, alfa)
    return float(d[d >= soglia].mean())


def contributo_cdar(matrice, pesi, i: int, alfa: float = 0.95) -> float:
    """CDaR del portafoglio con il sistema `i` meno CDaR dello stesso portafoglio senza di lui
    (peso azzerato, gli altri invariati). Positivo = il sistema aumenta il rischio di drawdown."""
    m, w = _arr(matrice), _arr(pesi).copy()
    con = cdar(m @ w, alfa)
    w[i] = 0.0
    return float(con - cdar(m @ w, alfa))


def enb(matrice) -> float:
    """Effective number of bets (Meucci 2009) sulle componenti principali della matrice di correlazione:
    exp(-somma p ln p), p = quota di varianza di ogni componente. Colonne costanti escluse."""
    m = _arr(matrice)
    m = m[:, m.std(axis=0) > 0]
    if m.shape[1] < 2:
        return float(m.shape[1])
    lam = np.clip(np.linalg.eigvalsh(np.corrcoef(m, rowvar=False)), 0, None)
    p = lam / lam.sum()
    p = p[p > 0]
    return float(np.exp(-np.sum(p * np.log(p))))


# ---------------------------------------------------------------- scheda

def scheda(giorn, date, trade=None, *, n_prove=None, var_sr_prove=None, cpcv=None, pbo=None,
           giorn_long=None, giorn_short=None, regimi=None, matrice_portafoglio=None, pesi=None,
           n_mc: int = 2000, seed: int = 0) -> dict:
    """Scheda compatta di un candidato (blocchi di `ricerca/progetto-software.md`).

    Calcolati qui: 1 Sharpe (DSR solo con `n_prove` e `var_sr_prove`), 3 regolarità, 4 robustezza
    (senza i 10 migliori, simmetria se ci sono i due lati), 5 Wald-Wolfowitz e 6 Monte Carlo.
    Entrano se passati: 2 `cpcv` e `pbo` (uscite di motore.validazione), 7 portafoglio
    (`matrice_portafoglio` T x N dei sistemi in produzione, `pesi` di tutti i sistemi più il candidato,
    ultimo). Il resto è None.
    """
    g = _arr(giorn)
    sr = sharpe(g)
    blocco1 = {"sharpe": sr, "sharpe_lo": sharpe_lo(g), "psr_0": psr(g, 0.0),
               "dsr": dsr(g, n_prove, var_sr_prove) if n_prove is not None and var_sr_prove is not None else None,
               "giorni": len(g)}
    pend = pendenze_annue(g, date)
    blocco3 = {"r2": r2(g), "k_ratio": k_ratio(g), "cv_pendenze": pend["cv"],
               "quota_anni_positivi": pend["quota_positivi"], "ulcer": ulcer(g), **drawdown(g),
               "trimestri_positivi": trimestri_positivi(g, date), "sharpe_mobile": sharpe_mobile(g)}
    blocco4 = {"profitto_senza_10_migliori": senza_migliori(trade, 10) if trade is not None else None,
               "profitto": float(np.sum(trade)) if trade is not None else float(g.sum()),
               "simmetria": simmetria(giorn_long, giorn_short) if giorn_long is not None and giorn_short is not None else None}
    blocco7 = None
    if matrice_portafoglio is not None:
        m = _arr(matrice_portafoglio)
        tutti = np.column_stack([m, g])
        w = np.ones(tutti.shape[1]) if pesi is None else _arr(pesi)
        c = correlazioni(tutti)
        blocco7 = {"correlazione": c["normale"][-1, :-1], "correlazione_coda": c["coda"][-1, :-1],
                   "sovrapposizione_dd": [sovrapposizione_dd(g, m[:, j])["rapporto"] for j in range(m.shape[1])],
                   "contributo_cdar": contributo_cdar(tutti, w, tutti.shape[1] - 1),
                   "enb_senza": enb(m), "enb_con": enb(tutti)}
    return pulisci({"1_sharpe": blocco1, "2_cpcv": cpcv, "2_pbo": pbo, "3_regolarita": blocco3,
                    "4_robustezza": blocco4, "5_z_wald_wolfowitz": z_wald_wolfowitz(trade) if trade is not None else None,
                    "6_montecarlo": montecarlo(g, trade, regimi, n_mc, seed), "7_portafoglio": blocco7})
