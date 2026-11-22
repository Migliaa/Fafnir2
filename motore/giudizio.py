"""Giudizio calcolato di un candidato (cruscotto, `ricerca/spec-cruscotto.md`, A2).

Deterministico e uguale per tutti. L'esito è `candidato` o `scartato`, senza vie di mezzo, e dipende da tre
cose in quest'ordine: i filtri di Andrea (guadagno medio per trade in euro secondo la durata, trade l'anno,
R², anni positivi), il cancello statistico (DSR e PBO) e la prova finale fuori campione. Le soglie sono le
costanti in cima al file. I sei gruppi colorati (caso, costi, regolarità, robustezza, rischio, portafoglio)
restano come dettaglio e non decidono.
"""
from __future__ import annotations

import math

import numpy as np

# ---- filtri di Andrea (1 CFD IG, al netto di spread e costo notturno): chi non li passa è scartato
SOGLIE_GUADAGNO = ((36.0, 20.0), (72.0, 30.0), (float("inf"), 50.0))   # (ore medie del trade fino a, € minimi a trade)
TRADE_ANNO_MIN = 12.0            # trade l'anno in media, circa uno al mese
R2_MIN = 0.85                    # R² della curva netta
ANNI_POSITIVI_MIN = 0.70         # quota di anni chiusi in utile
FUORI_CAMPIONE_QUOTA_MIN = 0.5   # prova finale: guadagno medio >= questa quota di quello in-sample (e utile positivo)
# ---- cancello statistico
DSR_MIN = 0.95                   # sul numero effettivo di prove dell'esperimento
PBO_MAX, PBO_MIN_COMBINAZIONI = 0.2, 4   # PBO della famiglia, solo se ha almeno 4 combinazioni
RAPPORTO_COSTI_INDICATIVO = 3.0  # lordo / costi: riferimento mostrato nella scheda, non scarta

# ---- soglie dei sei gruppi di dettaglio (non decidono l'esito)
DSR_VERDE, DSR_GIALLO = 0.95, 0.8
PBO_VERDE, PBO_GIALLO = 0.2, 0.5
CPCV_P10_VERDE = 0.0
RAPPORTO_COSTI_VERDE, RAPPORTO_COSTI_GIALLO = 3.0, 2.0
R2_VERDE = 0.8
QUOTA_ANNI_VERDE = 0.7
QUOTA_FINESTRE_VERDE = 0.7
ZONA_STABILE_VERDE = 0.7
RAPPORTO_DD_VERDE, RAPPORTO_DD_GIALLO = 1.3, 1.6
Z_WW_MAX = 1.96

GRUPPI = [("caso", "Caso o vantaggio", False), ("costi", "Costi e fattibilità", False),
          ("regolarita", "Regolarità", False), ("robustezza", "Robustezza", False),
          ("rischio", "Rischio", False), ("portafoglio", "Portafoglio", False)]


def _get(d, *chiavi):
    for k in chiavi:
        if not isinstance(d, dict) or d.get(k) is None:
            return None
        d = d[k]
    return d


def _voce(nome, valore, soglia, esito, spiegazione):
    return {"nome": nome, "valore": valore, "soglia": soglia, "esito": esito, "spiegazione": spiegazione}


def _e(ok):
    """Esito di una voce: grigio se il dato manca (ok None)."""
    return "grigio" if ok is None else ("verde" if ok else "rosso")


def _gruppo(esito, voci):
    return {"esito": esito, "voci": voci}


# ---------------------------------------------------------------- i sei gruppi

