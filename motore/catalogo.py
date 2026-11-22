"""Scheda di ogni prodotto: gruppo, gemelli, se IG lo quota, costi IG.

Fonte dei costi: `fonti/prodotti/costi-ig.md` (pagine ufficiali ig.com/it lette il 2026-11-22).
- `spread`: spread IG in punti del prezzo dei nostri dati, che è già il costo di un giro completo
  (si compra al prezzo lettera e si vende al denaro). `fasce` dà lo spread per fascia oraria
  (ora italiana, decimale, [da, a)); fuori dalle fasce vale `spread`.
- `finanziamento`: solo il costo amministrativo annuo di IG sul nozionale, per notte. Il tasso di
  riferimento (indici), il tom-next (cambi) e la base dei future (materie prime spot) non si
  contano perché i futures rettificati li contengono già nel loro andamento; resta il ricarico IG.
  Si usa il valore più alto fra quelli, discordanti, delle pagine IG.
- Prodotti che Andrea considera troppo costosi per un sistema (agricoli, bestiame, rame,
  esotici): `adatto=False`; restano come gemelli e per le conferme.
- Le unità di IG per le materie prime (centesimi, ×100) sono dedotte dal livello dei prezzi,
  non scritte da IG: `verificato=False` finché un confronto con la piattaforma non le conferma.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Prodotto:
    nome: str
    gruppo: str
    gemelli: tuple[str, ...] = ()
    ig: bool | None = True
    spread: float | None = None
    fasce: tuple[tuple[float, float, float], ...] = ()
    finanziamento: float = 0.0
    adatto: bool = True
    verificato: bool = False
    note: str = ""
    euro_punto: float | None = None   # valore di 1 CFD IG per punto di prezzo (indici: 1 per punto); None se non noto

    def spread_a(self, ore: np.ndarray) -> np.ndarray:
        """Spread in punti per ogni ora d'ingresso (ore decimali italiane)."""
        s = np.full(len(ore), self.spread, dtype=float)
        for da, a, v in self.fasce:
            dentro = (ore >= da) & (ore < a) if da < a else (ore >= da) | (ore < a)
            s[dentro] = v
        return s

    def costo(self, ore: np.ndarray, prezzo: np.ndarray, notti: np.ndarray) -> np.ndarray | None:
        """Costo in punti di trade aperti alle `ore` e tenuti `notti` notti."""
        if self.spread is None:
            return None
        return self.spread_a(ore) + np.abs(prezzo) * self.finanziamento / 365.0 * notti


_P = Prodotto
IND, FX, MP, ORO = 0.03, 0.008, 0.03, 0.008  # costo amministrativo annuo (indici, cambi, materie prime, oro/argento)


def _fx(pip: float, medio: float) -> dict:
    # spread medio IG lun 01:00 - ven 22:00 (dati IG del 2021); fuori da quella fascia doppio (stima prudente)
    return dict(spread=2 * medio * pip, fasce=((1, 22, medio * pip),), finanziamento=FX)


