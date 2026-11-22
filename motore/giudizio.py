"""Giudizio calcolato di un candidato (cruscotto, `ricerca/spec-cruscotto.md`, A2).

Deterministico e uguale per tutti: sei gruppi con esito verde, giallo, rosso o grigio (dati mancanti)
e le voci con valore, soglia ed esito. Le soglie sono le costanti qui sotto. I gruppi "caso" e
"costi" sono cancelli: un rosso lì e il candidato è scartato.
"""
from __future__ import annotations

# ---- soglie iniziali (da rivedere dopo i primi esperimenti)
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

GRUPPI = [("caso", "Caso o vantaggio", True), ("costi", "Costi e fattibilità", True),
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


def esito_complessivo(gruppi: dict) -> str:
    """`candidato`, `da_rivedere` o `scartato` dai colori dei gruppi."""
    cancelli = [gruppi[k]["esito"] for k, _, c in GRUPPI if c]
    if "rosso" in cancelli:
        return "scartato"
    if any(e == "grigio" for e in cancelli):
        return "da_rivedere"
    # il caso deve essere verde: DSR e PBO sono le regole di selezione del progetto, non avvisi
    if gruppi["caso"]["esito"] != "verde":
        return "da_rivedere"
    altri = [gruppi[k]["esito"] for k, _, c in GRUPPI if not c]
    return "da_rivedere" if "rosso" in altri else "candidato"


def giudica(scheda: dict | None, robustezza: dict | None) -> dict:
    """Giudizio del candidato dalla sua scheda (`metriche.scheda`) e dai controlli di `robustezza`.

    Se un cancello è grigio (dati mancanti) il candidato resta `da_rivedere`: non si promuove né si scarta."""
    funz = {"caso": _caso, "costi": _costi, "regolarita": _regolarita, "robustezza": _robustezza,
            "rischio": _rischio, "portafoglio": _portafoglio}
    gruppi = {}
    for k, nome, cancello in GRUPPI:
        g = funz[k](scheda or {}, robustezza or {})
        g.update({"nome": nome, "cancello": cancello, "sintesi": _sintesi(g)})
        gruppi[k] = g
    return {"esito": esito_complessivo(gruppi), "gruppi": gruppi}