def _caso(scheda, rob):
    dsr, pbo = _get(scheda, "1_sharpe", "dsr"), _get(scheda, "2_pbo", "pbo")
    p10 = _get(scheda, "2_cpcv", "p10")
    voci = [
        _voce("DSR", dsr, f">= {DSR_VERDE} (giallo >= {DSR_GIALLO})",
              "grigio" if dsr is None else "verde" if dsr >= DSR_VERDE else "giallo" if dsr >= DSR_GIALLO else "rosso",
              "Probabilità che lo Sharpe resti positivo dopo aver tenuto conto di tutte le prove fatte."),
        _voce("PBO", pbo, f"< {PBO_VERDE} (giallo < {PBO_GIALLO})",
              "grigio" if pbo is None else "verde" if pbo < PBO_VERDE else "giallo" if pbo < PBO_GIALLO else "rosso",
              "Probabilità che la variante scelta in campione sia sotto la mediana fuori campione."),
        _voce("10° percentile CPCV", p10, f"> {CPCV_P10_VERDE}", _e(None if p10 is None else p10 > CPCV_P10_VERDE),
              "Sharpe del decimo peggiore fra le combinazioni di anni di prova e di test."),
        _voce("Sharpe corretto per l'autocorrelazione", _get(scheda, "1_sharpe", "sharpe_lo"), "informativa",
              "info", "Sharpe annuo con la correzione di Lo per la correlazione fra giorni."),
        _voce("PSR", _get(scheda, "1_sharpe", "psr_0"), "informativa", "info",
              "Probabilità che lo Sharpe vero sia sopra zero, senza contare le prove fatte."),
    ]
    if dsr is None or pbo is None or p10 is None:
        return _gruppo("grigio", voci)
    if dsr >= DSR_VERDE and pbo < PBO_VERDE and p10 > CPCV_P10_VERDE:
        return _gruppo("verde", voci)
    if dsr >= DSR_GIALLO and pbo < PBO_GIALLO:
        return _gruppo("giallo", voci)
    return _gruppo("rosso", voci)


def costo_medio(rob):
    """Costo medio per trade in escursioni: lordo meno netto."""
    lordo, netto = _get(rob, "base", "lorda_esc"), _get(rob, "base", "media_esc")
    return None if lordo is None or netto is None else lordo - netto


def _costi(scheda, rob):
    lordo, costo = _get(rob, "base", "lorda_esc"), costo_medio(rob)
    rapporto = lordo / costo if lordo is not None and costo is not None and costo > 0 else None
    sr2 = _get(rob, "costi_doppi", "sharpe")
    voci = [
        _voce("Lordo medio / costo medio", rapporto, f">= {RAPPORTO_COSTI_VERDE} (giallo >= {RAPPORTO_COSTI_GIALLO})",
              "grigio" if rapporto is None else "verde" if rapporto >= RAPPORTO_COSTI_VERDE
              else "giallo" if rapporto >= RAPPORTO_COSTI_GIALLO else "rosso",
              "Quante volte il guadagno medio per trade prima dei costi copre lo spread e il costo notturno di IG."),
        _voce("Sharpe con costi doppi", sr2, "> 0", _e(None if sr2 is None else sr2 > 0),
              "Sharpe annuo se spread e costo notturno fossero il doppio."),
        _voce("Media lorda per trade (escursioni)", lordo, "informativa", "info", "Guadagno medio prima dei costi."),
        _voce("Costo medio per trade (escursioni)", costo, "informativa", "info", "Spread e costo notturno medi."),
    ]
    if rapporto is None or sr2 is None:
        return _gruppo("grigio", voci)
    if rapporto >= RAPPORTO_COSTI_VERDE and sr2 > 0:
        return _gruppo("verde", voci)
    if rapporto >= RAPPORTO_COSTI_GIALLO:
        return _gruppo("giallo", voci)
    return _gruppo("rosso", voci)


def _anni_positivi(rob):
    anni = _get(rob, "base", "per_anno")
    if anni:
        return sum(1 for v in anni.values() if v > 0) / len(anni)
    return _get(rob, "base", "anni_positivi")


def _regolarita(scheda, rob):
    r2 = _get(scheda, "3_regolarita", "r2")
    anni = _anni_positivi(rob)
    fin = _get(scheda, "3_regolarita", "sharpe_mobile", "quota_positiva")
    voci = [
        _voce("R²", r2, f">= {R2_VERDE}", _e(None if r2 is None else r2 >= R2_VERDE),
              "Quanto la curva cumulata somiglia a una retta (1 = retta perfetta)."),
        _voce("Anni positivi", anni, f">= {QUOTA_ANNI_VERDE}", _e(None if anni is None else anni >= QUOTA_ANNI_VERDE),
              "Quota di anni di calendario chiusi in profitto."),
        _voce("Finestre di 12 mesi con Sharpe positivo", fin, f">= {QUOTA_FINESTRE_VERDE}",
              _e(None if fin is None else fin >= QUOTA_FINESTRE_VERDE),
              "Quota di finestre mobili di un anno in cui lo Sharpe è positivo."),
        _voce("K-ratio", _get(scheda, "3_regolarita", "k_ratio"), "informativa", "info",
              "Pendenza della curva divisa per l'errore della pendenza."),
        _voce("Trimestri positivi", _get(scheda, "3_regolarita", "trimestri_positivi"), "informativa", "info",
              "Quota di trimestri chiusi in profitto."),
    ]
    ok = [v["esito"] == "verde" for v in voci[:3] if v["esito"] != "grigio"]
    if len(ok) < 3:
        return _gruppo("grigio", voci)
    return _gruppo("verde" if all(ok) else "giallo" if sum(ok) >= 2 else "rosso", voci)


