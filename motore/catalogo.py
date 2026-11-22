"""Scheda di ogni prodotto: gruppo, gemelli, se IG lo quota, costi IG.

I costi sono lo spread IG di un giro completo (ingresso + uscita) in punti del prezzo, nelle
ore principali e fuori, più il finanziamento notturno del CFD come tasso annuo sul nozionale.
Valori indicativi presi dai listini IG pubblici come li ricordavo a novembre 2026: vanno
confrontati con la piattaforma di Andrea (segnati `verificato=False`). Il finanziamento usa il
prezzo rettificato, che differisce da quello vero di qualche punto percentuale: errore piccolo
su un costo piccolo. `ig=None` vuol dire "non so": il prodotto serve come gemello finché
Andrea non conferma.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Prodotto:
    nome: str
    gruppo: str
    gemelli: tuple[str, ...] = ()
    ig: bool | None = True
    spread: float | None = None          # punti, giro completo, ore principali
    spread_fuori: float | None = None    # punti, giro completo, fuori orario
    ore_principali: tuple[int, int] = (0, 24)  # ora italiana [inizio, fine)
    finanziamento: float = 0.0           # tasso annuo sul nozionale per notte tenuta
    verificato: bool = False
    note: str = ""

    def costo(self, ora: int, prezzo: float, notti: int) -> float | None:
        """Costo in punti di un trade aperto all'ora italiana `ora` e tenuto `notti` notti."""
        if self.spread is None:
            return None
        a, b = self.ore_principali
        s = self.spread if a <= ora < b else (self.spread_fuori or self.spread)
        return s + abs(prezzo) * self.finanziamento / 365.0 * notti


_P = Prodotto
INDICE, CAMBIO = 0.03, 0.01  # finanziamento indicativo: indici e materie prime ~3%, cambi ~1%

