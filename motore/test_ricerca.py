"""Ricerca a cicli: motore a matrice uguale al motore degli eventi, statistiche per anno, test dei filtri a caso,
cicli di moltiplicazione e filtro, lancio. Uso: python -m motore.test_ricerca"""
import json
import math

import numpy as np

from . import albero as A
from . import pattern, ricerca as R, validazione
from .motori import matrice as MX
from .test_esperimento import _Ambiente

USCITE = [{"nome": "una barra", "barre": 0}, {"nome": "due barre", "barre": 1}, {"nome": "alle 15", "ora": "15:00"}, {"nome": "domani", "giorni": 1}]


def _contesto():
    vecchio = A.SCOPERTA
    A.SCOPERTA = (2014, 2016)
    try:
        return A.Contesto("KW", 60)
    finally:
        A.SCOPERTA = vecchio


def test_matrice_uguale_al_motore_degli_eventi():
    with _Ambiente():
        ctx = _contesto()
        conds = [p[3] for p in pattern.PATTERN]
        mx = MX.Matrice(ctx, MX.orari("09:00", "14:00", 60), USCITE, conds)
        provate = 0
        for t in ("09:00", "11:00", "14:00"):
            for k in range(len(USCITE)):
                for ci in (None, 0, 32, 40):
                    m = np.ones(mx.maschere[t].shape[0], bool) if ci is None else mx.maschere[t][:, ci]
                    ag = mx.aggregati(t, k, m[:, None])
                    reg = {"lato": 1, "da": t, "a": t, "cond": [] if ci is None else [conds[ci]],
                           "uscita": {a: b for a, b in USCITE[k].items() if a != "nome"}, "max_al_giorno": 1}
                    tr = ctx.trade(reg)
                    assert int(ag["n"].sum()) == tr.height, (t, k, ci, ag["n"].sum(), tr.height)
                    if tr.height:
                        assert abs(ag["s"].sum() - tr["netto"].sum()) < 1e-6, (t, k, ci)
                        assert abs(ag["h"][0] / tr.height - ((tr["uscita"] - tr["ingresso"]).dt.total_seconds().mean() / 3600)) < 1e-6
                        assert np.allclose(mx.serie(t, k, m), ctx.giornaliera(tr))
                    provate += 1
        assert provate == 48


def test_statistiche_per_anno():
    rng = np.random.default_rng(0)
    anni, regole = 10, 3
    x = [rng.normal(0.1 * (j + 1), 1, (anni, 30)) for j in range(regole)]       # 30 trade l'anno
    ag = {"n": np.full((anni, regole), 30.0), "s": np.column_stack([xi.sum(1) for xi in x]),
          "q": np.column_stack([(xi ** 2).sum(1) for xi in x]), "h": np.full(regole, 30.0 * anni * 4), "l": np.zeros(regole)}
    st = MX.statistiche(ag, 100.0, anni)
    tutti = [xi.ravel() for xi in x]
    for j in range(regole):
        assert abs(st["media"][j] - tutti[j].mean()) < 1e-12 and abs(st["sd"][j] - tutti[j].std(ddof=1)) < 1e-9
        assert abs(st["t"][j] - tutti[j].mean() / tutti[j].std(ddof=1) * math.sqrt(300)) < 1e-9
        # CPCV: mediana delle medie sulle 45 coppie di anni
        oos = [x[j][[a, b]].mean() for a in range(anni) for b in range(a + 1, anni)]
        assert abs(st["cpcv"][j] - np.median(oos)) < 1e-12
        assert abs(st["meta1"][j] - x[j][:5].mean()) < 1e-12 and abs(st["meta2"][j] - x[j][5:].mean()) < 1e-12
    # 4 ore a trade: soglia 20 euro; G e M come rapporti
    assert np.allclose(st["richiesto"], 20) and np.allclose(st["G"], st["media"] * 100 / 20) and np.allclose(st["M"], st["G"] * 30 / 12)
    # con la maschera degli anni conta solo quello che c'è dentro
    mk = np.zeros(anni, bool)
    mk[:3] = True
    s3 = MX.statistiche(ag, 100.0, anni, mk)
    assert abs(s3["media"][0] - x[0][:3].mean()) < 1e-12 and s3["trade_anno"][0] == 30