def _robustezza(scheda, rob):
    zona = _get(rob, "vicini", "rapporto")
    senza = _get(scheda, "4_robustezza", "profitto_senza_10_migliori")
    sp = _get(rob, "ingresso_spostato")
    sp_ok = None
    if sp:
        medie = [_get(sp, "meno_15", "media_esc"), _get(sp, "piu_15", "media_esc")]
        sp_ok = None if any(m is None for m in medie) else all(m > 0 for m in medie)
    gem = _get(rob, "gemello", "media_esc")
    rec = _get(rob, "base", "media_recente_esc")
    voci = [
        _voce("Zona stabile dei parametri", zona, f">= {ZONA_STABILE_VERDE}",
              _e(None if zona is None else zona >= ZONA_STABILE_VERDE),
              "Mediana degli Sharpe delle combinazioni vicine divisa per quello del candidato."),
        _voce("Profitto senza i 10 trade migliori", senza, "> 0", _e(None if senza is None else senza > 0),
              "Se il risultato regge togliendo i dieci trade più fortunati (escursioni)."),
        _voce("Ingresso spostato di ±15 minuti", sp_ok, "media > 0 in entrambi i versi", _e(sp_ok),
              "Se il vantaggio resta entrando 15 minuti prima o dopo."),
        _voce("Prodotto gemello", gem, "media > 0", _e(None if gem is None else gem > 0),
              "Media per trade della stessa regola su un prodotto simile."),
        _voce("Media 2019-2023", rec, "> 0", _e(None if rec is None else rec > 0),
              "Media per trade negli ultimi cinque anni della scoperta."),
        _voce("Specchio (regola speculare)", _get(rob, "specchio", "media_esc"), "informativa", "info",
              "Media per trade della regola per l'altro lato: un vantaggio vero in genere non si ripete uguale."),
        _voce("Media dei giorni ad alta escursione", _get(rob, "regimi", "sopra", "media"), "informativa", "info",
              "Media per trade nei giorni con escursione sopra la mediana."),
        _voce("Media dei giorni a bassa escursione", _get(rob, "regimi", "sotto", "media"), "informativa", "info",
              "Media per trade nei giorni con escursione sotto la mediana."),
    ]
    dispo = [v["esito"] for v in voci if v["esito"] in ("verde", "rosso")]
    if not dispo:
        return _gruppo("grigio", voci)
    verdi = dispo.count("verde")
    return _gruppo("verde" if verdi == len(dispo) else "giallo" if verdi * 2 >= len(dispo) else "rosso", voci)


def _rischio(scheda, rob):
    rapporto = _get(scheda, "6_montecarlo", "rapporto_dd")
    z = _get(scheda, "5_z_wald_wolfowitz", "z")
    voci = [
        _voce("Drawdown a blocchi / rimescolato", rapporto, f"<= {RAPPORTO_DD_VERDE} (giallo <= {RAPPORTO_DD_GIALLO})",
              "grigio" if rapporto is None else "verde" if rapporto <= RAPPORTO_DD_VERDE
              else "giallo" if rapporto <= RAPPORTO_DD_GIALLO else "rosso",
              "Mediana del drawdown con perdite a grappoli divisa per quella con perdite sparse a caso."),
        _voce("z di Wald-Wolfowitz", z, f"|z| < {Z_WW_MAX}", _e(None if z is None else abs(z) < Z_WW_MAX),
              "Se vincite e perdite si alternano come a caso (|z| piccolo) o a serie."),
        _voce("Drawdown massimo (escursioni)", _get(scheda, "3_regolarita", "massimo"), "informativa", "info",
              "Massima perdita dal massimo precedente della curva."),
        _voce("Drawdown a blocchi, 95° percentile", _get(scheda, "6_montecarlo", "blocchi", "drawdown", "p95"),
              "informativa", "info", "Drawdown superato solo nel 5% delle simulazioni a blocchi."),
        _voce("Peggior serie di perdite, 95° percentile", _get(scheda, "6_montecarlo", "blocchi", "serie_perdite", "p95"),
              "informativa", "info", "Giorni di perdita consecutivi superati solo nel 5% delle simulazioni."),
    ]
    if rapporto is None or z is None:
        return _gruppo("grigio", voci)
    if rapporto <= RAPPORTO_DD_VERDE and abs(z) < Z_WW_MAX:
        return _gruppo("verde", voci)
    if rapporto <= RAPPORTO_DD_GIALLO:
        return _gruppo("giallo", voci)
    return _gruppo("rosso", voci)