CATALOGO: dict[str, Prodotto] = {p.nome: p for p in [
    # indici: versione cash a 1 euro/dollaro per punto
    _P("FDAX", "indici europei", ("FESX",), True, 7.0,
       ((9, 17.5, 1.2), (8, 9, 2.0), (17.5, 22, 2.0)), IND,
       euro_punto=1.0, note="Germany 40; sessione notturna Eurex dalla fine del 2018"),
    _P("FESX", "indici europei", ("FDAX",), True, 3.0, ((8, 22, 1.5), (1.25, 8, 2.0)), IND, euro_punto=1.0),
    _P("ES", "indici USA", ("NQ", "YM", "RTY"), True, 1.0, ((15.5, 22, 0.7), (23, 24, 1.8)), IND, euro_punto=1.0),
    _P("NQ", "indici USA", ("ES", "YM", "RTY"), True, 2.9, ((15.5, 22, 1.4), (23, 24, 6.0)), IND, euro_punto=1.0),
    _P("YM", "indici USA", ("ES", "NQ"), True, 4.8, ((15.5, 22, 2.4), (8, 15.5, 3.6), (23, 24, 9.8)), IND, euro_punto=1.0),
    _P("RTY", "indici USA", ("ES",), True, 0.3, ((23, 24, 0.8),), IND, euro_punto=1.0),
    _P("VX", "volatilità", ("ES",), True, 0.1, note="VIX con scadenza: niente finanziamento"),
    # cambi
    _P("AUDJPY", "cambi yen", ("NZDJPY", "CADJPY", "GBPJPY"), True, **_fx(0.01, 1.79)),
    _P("GBPJPY", "cambi yen", ("EURJPY", "AUDJPY"), True, **_fx(0.01, 3.17)),
    _P("EURJPY", "cambi yen", ("GBPJPY", "CHFJPY"), True, **_fx(0.01, 1.97)),
    _P("CADJPY", "cambi yen", ("AUDJPY",), True, **_fx(0.01, 3.05)),
    _P("NZDJPY", "cambi yen", ("AUDJPY",), True, **_fx(0.01, 2.53)),
    _P("CHFJPY", "cambi yen", ("EURJPY",), True, **_fx(0.01, 2.63)),
    _P("EURGBP", "cambi europei", ("EURCHF",), True, **_fx(0.0001, 1.40)),
    _P("EURCHF", "cambi europei", ("EURGBP",), True, **_fx(0.0001, 2.64)),
    _P("AUDUSD", "cambi dollaro", ("NE1", "CD"), True, **_fx(0.0001, 0.82)),
    _P("AD", "cambi dollaro", ("NE1",), True, **_fx(0.0001, 0.82), note="AUD/USD"),
    _P("EC", "cambi dollaro", ("BP", "SF"), True, **_fx(0.0001, 0.85), note="EUR/USD"),
    _P("BP", "cambi dollaro", ("EC",), True, **_fx(0.0001, 1.40), note="GBP/USD"),
    _P("NE1", "cambi dollaro", ("AD",), True, **_fx(0.0001, 2.05), note="NZD/USD"),
    # futures in dollari per unità estera: lo spread IG di USD/xxx convertito al livello tipico
    _P("CD", "cambi dollaro", ("AD",), True, **_fx(0.0001 * 0.56, 1.77),
       note="IG quota USD/CAD; spread convertito con CD circa 0,75"),
    _P("JY", "cambi dollaro", ("SF",), True, **_fx(0.01 * 100 / 140**2, 0.94),
       note="dollari per 100 yen; IG quota USD/JPY, spread convertito con USD/JPY circa 140"),
    _P("SF", "cambi dollaro", ("JY",), True, **_fx(0.0001 / 0.89**2, 1.99),
       note="IG quota USD/CHF; spread convertito con USD/CHF circa 0,89"),
    _P("BTC", "cripto", ("MBT",), True, 100.0, finanziamento=0.25,
       note="finanziamento long 25% annuo; lo short riceve, qui contato come costo (prudente)"),
    _P("MBT", "cripto", ("BTC",), True, 100.0, finanziamento=0.25, note="micro Bitcoin: stesso mercato IG"),
    # tassi: IG quota ×100, spread dei future (nessun finanziamento)
    _P("FGBL", "tassi", ("TY", "US"), True, 0.02, note="Bund"),
    _P("TY", "tassi", ("US", "FGBL"), True, 0.02),
    _P("US", "tassi", ("TY",), True, 0.04),
    # metalli ed energia: forma spot (senza scadenza)
    _P("GC", "metalli", ("SI", "PL"), True, 0.7, finanziamento=ORO, note="IG indica anche 0,3 come minimo"),
    _P("SI", "metalli", ("GC",), True, 0.02, finanziamento=ORO),
    _P("PL", "metalli", ("GC",), True, 1.8, finanziamento=MP),
    _P("HG", "metalli", ("PL",), True, 0.002, finanziamento=MP, adatto=False),
    _P("CL", "energia", ("HO", "RB"), True, 0.03, finanziamento=MP),
    _P("HO", "energia", ("CL",), True, 0.002, finanziamento=MP),
    _P("RB", "energia", ("CL",), True, 0.003, finanziamento=MP),
    _P("NG", "energia", ("CL",), True, 0.003, finanziamento=MP),
    # agricoli e bestiame: forma spot, unità in centesimi come i futures CME
    _P("C", "cereali", ("W", "S"), True, 0.6, finanziamento=MP, adatto=False),
    _P("W", "cereali", ("KW", "C"), True, 0.6, finanziamento=MP, adatto=False),
    _P("KW", "cereali", ("W",), False, adatto=False, note="non trovato fra i mercati IG"),
    _P("S", "semi oleosi", ("SM", "BO"), True, 1.2, finanziamento=MP, adatto=False),
    _P("SM", "semi oleosi", ("S",), True, 0.4, finanziamento=MP, adatto=False),
    _P("BO", "semi oleosi", ("S",), True, 0.06, finanziamento=MP, adatto=False),
    _P("RR", "cereali", ("C",), True, 0.2, finanziamento=MP, adatto=False),
    _P("KC", "soft", ("CC", "SB"), True, 0.2, finanziamento=MP, adatto=False),
    _P("CC", "soft", ("KC",), True, 4.0, finanziamento=MP, adatto=False,
       note="livello dei dati rettificati molto distante dal reale: unità da controllare"),
    _P("SB", "soft", ("KC",), True, 0.03, finanziamento=MP, adatto=False),
    _P("CT", "soft", ("KC",), True, 0.15, finanziamento=MP, adatto=False),
    _P("OJ", "soft", ("KC",), True, 0.24, finanziamento=MP, adatto=False),
    _P("LC", "bestiame", ("FC", "LH"), True, 0.12, finanziamento=MP, adatto=False),
    _P("FC", "bestiame", ("LC",), True, 0.14, finanziamento=MP, adatto=False),
    _P("LH", "bestiame", ("LC",), True, 0.10, finanziamento=MP, adatto=False),
]}


def prodotto(nome: str) -> Prodotto:
    try:
        return CATALOGO[nome]
    except KeyError:
        raise KeyError(f"{nome} non è nel catalogo") from None


def riassunto() -> list[dict]:
    return [{"nome": p.nome, "gruppo": p.gruppo, "ig": p.ig, "adatto": p.adatto,
             "costi": p.spread is not None, "gemelli": list(p.gemelli),
             "euro_punto": p.euro_punto} for p in CATALOGO.values()]
