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
    "vol_relativa": ("EscMedia / EscLunga", "EscMedia / EscLunga", False),
    "dal_1530": ("(close - O1530) / EscMedia", "(O1530 - close) / EscMedia", False),
    "terzo_venerdi": ("dayofweek = 5 AND Day >= 15 AND Day <= 21", "dayofweek = 5 AND Day >= 15 AND Day <= 21", True),
    "giorno_mese": ("Day", "Day", False),
    "corpo_ieri": ("ABS(DClose(1) - DOpen(1)) / (DHigh(1) - DLow(1))",) * 2 + (False,),
    "var_ieri": ("(DClose(1) - DClose(2)) / EscMedia", "(DClose(2) - DClose(1)) / EscMedia", False),
    "ieri_verde": ("(DClose(1) - DOpen(1)) / EscMedia", "(DOpen(1) - DClose(1)) / EscMedia", False),
    "chiusure_in_rialzo": ("(DClose(1) > DClose(2)) + (DClose(2) > DClose(3)) + (DClose(3) > DClose(4))",
                           "(DClose(1) < DClose(2)) + (DClose(2) < DClose(3)) + (DClose(3) < DClose(4))", False),
    "massimo_ieri_su": ("(DHigh(1) - DHigh({0})) / EscMedia", "(DLow({0}) - DLow(1)) / EscMedia", False),
    "interna_ieri": ("DHigh(1) < DHigh(2) AND DLow(1) > DLow(2)",) * 2 + (True,),
    "esterna_ieri": ("DHigh(1) > DHigh(2) AND DLow(1) < DLow(2)",) * 2 + (True,),
    "massimi_crescenti": ("DHigh(1) > DHigh(2) AND DLow(1) > DLow(2)", "DHigh(1) < DHigh(2) AND DLow(1) < DLow(2)", True),
    "nr4": ("(DHigh(1) - DLow(1)) <= MinEsc4",) * 2 + (True,),
    "nr7": ("(DHigh(1) - DLow(1)) <= MinEsc7",) * 2 + (True,),
    "escursione_ieri": ("(DHigh(1) - DLow(1)) / EscMedia",) * 2 + (False,),
    "dal_massimo_20g": ("(close - Max20g) / EscMedia", "(Min20g - close) / EscMedia", False),
    "media_50g": ("(close - Media50g) / EscMedia", "(Media50g - close) / EscMedia", False),
    "media_200g": ("(close - Media200g) / EscMedia", "(Media200g - close) / EscMedia", False),
    "apertura_in_ieri": ("(DOpen(0) - DLow(1)) / (DHigh(1) - DLow(1))", "(DHigh(1) - DOpen(0)) / (DHigh(1) - DLow(1))", False),
    "dall_apertura": ("(close - DOpen(0)) / EscMedia", "(DOpen(0) - close) / EscMedia", False),
    "pos_oggi": ("(close - DLow(0)) / (DHigh(0) - DLow(0))", "(DHigh(0) - close) / (DHigh(0) - DLow(0))", False),
    "massimo_oggi_su_ieri": ("(DHigh(0) - DHigh(1)) / EscMedia", "(DLow(1) - DLow(0)) / EscMedia", False),
    "dal_minimo_seduta": ("(close - DLow(0)) / EscMedia", "(DHigh(0) - close) / EscMedia", False),
    "bollinger": ("(close - BollingerDown[{0}](close)) / (BollingerUp[{0}](close) - BollingerDown[{0}](close))",
                  "(BollingerUp[{0}](close) - close) / (BollingerUp[{0}](close) - BollingerDown[{0}](close))", False),
    "donchian": ("(close - highest[{0}](high)[1]) / AverageTrueRange[{0}](close)",
                 "(lowest[{0}](low)[1] - close) / AverageTrueRange[{0}](close)", False),
    "macd": ("(ExponentialAverage[12](close) - ExponentialAverage[26](close)) / EscMedia",
             "(ExponentialAverage[26](close) - ExponentialAverage[12](close)) / EscMedia", False),
    "adx": ("ADX[{0}]",) * 2 + (False,),
    "atr_rapporto": ("AverageTrueRange[{0}](close) / AverageTrueRange[{1}](close)",) * 2 + (False,),
    "candela": ("(close - open) / EscMedia", "(open - close) / EscMedia", False),
    "avvolgente": ("close > open AND close[1] < open[1] AND close >= open[1] AND open <= close[1]",
                   "close < open AND close[1] > open[1] AND close <= open[1] AND open >= close[1]", True),
    "barra_ampia": ("(high - low) / AverageTrueRange[20](close)",) * 2 + (False,),
    "giorno_settimana": ("dayofweek",) * 2 + (False,),
}
# righe di calcolo che alcune famiglie richiedono prima del segnale
PREPARAZIONE = {
    "vol_relativa": ["// escursione media di 100 giorni, da ieri", "EscSommaL = 0", "FOR i = 1 TO 100",
                     "   EscSommaL = EscSommaL + (DHigh(i) - DLow(i))", "NEXT", "EscLunga = EscSommaL / 100"],
    "dal_1530": ["// apertura della barra delle 15:30 (Wall Street); 0 prima di quell'ora",
                 "IF Date <> DataPrec1530 THEN", "   O1530 = 0", "ENDIF", "DataPrec1530 = Date",
                 "IF OpenTime = 153000 THEN", "   O1530 = open", "ENDIF"],
}
for _k in (4, 7):
    PREPARAZIONE[f"nr{_k}"] = [f"// escursione più piccola dei {_k - 1} giorni prima di ieri", f"MinEsc{_k} = DHigh(2) - DLow(2)",
                               f"FOR i = 3 TO {_k}", f"   MinEsc{_k} = min(MinEsc{_k}, DHigh(i) - DLow(i))", "NEXT"]
