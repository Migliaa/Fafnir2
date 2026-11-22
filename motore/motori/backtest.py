"""Backtest al minuto: stessa regola e stessi candidati di `eventi`, ma stop, target e pareggio
seguiti minuto per minuto.

Il formato della regola è quello di `eventi.py` con una chiave in più:
    "pareggio": {"attiva": x, "a": y}   (in escursioni medie giornaliere)
quando il guadagno massimo raggiunto tocca `x`, lo stop si sposta a ingresso + `y` nel verso del
lato (se c'è già uno stop, vale il più stretto dei due). Lo spostamento vale dal minuto dopo
quello in cui `x` è stato toccato, perché dentro un minuto l'ordine dei prezzi non si vede.

Convenzioni, oltre a quelle di `eventi`:
- ingresso, candidati e uscite a tempo sono quelli di `eventi.prova` (l'istante dell'uscita a
  tempo si calcola sulle barre); fra l'apertura della barra d'ingresso e quell'istante si
  scorrono i minuti;
- nello stesso minuto stop e target insieme: vince lo stop; se un minuto apre oltre il livello
  si esce all'apertura di quel minuto, altrimenti al livello;
- dopo un'uscita al minuto la posizione è libera dalla fine di quel minuto;
- colonne dei trade: quelle di `eventi` (compresa `punti`) più `motivo` (`stop`, `target`, `pareggio`, `tempo`);
  `uscita` è l'inizio del minuto d'uscita (o della barra, per l'uscita a tempo) e `barre` le barre
  fra l'ingresso e quella che contiene l'uscita.
"""
from __future__ import annotations

import numpy as np
import polars as pl
from numba import njit

from .. import catalogo, dati
from ..config import SCOPERTA
from . import eventi

MOTIVI = np.array(["tempo", "stop", "target", "pareggio"])
MINUTO_US = 60_000_000


def _us(serie: pl.Series) -> np.ndarray:
    return serie.dt.epoch("us").to_numpy().astype(np.int64)


@njit(cache=True)
def _percorso(cand, o, esc, tod, giorno, dn, apre, bar_m0, mt, mo, mh, ml,
              lato, barre, ora, ven, giorni, stop, target, att, abe, max_g):
    n = len(o)
    nm = len(mt)
    k_max = len(cand)
    ent = np.full(k_max, -1, np.int64)
    ubar = np.full(k_max, -1, np.int64)
    ut = np.zeros(k_max, np.int64)
    px = np.zeros(k_max)
    mot = np.zeros(k_max, np.int64)
    k = 0
    libero = np.int64(-(2 ** 62))      # primo istante (microsecondi) in cui si può rientrare
    giorno_ult, quanti = -1, 0
    for i in cand:
        e = i + 1
        if e >= n or apre[e] < libero:
            continue
        if dn[i] != giorno_ult:
            giorno_ult, quanti = dn[i], 0
        if quanti >= max_g:
            continue
        # istante dell'uscita a tempo, come in eventi: decisa alla chiusura di j, eseguita all'apertura di j+1
        texit = -1
        cambi = 0
        for j in range(e, n):
            if j > e and dn[j] != dn[j - 1]:
                cambi += 1
            esci = (barre >= 0 and j - e > barre) or (ora >= 0 and tod[j] == ora) \
                or (ven >= 0 and giorno[j] == 5 and tod[j] == ven) or (giorni > 0 and cambi >= giorni)
            if esci:
                if j + 1 < n:
                    texit = j + 1
                break
        m_a = bar_m0[e]
        m_b = bar_m0[texit] if texit >= 0 else nm
        p0 = o[e]
        x = esc[i]
        sl = p0 - lato * stop * x if stop > 0 else np.nan
        tp = p0 + lato * target * x if target > 0 else np.nan
        liv_att = p0 + lato * att * x if att > 0 else np.nan
        sl_pareggio = False
        armato = False
        motivo, prezzo, tempo = -1, 0.0, np.int64(0)
        for m in range(m_a, m_b):
            if not np.isnan(sl) and ((lato > 0 and ml[m] <= sl) or (lato < 0 and mh[m] >= sl)):
                beyond = (lato > 0 and mo[m] <= sl) or (lato < 0 and mo[m] >= sl)
                motivo = 3 if sl_pareggio else 1
                prezzo = mo[m] if beyond else sl
                tempo = mt[m]
                break
            if not np.isnan(tp) and ((lato > 0 and mh[m] >= tp) or (lato < 0 and ml[m] <= tp)):
                beyond = (lato > 0 and mo[m] >= tp) or (lato < 0 and mo[m] <= tp)
                motivo = 2
                prezzo = mo[m] if beyond else tp
                tempo = mt[m]
                break
            if att > 0 and not armato and ((lato > 0 and mh[m] >= liv_att) or (lato < 0 and ml[m] <= liv_att)):
                armato = True
                nuovo = p0 + lato * abe * x
                if np.isnan(sl) or (lato > 0 and nuovo > sl) or (lato < 0 and nuovo < sl):
                    sl = nuovo
                    sl_pareggio = True
        if motivo >= 0:
            ent[k], ut[k], px[k], mot[k] = e, tempo, prezzo, motivo
            ubar[k] = np.searchsorted(apre, tempo, side="right") - 1
            libero = tempo + 60_000_000
        elif texit >= 0:
            ent[k], ubar[k], ut[k], px[k], mot[k] = e, texit, apre[texit], o[texit], 0
            libero = apre[texit]
        else:
            break       # fine dei dati in posizione: il trade non si conta
        k += 1
        quanti += 1
    return ent[:k], ubar[:k], ut[:k], px[:k], mot[:k]