CATALOGO: dict[str, Prodotto] = {p.nome: p for p in [
    # indici
    _P("FDAX", "indici europei", ("FESX",), True, 1.2, 4.0, (9, 22), INDICE,
       note="Germany 40; sessione notturna Eurex dalla fine del 2018"),
    _P("FESX", "indici europei", ("FDAX",), True, 1.0, 3.0, (9, 22), INDICE),
    _P("ES", "indici USA", ("NQ", "YM", "RTY"), True, 0.4, 1.0, (15, 22), INDICE),
    _P("NQ", "indici USA", ("ES", "YM", "RTY"), True, 1.0, 4.0, (15, 22), INDICE),
    _P("YM", "indici USA", ("ES", "NQ"), True, 2.4, 6.0, (15, 22), INDICE),
    _P("RTY", "indici USA", ("ES",), True, 0.3, 1.0, (15, 22), INDICE),
    _P("VX", "volatilità", ("ES",), True, 0.1, 0.2, (15, 22), INDICE),
    # cambi (futures CME contro dollaro e cross sintetici)
    _P("AUDJPY", "cambi yen", ("NZDJPY", "CADJPY", "GBPJPY"), True, 0.013, 0.03, (8, 22), CAMBIO),
    _P("GBPJPY", "cambi yen", ("EURJPY", "AUDJPY"), True, 0.025, 0.05, (8, 22), CAMBIO),
    _P("EURJPY", "cambi yen", ("GBPJPY", "CHFJPY"), True, 0.015, 0.03, (8, 22), CAMBIO),
    _P("CADJPY", "cambi yen", ("AUDJPY",), True, 0.025, 0.05, (8, 22), CAMBIO),
    _P("NZDJPY", "cambi yen", ("AUDJPY",), True, 0.025, 0.05, (8, 22), CAMBIO),
    _P("CHFJPY", "cambi yen", ("EURJPY",), True, 0.03, 0.06, (8, 22), CAMBIO),
    _P("EURGBP", "cambi europei", ("EURCHF",), True, 0.0009, 0.002, (8, 22), CAMBIO),
    _P("EURCHF", "cambi europei", ("EURGBP",), True, 0.0015, 0.003, (8, 22), CAMBIO),
    _P("AUDUSD", "cambi dollaro", ("NE1", "CD"), True, 0.0006, 0.0015, (8, 22), CAMBIO),
    _P("EC", "cambi dollaro", ("BP", "SF"), True, 0.00006, 0.00015, (8, 22), CAMBIO, note="EUR/USD"),
    _P("BP", "cambi dollaro", ("EC",), True, 0.0009, 0.002, (8, 22), CAMBIO, note="GBP/USD"),
    _P("AD", "cambi dollaro", ("NE1",), True, 0.0006, 0.0015, (8, 22), CAMBIO, note="AUD/USD"),
    _P("NE1", "cambi dollaro", ("AD",), True, 0.0009, 0.002, (8, 22), CAMBIO, note="NZD/USD"),
    _P("CD", "cambi dollaro", ("AD",), True, 0.0001, 0.0003, (8, 22), CAMBIO,
       note="dollaro canadese in USD; IG quota USD/CAD (prezzo inverso)"),
    _P("JY", "cambi dollaro", ("SF",), True, None, None, note="yen in USD per 100 yen; IG quota USD/JPY"),
    _P("SF", "cambi dollaro", ("JY",), True, None, None, note="franco in USD; IG quota USD/CHF"),
    _P("BTC", "cripto", ("MBT",), True, None, None),
    _P("MBT", "cripto", ("BTC",), None),
    # tassi
    _P("FGBL", "tassi", ("TY", "US"), True, 0.02, 0.04, (8, 22), INDICE, note="Bund"),
    _P("TY", "tassi", ("US", "FGBL"), True, 0.03, 0.06, (14, 22), INDICE),
    _P("US", "tassi", ("TY",), True, 0.06, 0.12, (14, 22), INDICE),
    # metalli ed energia
    _P("GC", "metalli", ("SI", "PL"), True, 0.3, 0.6, (8, 22), INDICE),
    _P("SI", "metalli", ("GC",), True, 0.02, 0.04, (8, 22), INDICE),
    _P("PL", "metalli", ("GC",), True, 1.0, 2.0, (8, 22), INDICE),
    _P("HG", "metalli", ("PL",), True, 0.002, 0.004, (8, 22), INDICE),
    _P("CL", "energia", ("HO", "RB"), True, 0.028, 0.05, (9, 22), INDICE),
    _P("HO", "energia", ("CL",), True, None, None),
    _P("RB", "energia", ("CL",), True, None, None),
    _P("NG", "energia", ("CL",), True, 0.005, 0.01, (9, 22), INDICE),
    # agricoli e bestiame: quotazione IG da confermare
    _P("C", "cereali", ("W", "S"), True, None, None),
    _P("W", "cereali", ("KW", "C"), True, None, None),
    _P("KW", "cereali", ("W",), None),
    _P("S", "semi oleosi", ("SM", "BO"), True, None, None),
    _P("SM", "semi oleosi", ("S",), None),
    _P("BO", "semi oleosi", ("S",), None),
    _P("RR", "cereali", ("C",), None, note="riso: probabilmente non quotato"),
    _P("KC", "soft", ("CC", "SB"), True, None, None),
    _P("CC", "soft", ("KC",), True, None, None),
    _P("SB", "soft", ("KC",), True, None, None),
    _P("CT", "soft", ("KC",), True, None, None),
    _P("OJ", "soft", ("KC",), None),
    _P("LC", "bestiame", ("FC", "LH"), None),
    _P("FC", "bestiame", ("LC",), None),
    _P("LH", "bestiame", ("LC",), None),
]}


def prodotto(nome: str) -> Prodotto:
    try:
        return CATALOGO[nome]
    except KeyError:
        raise KeyError(f"{nome} non è nel catalogo") from None


def riassunto() -> list[dict]:
    return [{"nome": p.nome, "gruppo": p.gruppo, "ig": p.ig, "costi": p.spread is not None,
             "gemelli": list(p.gemelli)} for p in CATALOGO.values()]