def _portafoglio(scheda, rob):
    return _gruppo("grigio", [_voce("Sovrapposizione con i sistemi in produzione", None, "da definire", "grigio",
                                    "Serve la lista dei trade dei sistemi in produzione.")])


def _sintesi(g):
    voci = [v for v in g["voci"] if v["esito"] != "info"]
    if not voci:
        return "nessuna voce"
    if g["esito"] == "grigio":
        mancanti = [v["nome"] for v in voci if v["esito"] == "grigio"]
        return "mancano: " + ", ".join(mancanti) if mancanti else "dati mancanti"
    ko = [v["nome"] for v in voci if v["esito"] in ("rosso", "giallo")]
    if not ko:
        return f"tutte le {len(voci)} voci superate"
    return f"{len(voci) - len(ko)} voci su {len(voci)} superate; non superate: " + ", ".join(ko)


# ---------------------------------------------------------------- misure e filtri di Andrea

def soglia_guadagno(ore_medie: float) -> float:
    """Guadagno medio minimo a trade, in euro, per la durata media del trade in ore."""
    for fino_a, euro in SOGLIE_GUADAGNO:
        if ore_medie <= fino_a:
            return euro
    return SOGLIE_GUADAGNO[-1][1]


def misure(trade, date, euro_punto: float | None, n_barre: int | None = None, anni: tuple = (2011, 2023)) -> dict:
    """Le misure su cui giudicano i filtri, da una tabella dei trade (colonne `ingresso`, `uscita`, `barre`,
    `punti`, `costo`) per 1 CFD IG. `date` sono i giorni di borsa (datetime64[D], ordinati) del periodo,
    `n_barre` il numero di barre del periodo (per il tempo in mercato), `anni` gli estremi del periodo."""
    from . import metriche
    n = int(trade.height)
    anni_n = anni[1] - anni[0] + 1
    out = {"euro_punto": euro_punto, "n": n, "trade_anno": n / anni_n, "guadagno_medio": None, "lordo_medio": None,
           "costo_medio": None, "rapporto_costi": None, "ore_medie": None, "in_mercato": None, "r2": None,
           "anni_positivi": None, "utile": None, "drawdown": None, "utile_su_dd": None}
    if n:
        out["ore_medie"] = float((trade["uscita"] - trade["ingresso"]).dt.total_seconds().mean() / 3600)
        if n_barre:
            out["in_mercato"] = float(trade["barre"].sum() / n_barre)
    if euro_punto is None or n < 3:
        return out
    ep = float(euro_punto)
    punti, costo = trade["punti"].to_numpy(), trade["costo"].to_numpy()
    out["guadagno_medio"] = float(punti.mean() * ep)
    out["costo_medio"] = float(costo.mean() * ep)
    out["lordo_medio"] = out["guadagno_medio"] + out["costo_medio"]
    out["rapporto_costi"] = out["lordo_medio"] / out["costo_medio"] if out["costo_medio"] > 0 else None
    d = np.asarray(date).astype("datetime64[D]")
    giorno = np.minimum(np.searchsorted(d, trade["uscita"].dt.date().to_numpy().astype("datetime64[D]")), len(d) - 1)
    g = np.bincount(giorno, weights=punti, minlength=len(d)) * ep
    out["utile"] = float(g.sum())
    dd = metriche.drawdown(g)["massimo"]
    out["drawdown"] = float(dd)
    out["utile_su_dd"] = out["utile"] / dd if dd > 0 else None
    out["r2"] = float(metriche.r2(g)) if g.std() > 0 else None
    anno_u = trade["uscita"].dt.year().to_numpy()
    out["anni_positivi"] = float(np.mean([punti[anno_u == a].sum() > 0 for a in range(anni[0], anni[1] + 1)]))
    return out


