"""Controlli di robustezza, giudizio, ProRealCode e arricchimento su dati finti. Uso: python -m motore.test_robustezza"""
import copy
import json
from contextlib import contextmanager

from . import catalogo, esperimento, giudizio, robustezza, uscita, validazione
from .test_esperimento import CAMPI, _Ambiente, _scrivi

P = catalogo.Prodotto


@contextmanager
def _ambiente():
    """Dati finti di test_esperimento più due prodotti di prova con costi: TST (2 euro a punto) e il gemello TW2."""
    with _Ambiente() as tmp:
        vecchio = dict(catalogo.CATALOGO)
        catalogo.CATALOGO["TST"] = P("TST", "prova", ("TW2",), True, 0.05, euro_punto=2.0)
        catalogo.CATALOGO["TW2"] = P("TW2", "prova", ("TST",), True, 0.05)
        catalogo.CATALOGO["KW"] = P("KW", "prova", (), True)       # senza costi, senza gemelli, senza euro a punto
        try:
            yield tmp
        finally:
            catalogo.CATALOGO.clear()
            catalogo.CATALOGO.update(vecchio)


def _lancia(tmp):
    f = _scrivi(tmp, prodotti=["TST"], k=3)
    return esperimento.lancia(f, n_mc=100)


# ---------------------------------------------------------------- robustezza

def test_robustezza_coerente():
    with _ambiente() as tmp:
        regola = {"lato": 1, "da": "09:00", "a": "09:00", "uscita": {"barre": 5}, "max_al_giorno": 1}
        rob, trade = robustezza.calcola(regola, "TST", 5)
        b = rob["base"]
        assert b["n"] > 1000 and b["media_esc"] > 0, b
        # costi doppi: la media scende esattamente del costo medio (lordo - netto)
        costo = b["lorda_esc"] - b["media_esc"]
        assert costo > 0
        assert abs(rob["costi_doppi"]["media_esc"] - (b["media_esc"] - costo)) < 3e-4, (rob["costi_doppi"], b)
        assert rob["costi_doppi"]["lorda_esc"] == b["lorda_esc"]
        # euro: 2 euro a punto sulla somma dei punti netti
        assert abs(rob["euro"]["profitto"] - 2.0 * trade["punti"].sum()) < 0.01, rob["euro"]
        assert rob["euro"]["trade_medio"] > 0 and rob["euro"]["drawdown"] >= 0
        # ingresso spostato di -15 e +15 minuti: entrambi con vantaggio, perché il rialzo dura un'ora
        sp = rob["ingresso_spostato"]
        assert sp["meno_15"]["n"] > 1000 and sp["piu_15"]["n"] > 1000, sp
        assert sp["meno_15"]["media_esc"] > 0 and sp["piu_15"]["media_esc"] > 0, sp
        assert robustezza._sposta(regola, -15)["da"] == "08:45" and robustezza._sposta(regola, 15)["a"] == "09:15"
        # specchio: il lato opposto perde
        assert rob["specchio"]["media_esc"] < 0, rob["specchio"]
        # gemello: primo gemello con costi
        assert rob["gemello"]["prodotto"] == "TW2" and rob["gemello"]["media_esc"] > 0, rob["gemello"]
        # regimi: i due gruppi coprono tutti i trade
        rg = rob["regimi"]
        assert rg["sopra"]["n"] + rg["sotto"]["n"] == b["n"] and rg["sopra"]["n"] > 100 and rg["sotto"]["n"] > 100
        # finestre di 12 mesi: la prima coincide con il 2011, passo di 3 mesi
        fin = rob["finestre_12_mesi"]
        assert fin[0]["da"] == "2011-01" and fin[0]["a"] == "2011-12" and fin[1]["da"] == "2011-04", fin[:2]
        assert fin[-1]["a"] == "2023-12" and len(fin) == 4 * 13 - 3, (fin[-1], len(fin))
        assert abs(fin[0]["profitto"] - b["per_anno"]["2011"]) < 0.01, (fin[0], b["per_anno"])
        # calendario: i mesi dell'anno sommano al profitto dell'anno
        assert abs(sum(rob["calendario"]["2011"].values()) - b["per_anno"]["2011"]) < 0.01
        assert rob["vicini"] is None          # senza famiglia non c'è registro da leggere
    # un prodotto senza costi né gemelli: i campi in euro e il gemello sono None
    with _ambiente():
        regola = {"lato": 1, "da": "09:00", "a": "09:00", "uscita": {"barre": 0}, "max_al_giorno": 1}
        rob = robustezza.robustezza(regola, "KW", 60)
        assert rob["gemello"] is None and rob["ingresso_spostato"] is None, rob
        assert rob["euro"]["profitto"] is None and rob["euro"]["drawdown"] is None, rob["euro"]