def test_quantile_dei_filtri_a_caso():
    rng = np.random.default_rng(1)
    padre = rng.normal(0, 1, 2000)
    for k, spinta in ((200, 0.0), (500, 0.08), (300, 0.2)):
        idx = np.argsort(padre + rng.normal(0, 1 / max(spinta, 1e-9) if spinta else 1e9, 2000))[-k:] if spinta else rng.choice(2000, k, replace=False)
        figlio = padre[idx]
        q = MX.quantile_filtro(np.array([k]), np.array([figlio.mean()]), 2000, padre.mean(), padre.var(ddof=1))[0]
        perm = np.array([padre[rng.choice(2000, k, replace=False)].mean() for _ in range(3000)])
        empirico = (perm < figlio.mean()).mean()
        assert abs(q - empirico) < 0.03, (k, spinta, q, empirico)


def test_cicli_moltiplicano_e_filtrano():
    with _Ambiente():
        ctx = _contesto()
        mx = MX.Matrice(ctx, MX.orari("08:00", "14:00", 60), USCITE, [p[3] for p in pattern.PATTERN])
        vecchi = (R.M_MIN, R.T_MIN)
        try:
            cfg = {"semi_1": 5, "semi_2": 4, "finali": 3, "margine_semi": 0.0, "correlazione_semi": 0.9, "correlazione_max": 0.7}
            c = R.Cicli(mx, cfg, log=lambda *a: None)
            n = c.forza_bruta()
            assert n == 7 * 4 * (1 + len(pattern.dello_strato(1)))
            g = c.giro()
            p = {x["strato"]: x for x in g["passi"]}
            assert g["provate"] == p["forza"]["n"] + p["molt1"]["n"] + p["molt2"]["n"]
            assert len(g["semi1"]) <= 5 and len(g["semi2"]) <= 4 and len(g["finali"]) <= 3
            # i figli della moltiplicazione 1 hanno un pattern in più del loro seme e di un'altra famiglia
            assert p["molt1"]["n"] > 0 and all(len(s["conds"]) <= 3 for s in g["finali"])
            # i finali sono diversi fra loro
            serie = [c._serie(f["ti"], f["k"], f["conds"]) for f in g["finali"]]
            for i in range(len(serie)):
                for j in range(i):
                    assert abs(np.corrcoef(serie[i], serie[j])[0, 1]) <= 0.7 + 1e-9
            # ogni finale passa le porte comuni
            for f in g["finali"]:
                assert f["trade_anno"] >= R.TRADE_ANNO_MIN and f["t"] >= R.T_MIN and f["cpcv"] > 0
            # con un solo anno di ricerca la CPCV non ha coppie di anni: nessuna regola passa e il giro finisce vuoto
            g1 = c.giro(np.array([True, False, False]))
            assert g1["finali"] == [] and g1["provate"] == p["forza"]["n"]
        finally:
            R.M_MIN, R.T_MIN = vecchi