def _euro(x: float, limite: float | None = None) -> str:
    """Importo per le frasi di scarto, arrotondato; se è sotto `limite` e l'arrotondamento lo raggiungerebbe, si
    tronca, così un valore appena sotto la soglia non si legge uguale ad essa."""
    cifre = 1 if abs(x) < 100 else 0
    v = round(x, cifre)
    if limite is not None and x < limite <= v:
        v = math.floor(x * 10 ** cifre) / 10 ** cifre
    return f"{v:.{cifre}f}".replace(".", ",") + " €"


def _num(x: float, cifre: int = 2) -> str:
    return f"{x:.{cifre}f}".replace(".", ",")


def _filtro(nome, valore, soglia, ok, spiegazione, motivo):
    """Voce di un filtro; `motivo` è la frase usata se non passa."""
    return {"nome": nome, "valore": valore, "soglia": soglia, "esito": _e(ok), "spiegazione": spiegazione, "motivo": motivo}


def filtri_andrea(m: dict) -> list[dict]:
    """I filtri di Andrea sulle misure: guadagno medio per durata, trade l'anno, R², anni positivi.
    Con il valore del punto ignoto (`euro_punto` None) il sistema non è giudicabile: una sola voce rossa."""
    if m.get("euro_punto") is None:
        return [_filtro("Valore del punto", None, "noto", False, "Senza il valore in euro di 1 CFD IG per punto i filtri in euro non si calcolano.",
                        "valore del punto non noto")]
    ore, gm = m.get("ore_medie"), m.get("guadagno_medio")
    voci = []
    if ore is None or gm is None:
        voci.append(_filtro("Guadagno medio per trade", gm, "n.d.", None, "Mancano i trade per calcolarlo.", "trade insufficienti"))
    else:
        sg = soglia_guadagno(ore)
        voci.append(_filtro("Guadagno medio per trade", gm, f">= {sg:.0f} € (durata media {ore:.1f} ore)", gm >= sg,
                            "Guadagno netto di spread e costo notturno con 1 CFD IG; la soglia cresce con la durata media del trade "
                            "(20 € fino a 36 ore, 30 € fino a 72, 50 € oltre).",
                            f"guadagno medio {_euro(gm, sg)} sotto i {sg:.0f} €"))
    ta = m.get("trade_anno")
    voci.append(_filtro("Trade l'anno", ta, f">= {TRADE_ANNO_MIN:.0f}", None if ta is None else ta >= TRADE_ANNO_MIN,
                        "Numero medio di trade in un anno.", "trade l'anno non calcolabili" if ta is None else f"{_num(ta, 0)} trade l'anno sotto i {TRADE_ANNO_MIN:.0f}"))
    r2 = m.get("r2")
    voci.append(_filtro("Regolarità della curva (R²)", r2, f">= {R2_MIN}", None if r2 is None else r2 >= R2_MIN,
                        "Quanto la curva netta somiglia a una retta (1 = retta perfetta).",
                        "R² non calcolabile" if r2 is None else f"R² {_num(r2)} sotto {_num(R2_MIN)}"))
    ap = m.get("anni_positivi")
    voci.append(_filtro("Anni positivi", ap, f">= {ANNI_POSITIVI_MIN:.0%}", None if ap is None else ap >= ANNI_POSITIVI_MIN,
                        "Quota di anni di calendario chiusi in utile.",
                        "anni positivi non calcolabili" if ap is None else f"anni positivi {ap:.0%} sotto il {ANNI_POSITIVI_MIN:.0%}"))
    return voci


def cancello_statistico(dsr, pbo) -> list[dict]:
    """DSR sul numero effettivo di prove e PBO della famiglia (solo se calcolato: serve almeno 4 combinazioni)."""
    voci = [_filtro("DSR", dsr, f">= {DSR_MIN}", None if dsr is None else dsr >= DSR_MIN,
                    "Probabilità che lo Sharpe resti positivo dopo aver tenuto conto di tutte le prove fatte.",
                    "DSR non calcolabile" if dsr is None else f"DSR {_num(dsr, 3)} sotto {DSR_MIN}")]
    if pbo is not None:
        voci.append(_filtro("PBO della famiglia", pbo, f"< {PBO_MAX}", pbo < PBO_MAX,
                            "Probabilità che la variante scelta in campione sia sotto la mediana fuori campione.",
                            f"PBO {_num(pbo)} oltre {PBO_MAX}"))
    return voci