def test_vicini_dal_registro():
    with _ambiente() as tmp:
        _lancia(tmp)
        righe = {r["parametri"]["uscita.barre"]: r["sharpe"] for r in validazione._righe()}
        assert set(righe) == {0, 1, 2, 3, 4, 5}
        v = robustezza.vicini("prova", "TST", {"uscita.barre": 2}, None)
        assert v["n"] == 2 and sorted(x["parametri"]["uscita.barre"] for x in v["vicini"]) == [1, 3], v
        med = sorted([righe[1], righe[3]])
        assert abs(v["mediana"] - (med[0] + med[1]) / 2) < 1e-9
        assert abs(v["rapporto"] - v["mediana"] / righe[2]) < 1e-9 and v["sharpe_candidato"] == righe[2]
        # agli estremi della griglia c'è un solo vicino
        assert robustezza.vicini("prova", "TST", {"uscita.barre": 0}, None)["n"] == 1
        assert robustezza.vicini("prova", "TST", {"uscita.barre": 5}, None)["n"] == 1
        assert robustezza.vicini("altra", "TST", {"uscita.barre": 2}, None) is None
        # il registro si legge soltanto
        assert len(validazione._righe()) == 6


# ---------------------------------------------------------------- giudizio

def _scheda(dsr=0.99, pbo=0.1, p10=0.2, r2=0.9, qf=0.8, rapporto_dd=1.0, z=0.5, senza=10.0):
    return {"1_sharpe": {"dsr": dsr, "sharpe_lo": 1.0, "psr_0": 1.0}, "2_pbo": {"pbo": pbo}, "2_cpcv": {"p10": p10},
            "3_regolarita": {"r2": r2, "sharpe_mobile": {"quota_positiva": qf}, "massimo": 1.0},
            "4_robustezza": {"profitto_senza_10_migliori": senza},
            "5_z_wald_wolfowitz": {"z": z}, "6_montecarlo": {"rapporto_dd": rapporto_dd}}


def _rob(lordo=0.03, netto=0.02, sr2=0.5, rapporto=0.8, sp=0.01, gem=0.01, rec=0.01, anni=None):
    return {"base": {"lorda_esc": lordo, "media_esc": netto, "media_recente_esc": rec,
                     "per_anno": anni or {"2011": 1, "2012": 1, "2013": 1, "2014": -1}},
            "costi_doppi": {"sharpe": sr2}, "vicini": {"rapporto": rapporto},
            "ingresso_spostato": {"meno_15": {"media_esc": sp}, "piu_15": {"media_esc": sp}},
            "gemello": {"media_esc": gem}}


def _misure(**kw):
    """Misure che passano tutti i filtri di Andrea (trade di 5 ore, 30 euro a trade)."""
    return {"euro_punto": 1.0, "n": 520, "trade_anno": 40.0, "guadagno_medio": 30.0, "ore_medie": 5.0, "r2": 0.9,
            "anni_positivi": 0.8, **kw}


FUORI_CAMPIONE_OK = {"avanti": {"n": 20, "utile": 100.0, "guadagno_medio": 25.0}}