def test_lancio_scrive_la_fisarmonica_e_non_si_ripete():
    with _Ambiente() as tmp:
        A.CARTELLA = tmp / "ricerche"
        vecchi = (A.SCOPERTA, R.WF_PRIMO_ANNO)
        A.SCOPERTA, R.WF_PRIMO_ANNO = (2014, 2016), 2015
        try:
            spec = {"tipo": "cicli", "nome": "prova-cicli", "ipotesi": "x", "meccanismo": "y", "fonte": "z", "prodotto": "KW", "barre": 60,
                    "forza_bruta": {"orari": {"da": "08:00", "a": "12:00", "passo": 60}, "uscite": USCITE[:2]},
                    "cicli": {"semi_1": 3, "semi_2": 2, "finali": 2, "margine_semi": 0.0}, "uscite_finali": []}
            f = tmp / "c.json"
            f.write_text(json.dumps(spec), encoding="utf-8")
            assert R.controlla(f)["ok"] and R.controlla(f)["prove_forza_bruta"] == 5 * 2 * (1 + len(pattern.dello_strato(1)))
            r = R.lancia(f, log=lambda *a: None)
            strati = [x["strato"] for x in r["imbuto"]]
            assert strati[:6] == ["forza", "filtro1", "molt1", "filtro2", "molt2", "filtro3"], strati
            assert r["prove"] >= r["imbuto"][0]["n"] and r["effettive"]["effettive"] >= 1
            assert len(r["walkforward_ricerca"]["anni"]) == 2          # 2015 e 2016: il primo anno serve da ricerca
            # nel 2015 la ricerca vede solo il 2014: un anno solo non dà coppie per la CPCV, quindi nessun finale e nessun
            # trade; se vedesse anche il 2015 (il futuro) qualcosa passerebbe
            assert r["walkforward_ricerca"]["anni"][0]["n"] == 0, r["walkforward_ricerca"]
            salvato = json.loads((tmp / "ricerche" / "prova-cicli" / "ricerca.json").read_text(encoding="utf-8"))
            assert salvato["cicli"] and len(salvato["pattern"]) == len(pattern.PATTERN)
            assert json.loads((tmp / "ricerche" / "prova-cicli" / "stato.json").read_text(encoding="utf-8"))["stato"] == "finita"
            assert any(x["famiglia"] == "ricerca:prova-cicli" for x in validazione._righe()) or not r["nodi"]
            try:
                R.lancia(f, log=lambda *a: None)
            except ValueError as ex:
                assert "già lanciata" in str(ex)
            else:
                raise AssertionError("ricerca rilanciata")
        finally:
            A.SCOPERTA, R.WF_PRIMO_ANNO = vecchi


def test_libreria_dei_pattern():
    nomi = [p[0] for p in pattern.PATTERN]
    assert len(nomi) == len(set(nomi))
    assert {p[2] for p in pattern.PATTERN} == {1, 2, 3}
    for p in pattern.PATTERN:
        assert p[3][1] in (">", ">=", "<", "<=", "==") and not str(p[3][0]).startswith("ptn")
    # nessuna soglia in % del prezzo: le grandezze sono in escursioni o rapporti
    assert pattern.nome(["gap", ">=", 0.25]) == "gap in su di almeno 0,25 escursioni"


def test_rumore_slega_le_condizioni():
    with _Ambiente():
        ctx = _contesto()
        mx = MX.Matrice(ctx, MX.orari("08:00", "12:00", 60), USCITE, [p[3] for p in pattern.PATTERN])
        t = "10:00"
        assert np.array_equal(mx.spostata(0).maschere[t], mx.maschere[t])
        sp = mx.spostata(300)
        g = mx.giorno_riga[t]
        nd = len(ctx.date)
        pos = {d: i for i, d in enumerate(g)}
        for r in range(0, len(g), 37):                                  # ogni giorno prende le condizioni di 300 giorni dopo
            src = pos.get((g[r] + 300) % nd)
            atteso = mx.maschere[t][src] if src is not None else np.zeros(mx.maschere[t].shape[1], bool)
            assert np.array_equal(sp.maschere[t][r], atteso)
        assert sp.trade is mx.trade                                     # i risultati restano quelli veri
        c = R.Cicli(mx, {"semi_1": 3, "semi_2": 2, "finali": 2, "margine_semi": 0.0}, log=lambda *a: None)
        c.forza_bruta()
        rum = c.rumore(3, seme=1)
        assert len(rum["giri"]) == 3 and all(g_["passo"] >= 260 or nd < 521 for g_ in rum["giri"])
        # p = (1 + giri con un migliore >= punteggio) / (1 + giri)
        finto = {"giri": [{"migliore": 0.5}, {"migliore": 1.5}, {"migliore": 2.5}, {"migliore": 0.0}]}
        assert R.p_rumore(3.0, finto) == 1 / 5 and R.p_rumore(1.0, finto) == 3 / 5 and R.p_rumore(0.0, finto) == 1.0


def test_nomi_speculari_per_lo_short():
    assert pattern.nome(["gap", ">=", 0.25], -1) == "gap in giù di almeno 0,25 escursioni"
    assert pattern.nome(["rsi:2", "<=", 10], -1) == "RSI 2 sopra 90"
    assert pattern.nome(["adx:14", ">=", 25], -1) == "ADX 14 sopra 25 (tendenza)"        # uguale per i due lati
    assert pattern.nome(["apertura_in_ieri", ">=", 1], -1) == "apre sotto il minimo di ieri"


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok", nome)