def prova_finale_voci(prova: dict | None, guadagno_in_sample: float | None) -> list[dict]:
    """Prova finale (risultato di `prova_finale.esegui`, None se non eseguita): utile positivo e guadagno medio
    >= metà di quello in-sample, sul periodo in avanti."""
    if prova is None:
        return [_filtro("Fuori campione", None, "da eseguire", None, "La prova finale non è stata eseguita.", "prova finale non eseguita")]
    avanti = prova.get("avanti")
    if not avanti:
        return [_filtro("Fuori campione", None, "almeno un trade", False, "Nessun trade nel periodo.", "nessun trade fuori campione")]
    n, utile, gm = avanti.get("n") or 0, avanti.get("utile"), avanti.get("guadagno_medio")
    if not n or utile is None or gm is None:
        return [_filtro("Fuori campione", None, "almeno un trade", False, "Nessun trade nel periodo.", "nessun trade fuori campione")]
    voci = [_filtro("Utile fuori campione", utile, "> 0", utile > 0, "Utile netto di 1 CFD IG nel periodo.", "fuori campione negativo")]
    if guadagno_in_sample is not None:
        minimo = FUORI_CAMPIONE_QUOTA_MIN * guadagno_in_sample
        voci.append(_filtro("Guadagno medio fuori campione", gm, f">= {minimo:.1f} € ({FUORI_CAMPIONE_QUOTA_MIN:.0%} di {guadagno_in_sample:.1f} €)",
                            gm >= minimo, "Guadagno medio a trade nel periodo di prova finale, rispetto a quello in-sample.",
                            f"fuori campione {_euro(gm, minimo)} a trade, sotto la metà dei {_euro(guadagno_in_sample)} in-sample"))
    return voci


def _motivo(voci: list[dict]) -> str | None:
    """Motivo principale: la prima voce che non passa (rossa o con dato mancante)."""
    for v in voci:
        if v["esito"] in ("rosso", "grigio"):
            return v["motivo"]
    return None


def giudica(scheda: dict | None, robustezza: dict | None, misure: dict | None = None,
            prova_finale: dict | None = None) -> dict:
    """Giudizio del candidato: filtri di Andrea, cancello statistico e prova finale.

    `scheda` è quella di `metriche.scheda`, `robustezza` i controlli di `robustezza.calcola`, `misure` quelle di
    `misure()` sul backtest al minuto e `prova_finale` il risultato di `prova_finale.esegui` (None se non
    eseguita: in quel caso un sistema che ha passato il resto resta scartato per "prova finale non eseguita").
    Esito `candidato` o `scartato`, con il motivo principale in una frase; i sei gruppi sono il dettaglio."""
    misure = misure or {}
    funz = {"caso": _caso, "costi": _costi, "regolarita": _regolarita, "robustezza": _robustezza,
            "rischio": _rischio, "portafoglio": _portafoglio}
    gruppi = {}
    for k, nome, cancello in GRUPPI:
        g = funz[k](scheda or {}, robustezza or {})
        g.update({"nome": nome, "cancello": cancello, "sintesi": _sintesi(g)})
        gruppi[k] = g
    voci_filtri = filtri_andrea(misure) if misure else [_filtro("Misure", None, "da calcolare", None, "Misure non calcolate.", "misure non calcolate")]
    voci_stat = cancello_statistico(_get(scheda, "1_sharpe", "dsr"), _get(scheda, "2_pbo", "pbo"))
    scoperta = voci_filtri + voci_stat
    motivo = _motivo(scoperta)
    voci_pf = None
    if motivo is None:
        voci_pf = prova_finale_voci(prova_finale, misure.get("guadagno_medio"))
        motivo = _motivo(voci_pf)
    return {"esito": "scartato" if motivo else "candidato", "motivo": motivo or "passa filtri, cancello statistico e prova finale",
            "filtri": voci_filtri, "statistico": voci_stat, "prova_finale": voci_pf, "misure": misure,
            "passa_scoperta": _motivo(scoperta) is None, "gruppi": gruppi}
