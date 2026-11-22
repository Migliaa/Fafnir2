"""Traduzione di una regola del motore in codice ProRealCode (cruscotto, `ricerca/spec-cruscotto.md`, A3).

Convenzioni di `motori/eventi.py`: `da`/`a` e `uscita.ora` sono l'ora di chiusura della barra (`Time`),
l'ordine parte alla chiusura ed è eseguito alla barra dopo, `uscita.barre = N` è
`BarIndex - TradeIndex > N`, una posizione alla volta. In testa c'è la console di gestione di
`moduli/console-rischio-per-trade.txt` (con `Aggressivita = 0`, come vuole il progetto per le proposte).
Le famiglie che non si sanno tradurre lasciano un commento `// DA TRADURRE: ...` e `completo = False`.
"""
from __future__ import annotations

from . import condizioni
from .config import RADICE

CONSOLE = RADICE / "moduli" / "console-rischio-per-trade.txt"
SEGNAPOSTO = "// ... parametri della strategia"
STOP_DIMENSIONE_ESC = 1.0       # stop di riferimento per la taglia quando la regola non ha stop
OPERATORI_PRC = {">": ">", ">=": ">=", "<": "<", "<=": "<=", "==": "="}

# famiglia: (long, short, booleana) con le espressioni ProRealCode; `{0}` e `{1}` sono i parametri
TRADUZIONI = {
    "dist_apertura": ("(close - DOpen(0)) / AverageTrueRange[{0}]", "(DOpen(0) - close) / AverageTrueRange[{0}]", False),
    "dist_media": ("(close - ExponentialAverage[{0}](close)) / EscMedia",
                   "(ExponentialAverage[{0}](close) - close) / EscMedia", False),
    "rsi": ("RSI[{0}](close)", "100 - RSI[{0}](close)", False),
    "pos_chiusura_ieri": ("(DClose(1) - DLow(1)) / (DHigh(1) - DLow(1))",
                          "(DHigh(1) - DClose(1)) / (DHigh(1) - DLow(1))", False),
    "minimo_ieri_su": ("(DLow(1) - DLow({0})) / EscMedia", "(DHigh({0}) - DHigh(1)) / EscMedia", False),
    "dal_massimo_seduta": ("(close - DHigh(0)) / EscMedia", "(DLow(0) - close) / EscMedia", False),
    "dal_minimo_ieri": ("(close - DLow(1)) / EscMedia", "(DHigh(1) - close) / EscMedia", False),
    "dal_close_ieri": ("(close - DClose(1)) / EscMedia", "(DClose(1) - close) / EscMedia", False),
    "gap": ("(DOpen(0) - DClose(1)) / EscMedia", "(DClose(1) - DOpen(0)) / EscMedia", False),
    "rottura_barra": ("(high - high[1]) / EscMedia", "(low[1] - low) / EscMedia", False),
    "escursione_oggi": ("(DHigh(0) - DLow(0)) / EscMedia", "(DHigh(0) - DLow(0)) / EscMedia", False),
    "incrocio": ("Average[{0}](close) > Average[{1}](close) AND Average[{0}](close)[1] <= Average[{1}](close)[1]",
                 "Average[{0}](close) < Average[{1}](close) AND Average[{0}](close)[1] >= Average[{1}](close)[1]", True),
    "minimo_oggi_su_ieri": ("(DLow(0) - DLow(1)) / EscMedia", "(DHigh(1) - DHigh(0)) / EscMedia", False),
    "inversione_ieri": ("DClose(1) < DOpen(1) AND DClose(2) > DOpen(2)",
                        "DClose(1) > DOpen(1) AND DClose(2) < DOpen(2)", True),
}


def _n(x) -> str:
    return f"{x:g}" if isinstance(x, (int, float)) else str(x)


def _hhmmss(hhmm: str) -> str:
    a, b = hhmm.split(":")
    return f"{int(a):02d}{int(b):02d}00"