def _colori(s, r, m="ok", pf="ok"):
    g = giudizio.giudica(s, r, _misure() if m == "ok" else m, FUORI_CAMPIONE_OK if pf == "ok" else pf)
    return g["esito"], {k: v["esito"] for k, v in g["gruppi"].items()}


def test_giudizio_soglie():
    esito, c = _colori(_scheda(), _rob())
    assert esito == "candidato" and c == {"caso": "verde", "costi": "verde", "regolarita": "verde",
                                          "robustezza": "verde", "rischio": "verde", "portafoglio": "grigio"}, c
    # caso: giallo se DSR >= 0,8 e PBO < 0,5; rosso sotto; il CPCV negativo toglie il verde
    assert _colori(_scheda(dsr=0.9), _rob())[1]["caso"] == "giallo"
    assert _colori(_scheda(pbo=0.3), _rob())[1]["caso"] == "giallo"
    assert _colori(_scheda(p10=-0.1), _rob())[1]["caso"] == "giallo"
    assert _colori(_scheda(dsr=0.7), _rob())[1]["caso"] == "rosso"
    assert _colori(_scheda(pbo=0.5), _rob())[1]["caso"] == "rosso"
    # costi: rapporto 3 e Sharpe doppio > 0 verde; rapporto 2 giallo; sotto rosso; costo doppio non basta
    assert _colori(_scheda(), _rob(lordo=0.03, netto=0.02))[1]["costi"] == "verde"          # rapporto 3
    assert _colori(_scheda(), _rob(lordo=0.03, netto=0.015))[1]["costi"] == "giallo"        # rapporto 2
    assert _colori(_scheda(), _rob(lordo=0.03, netto=0.02, sr2=-0.1))[1]["costi"] == "giallo"
    assert _colori(_scheda(), _rob(lordo=0.03, netto=0.0))[1]["costi"] == "rosso"           # rapporto 1
    # regolarità: tre voci, due su tre giallo
    assert _colori(_scheda(r2=0.5), _rob())[1]["regolarita"] == "giallo"
    assert _colori(_scheda(r2=0.5, qf=0.5), _rob())[1]["regolarita"] == "rosso"
    assert _colori(_scheda(), _rob(anni={"2011": 1, "2012": -1}))[1]["regolarita"] == "giallo"
    # robustezza: tutte verdi, metà verdi giallo, meno rosso; le voci mancanti non contano
    assert _colori(_scheda(), _rob(gem=-1))[1]["robustezza"] == "giallo"
    assert _colori(_scheda(senza=-1), _rob(gem=-1, rapporto=0.2))[1]["robustezza"] == "rosso"
    assert _colori(_scheda(), _rob(sp=-0.01))[1]["robustezza"] == "giallo"
    r = _rob()
    r["gemello"] = None
    r["ingresso_spostato"] = None
    assert _colori(_scheda(), r)[1]["robustezza"] == "verde"
    # rischio
    assert _colori(_scheda(rapporto_dd=1.5), _rob())[1]["rischio"] == "giallo"
    assert _colori(_scheda(z=2.5), _rob())[1]["rischio"] == "giallo"
    assert _colori(_scheda(rapporto_dd=1.7), _rob())[1]["rischio"] == "rosso"