PREPARAZIONE["dal_massimo_20g"] = ["// massimo e minimo degli ultimi 20 giorni, fino a ieri", "Max20g = DHigh(1)", "Min20g = DLow(1)",
                                   "FOR i = 2 TO 20", "   Max20g = max(Max20g, DHigh(i))", "   Min20g = min(Min20g, DLow(i))", "NEXT"]
for _g in (50, 200):
    PREPARAZIONE[f"media_{_g}g"] = [f"// media delle ultime {_g} chiusure giornaliere, fino a ieri", f"Somma{_g}g = 0", f"FOR i = 1 TO {_g}",
                                    f"   Somma{_g}g = Somma{_g}g + DClose(i)", "NEXT", f"Media{_g}g = Somma{_g}g / {_g}"]

# condizione aggiunta al segnale quando la grandezza non esiste ancora (in Python vale null e la condizione è falsa)
VALIDA = {"dal_1530": "O1530 > 0", "vol_relativa": "EscLunga > 0"}


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


# futures quotati al contrario di IG: sui dati il prezzo è 1 / quello di IG, quindi un long sui dati è uno short su IG
# con le condizioni speculari (i massimi diventano minimi). Le soglie in escursioni restano valide in prima approssimazione.
ROVESCIATI = {"JY": "USD/JPY", "CD": "USD/CAD", "SF": "USD/CHF"}


def traduci(regola: dict, prodotto: str, barre: int) -> dict:
    """{"codice": str, "completo": bool, "da_tradurre": [str]}."""
    if prodotto in ROVESCIATI:
        r = traduci(condizioni.specchia(regola), f"{ROVESCIATI[prodotto]} (dai dati {prodotto}, lato e condizioni rovesciati)", barre)
        return r
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
    for fam in dict.fromkeys(c[0].split(":")[0] for c in regola.get("cond", [])):
        s += PREPARAZIONE.get(fam, [])
        if fam in VALIDA:
            cond.append(VALIDA[fam])
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