def _console() -> tuple[str, str]:
    """Console in due metà, divise dopo il segnaposto dei parametri della strategia."""
    righe = CONSOLE.read_text(encoding="utf-8").splitlines()
    k = next(i for i, r in enumerate(righe) if r.startswith(SEGNAPOSTO))
    testa = [("Aggressivita        = 0" + r[len("Aggressivita        = 1"):])
             if r.startswith("Aggressivita        = 1") else r for r in righe[:k + 1]]
    return "\n".join(testa), "\n".join(righe[k + 1:])


def _grandezza(nome: str, lato: int):
    """(espressione ProRealCode, booleana) della grandezza, o (None, False) se la famiglia non si traduce."""
    fam, *par = nome.split(":")
    if fam not in TRADUZIONI or fam not in condizioni.FAMIGLIE:
        return None, False
    lungo, corto, booleana = TRADUZIONI[fam]
    try:
        return (lungo if lato > 0 else corto).format(*par), booleana
    except IndexError:
        return None, False


def traduci(regola: dict, prodotto: str, barre: int) -> dict:
    """{"codice": str, "completo": bool, "da_tradurre": [str]}."""
    lato = int(regola["lato"])
    da_tradurre: list[str] = []
    u = regola.get("uscita") or {}
    stop, target = regola.get("stop"), regola.get("target")
    max_g = int(regola.get("max_al_giorno", 1))
    testa, resto = _console()
    nome_lato = "long" if lato > 0 else "short"

    # ---- parametri e escursione media
    p = ["", "//=========================================================================",
         f"// REGOLA TRADOTTA DAL MOTORE: {prodotto}, barre da {barre} minuti, {nome_lato}",
         "// Ora = chiusura della barra (Time); l'ordine parte alla chiusura ed entra alla barra dopo.",
         "//=========================================================================",
         f"MaxAlGiorno = {max_g}",
         f"StopEsc = {_n(stop)}      // stop in escursioni medie giornaliere (0 = nessuno)" if stop else
         "StopEsc = 0                // nessuno stop",
         f"TargetEsc = {_n(target)}      // target in escursioni medie giornaliere (0 = nessuno)" if target else
         "TargetEsc = 0              // nessun target",
         f"StopDimensioneEsc = {_n(STOP_DIMENSIONE_ESC)}   // stop di riferimento per la taglia quando StopEsc = 0",
         "",
         "// escursione media giornaliera: media delle ultime 20 differenze DHigh - DLow, da ieri",
         "EscSomma = 0",
         "FOR i = 1 TO 20",
         "   EscSomma = EscSomma + (DHigh(i) - DLow(i))",
         "NEXT",
         "EscMedia = EscSomma / 20",
         "IF StopEsc > 0 THEN",
         "   RifEsc = StopEsc",
         "ELSE",
         "   RifEsc = StopDimensioneEsc",
         "ENDIF",
         "// stop per la taglia, in % del prezzo (la console lo usa in StopL e StopS)",
         "MySLL = max(0.01, RifEsc * EscMedia / close * 100)",
         "MySLS = MySLL"]

    # ---- condizioni d'ingresso
    s = ["", "//---- SEGNALE D'INGRESSO"]
    cond = []
    if regola.get("giorni"):
        cond.append("(" + " OR ".join(f"dayofweek = {g}" for g in regola["giorni"]) + ")")
    da, a = regola.get("da"), regola.get("a")
    if da is not None and a is not None:
        if da == a:
            cond.append(f"time = {_hhmmss(da)}")
        elif eventi_min(da) <= eventi_min(a):
            cond.append(f"(time >= {_hhmmss(da)} AND time <= {_hhmmss(a)})")
        else:
            cond.append(f"(time >= {_hhmmss(da)} OR time <= {_hhmmss(a)})")
    for k, c in enumerate(regola.get("cond", []), 1):
        nome, op, soglia, *grezza = c
        espr, booleana = _grandezza(nome, 1 if grezza else lato)
        if espr is None:
            da_tradurre.append(f"famiglia {nome.split(':')[0]}")
            s.append(f"// DA TRADURRE: condizione {k} ({nome} {op} {_n(soglia)}), famiglia non tradotta")
            continue
        if booleana:
            s += [f"IF {espr} THEN", f"   G{k} = 1", "ELSE", f"   G{k} = 0", "ENDIF"]
        else:
            s.append(f"G{k} = {espr}")
        cond.append(f"G{k} {OPERATORI_PRC[op]} {_n(soglia)}")
    s += ["IF Date <> DataPrec THEN", "   IngressiOggi = 0"]
    if u.get("giorni"):
        s += ["   IF ONMARKET AND BarIndex > TradeIndex THEN", "      CambiGiorno = CambiGiorno + 1", "   ENDIF"]
    s += ["ENDIF", "DataPrec = Date"]
    if u.get("giorni"):
        s += ["IF NOT ONMARKET THEN", "   CambiGiorno = 0", "ENDIF"]
    s.append("Segnale = " + " AND ".join(["EscMedia > 0"] + cond) if cond else "Segnale = EscMedia > 0")
    ordine, chiudi = ("BUY PsL LOTS AT MARKET", "SELL AT MARKET") if lato > 0 else \
        ("SELLSHORT PsS LOTS AT MARKET", "EXITSHORT AT MARKET")
    stato = "LONGONMARKET" if lato > 0 else "SHORTONMARKET"
    s += ["IF NOT ONMARKET AND IngressiOggi < MaxAlGiorno AND Segnale THEN",
          "   // stop e target in punti, fissati con l'escursione della barra di decisione",
          "   StopPunti = StopEsc * EscMedia", "   TargetPunti = TargetEsc * EscMedia",
          f"   {ordine}", "   IngressiOggi = IngressiOggi + 1", "ENDIF"]

    # ---- uscite
    x = ["", "//---- USCITE"]
    ex = []
    if u.get("barre") is not None:
        ex.append(f"BarIndex - TradeIndex > {int(u['barre'])}")
    if u.get("ora"):
        ex.append(f"time = {_hhmmss(u['ora'])}")
    if u.get("venerdi"):
        ex.append(f"(dayofweek = 5 AND time = {_hhmmss(u['venerdi'])})")
    if u.get("giorni"):
        ex.append(f"CambiGiorno >= {int(u['giorni'])}")
    if ex:
        x += [f"IF {stato} AND (" + " OR ".join(ex) + ") THEN", f"   {chiudi}", "ENDIF"]
    else:
        x.append("// nessuna uscita a tempo nella regola")
    if regola.get("pareggio"):
        par = regola["pareggio"]
        da_tradurre.append("pareggio")
        x.append(f"// DA TRADURRE: pareggio (a {_n(par.get('attiva'))} escursioni di guadagno, stop a "
                 f"{_n(par.get('a'))}): il motore lo controlla sui minuti, qui non c'è un equivalente letterale")
    x += ["IF ONMARKET AND StopEsc > 0 THEN", "   SET STOP LOSS StopPunti", "ENDIF",
          "IF ONMARKET AND TargetEsc > 0 THEN", "   SET TARGET PROFIT TargetPunti", "ENDIF"]

    codice = "\n".join(["// Generato da motore/uscita.py: non modificare a mano, rigenerare dal motore.",
                        "DEFPARAM CumulateOrders = False", testa, *p, resto.rstrip("\n"), *s, *x, ""])
    return {"codice": codice, "completo": not da_tradurre, "da_tradurre": da_tradurre}


def eventi_min(hhmm: str) -> int:
    a, b = hhmm.split(":")
    return int(a) * 60 + int(b)


def prorealcode(regola: dict, prodotto: str, barre: int) -> str:
    """Codice ProRealCode della regola (testo); `traduci` dice anche se è completo."""
    return traduci(regola, prodotto, barre)["codice"]