def test_giudizio_esito_complessivo():
    # solo candidato o scartato: decidono filtri, cancello statistico e prova finale, non i colori dei gruppi
    assert _colori(_scheda(), _rob())[0] == "candidato"
    assert _colori(_scheda(dsr=0.5), _rob())[0] == "scartato"
    assert _colori(_scheda(dsr=0.9), _rob())[0] == "scartato"             # DSR giallo ma sotto 0,95
    assert _colori(_scheda(pbo=0.3), _rob())[0] == "scartato"
    # i gruppi restano il dettaglio: costi rossi o rischio rosso non cambiano l'esito
    esito, c = _colori(_scheda(), _rob(lordo=0.03, netto=0.0))
    assert esito == "candidato" and c["costi"] == "rosso", (esito, c)
    esito, c = _colori(_scheda(rapporto_dd=2.0), _rob())
    assert esito == "candidato" and c["rischio"] == "rosso", (esito, c)
    # dati mancanti: scartato, con il motivo, e tutti i gruppi grigi
    g = giudizio.giudica(None, None)
    assert g["esito"] == "scartato" and g["motivo"] == "misure non calcolate", g["motivo"]
    assert {x["esito"] for x in g["gruppi"].values()} == {"grigio"}
    assert _colori(None, None, m=_misure())[0] == "scartato"             # senza scheda il DSR manca
    g = giudizio.giudica(_scheda(), _rob(), _misure(), FUORI_CAMPIONE_OK)
    assert set(g) >= {"esito", "motivo", "filtri", "statistico", "prova_finale", "misure", "gruppi", "passa_scoperta"}
    for gr in g["gruppi"].values():
        assert {"esito", "voci", "nome", "cancello", "sintesi"} <= set(gr)
        for v in gr["voci"]:
            assert {"nome", "valore", "soglia", "esito", "spiegazione"} <= set(v) and v["spiegazione"]


# ---------------------------------------------------------------- ProRealCode

def _regola(nome):
    from .config import RADICE
    return json.loads((RADICE / "esperimenti" / "taratura" / nome).read_text(encoding="utf-8"))


def test_prorealcode_165_dax():
    t = uscita.traduci(_regola("165-dax-long.json"), "FDAX", 30)
    c = t["codice"]
    assert t["completo"] and not t["da_tradurre"]
    for pezzo in ("time = 133000 AND", "ExponentialAverage[25]", "G2 = RSI[2](close)", "G2 > 65", "dayofweek = 1 OR dayofweek = 2",
                  "time = 080000", "(dayofweek = 5 AND time = 210000)", "BUY PsL LOTS AT MARKET", "SELL AT MARKET",
                  "FOR i = 1 TO 20", "DHigh(i) - DLow(i)", "LONGONMARKET"):
        assert pezzo in c, pezzo
    assert not any(r.strip().upper().startswith("GRAPH") for r in c.splitlines())
    # la console di gestione è copiata riga per riga (salvo Aggressivita = 0 delle proposte)
    righe = [r for r in uscita.CONSOLE.read_text(encoding="utf-8").splitlines() if not r.startswith("Aggressivita")]
    resto = c
    for r in righe:
        k = resto.find(r)
        assert k >= 0, r
        resto = resto[k:]
    assert "Aggressivita        = 0" in c
    # short con una condizione "grezza": la versione long della grandezza anche sullo short
    s = uscita.traduci(_regola("165-dax-short.json"), "FDAX", 30)["codice"]
    assert "G2 = (DLow(1) - DLow(5)) / EscMedia" in s and "G2 <= 0" in s and "BarIndex - TradeIndex > 12" in s
    assert "SELLSHORT PsS LOTS AT MARKET" in s and "EXITSHORT AT MARKET" in s and "SHORTONMARKET" in s
    n = uscita.traduci(_regola("185-nq-short.json"), "NQ", 60)["codice"]
    assert "AverageTrueRange[20]" in n and "(DOpen(0) - close) / AverageTrueRange[20]" in n
    assert "CambiGiorno >= 4" in n and "time >= 160000 AND time <= 200000" in n
    # ogni famiglia del catalogo ha una traduzione
    assert set(uscita.TRADUZIONI) == set(uscita.condizioni.FAMIGLIE)