def simula(nome: str, minuti: int, regola: dict, tabella: pl.DataFrame | None = None,
           m1: pl.DataFrame | None = None, molt_costi: float = 1.0, anni=None):
    """Restituisce (riassunto JSON, tabella dei trade), come `eventi.prova`, con stop, target e
    pareggio controllati sui minuti. `tabella` è la base di `eventi.base`, `m1` i minuti
    (`dati.minuti`) del prodotto; se mancano si caricano. `molt_costi` moltiplica i costi del
    catalogo (2.0 = costi doppi); la colonna `punti` dei trade è il netto in punti di prezzo e `costo` il costo.
    `anni` (None: la scoperta) è il periodo; con la tabella già costruita deve essere lo stesso."""
    b = eventi.base(nome, minuti, anni) if tabella is None else tabella
    if m1 is None:
        m1 = dati.minuti(nome)
    m1 = eventi._anni(m1, SCOPERTA if anni is None else anni).sort("apre")
    lato = int(regola["lato"])
    cand = eventi.candidati(b, regola)

    u = regola.get("uscita", {})
    par = regola.get("pareggio") or {}
    arr = {x: b[x].to_numpy() for x in ("o", "esc")}
    tod, giorno, dn = (b[x].to_numpy().astype(np.int64) for x in ("tod", "giorno", "dn"))
    apre, mt = _us(b["apre"]), _us(m1["apre"])
    bar_m0 = np.searchsorted(mt, apre, side="left").astype(np.int64)
    ent, ubar, ut, px, mot = _percorso(
        cand, arr["o"], np.nan_to_num(arr["esc"]), tod, giorno, dn, apre, bar_m0, mt,
        m1["o"].to_numpy(), m1["h"].to_numpy(), m1["l"].to_numpy(), lato,
        -1 if u.get("barre") is None else int(u["barre"]), eventi._min(u.get("ora")),
        eventi._min(u.get("venerdi")), int(u.get("giorni") or 0),
        float(regola.get("stop") or 0), float(regola.get("target") or 0),
        float(par.get("attiva") or 0), float(par.get("a") or 0), int(regola.get("max_al_giorno", 1)))

    esc = arr["esc"][ent - 1]
    lordo = lato * (px - arr["o"][ent]) / esc
    prod = catalogo.prodotto(nome)
    ore = b["apre"].dt.hour().to_numpy()[ent] + b["apre"].dt.minute().to_numpy()[ent] / 60
    costo = prod.costo(ore, arr["o"][ent], dn[ubar] - dn[ent])
    costo_p = np.zeros(len(ent)) if costo is None else molt_costi * costo
    netto = lordo - costo_p / esc
    punti = lato * (px - arr["o"][ent]) - costo_p
    tipo = b.schema["apre"]
    uscita = (pl.Series("uscita", ut, dtype=pl.Int64).cast(pl.Datetime("us"))
              .dt.replace_time_zone("UTC").dt.convert_time_zone(tipo.time_zone).cast(tipo))
    trade = pl.DataFrame({"ingresso": b["apre"].gather(ent), "uscita": uscita, "barre": ubar - ent,
                          "lordo": lordo, "netto": netto, "punti": punti,
                          "costo": costo_p, "motivo": MOTIVI[mot]})
    return eventi._riassunto(nome, minuti, regola, trade, b, costo is not None), trade