def test_prorealcode_stop_target_e_non_tradotto():
    base = {"lato": 1, "da": "09:00", "a": "09:00", "cond": [["rsi:2", "<", 10]],
            "uscita": {"barre": 3}, "stop": 1.5, "target": 2, "max_al_giorno": 2}
    t = uscita.traduci(base, "FDAX", 5)
    c = t["codice"]
    assert t["completo"] and "StopEsc = 1.5" in c and "TargetEsc = 2" in c and "MaxAlGiorno = 2" in c
    assert "SET STOP LOSS StopPunti" in c and "SET TARGET PROFIT TargetPunti" in c and "StopPunti = StopEsc * EscMedia" in c
    assert "BarIndex - TradeIndex > 3" in c
    # famiglia sconosciuta o pareggio: commento e completo False
    x = copy.deepcopy(base)
    x["cond"].append(["xyz:3", ">", 1])
    t = uscita.traduci(x, "FDAX", 5)
    assert not t["completo"] and "// DA TRADURRE" in t["codice"] and t["da_tradurre"], t
    p = copy.deepcopy(base)
    p["pareggio"] = {"attiva": 1, "a": 0.2}
    t = uscita.traduci(p, "FDAX", 5)
    assert not t["completo"] and "pareggio" in t["da_tradurre"] and "// DA TRADURRE: pareggio" in t["codice"]
    assert uscita.prorealcode(base, "FDAX", 5) == uscita.traduci(base, "FDAX", 5)["codice"]


# ---------------------------------------------------------------- arricchimento

def test_arricchisci():
    with _ambiente() as tmp:
        r0 = _lancia(tmp)
        prove0 = len(validazione._righe())
        r = esperimento.arricchisci("prova")
        assert len(validazione._righe()) == prove0 == 6       # il registro non si tocca
        cart = esperimento.CARTELLA / "prova" / "candidati"
        for riga in r["candidati"]:
            i = riga["id"]
            c = json.loads((cart / f"{i}.json").read_text(encoding="utf-8"))
            assert {"robustezza", "giudizio", "prorealcode"} <= set(c), c.keys()
            assert (cart / f"{i}.prc").read_text(encoding="utf-8") == c["prorealcode"]["codice"]
            assert riga["esito"] == c["giudizio"]["esito"] and riga["esito"] in ("candidato", "scartato")
            assert riga["motivo"] == c["giudizio"]["motivo"] and riga["misure"]["n"] == c["misure"]["n"]
            assert riga["gruppi"] == {k: g["esito"] for k, g in c["giudizio"]["gruppi"].items()}
            assert set(riga["gruppi"]) == {"caso", "costi", "regolarita", "robustezza", "rischio", "portafoglio"}
            assert c["robustezza"]["vicini"] is not None and c["robustezza"]["euro"]["euro_punto"] == 2.0
        import polars as pl
        t = pl.read_parquet(cart / "c01_trade.parquet")
        assert "punti" in t.columns and t.height == r0["candidati"][0]["n"]
        # il riassunto salvato contiene l'esito e si può rileggere
        assert esperimento.riassunto("prova")["candidati"][0]["esito"] == r["candidati"][0]["esito"]
        # l'esito scritto nel riassunto è quello calcolato dal giudizio, qualunque sia
        vero = giudizio.giudica
        giudizio.giudica = lambda s, r, *a: {**vero(s, r, *a), "esito": "scartato"}
        try:
            r2 = esperimento.arricchisci("prova")
        finally:
            giudizio.giudica = vero
        assert {x["esito"] for x in r2["candidati"]} == {"scartato"}
        assert json.loads((cart / "c01.json").read_text(encoding="utf-8"))["giudizio"]["esito"] == "scartato"
        r = esperimento.arricchisci("prova")
        # il vantaggio è seminato: la scheda lo vede e il giudizio dei costi è verde
        assert r["candidati"][0]["gruppi"]["costi"] == "verde", r["candidati"][0]


if __name__ == "__main__":
    for f in (test_robustezza_coerente, test_vicini_dal_registro, test_giudizio_soglie,
              test_giudizio_esito_complessivo, test_prorealcode_165_dax, test_prorealcode_stop_target_e_non_tradotto,
              test_arricchisci):
        f()
        print("ok", f.__name__)
