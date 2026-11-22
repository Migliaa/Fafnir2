"""Comandi per l'IA. Ogni comando stampa un riassunto JSON compatto su stdout.

Uso (dalla cartella del progetto):
  python -m motore.cli catalogo
  python -m motore.cli mappa calcola AUDJPY --barre 60 --ore 72
  python -m motore.cli mappa migliori AUDJPY --barre 60 --k 10
  python -m motore.cli mappa cella AUDJPY --barre 60 --giorno lun --ora 03:00 --durata 67
  python -m motore.cli eventi FDAX esperimenti/regola.json --barre 30 --specchio
  python -m motore.cli minbtl --sr 0.7 --anni 13 [--prove 50]
  python -m motore.cli registro stato [--famiglia X]
  python -m motore.cli backtest FDAX esperimenti/regola.json --barre 30
  python -m motore.cli esperimento controlla|lancia|riassunto|arricchisci <file.json | nome>
"""
from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

from . import catalogo, condizioni, esperimento, metriche, validazione
from .motori import backtest, eventi, mappa


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="motore.cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("catalogo")
    m = sub.add_parser("mappa")
    m.add_argument("azione", choices=["calcola", "migliori", "cella"])
    m.add_argument("prodotto")
    m.add_argument("--barre", type=int, default=60)
    m.add_argument("--ore", type=int, default=72, help="durata massima (calcola)")
    m.add_argument("--k", type=int, default=10)
    m.add_argument("--lati", default="LS")
    m.add_argument("--giorno")
    m.add_argument("--ora")
    m.add_argument("--durata", type=float, help="ore")
    b = sub.add_parser("minbtl", help="prove ammesse e anni necessari (Bailey et al. 2014)")
    b.add_argument("--sr", type=float, required=True, help="Sharpe annuo da certificare")
    b.add_argument("--anni", type=float, required=True, help="anni di dati della scoperta")
    b.add_argument("--prove", type=int, help="numero di prove per cui calcolare gli anni necessari")
    r = sub.add_parser("registro")
    r.add_argument("azione", choices=["stato"])
    r.add_argument("--famiglia")
    e = sub.add_parser("eventi", help="prova una regola (JSON in riga o file .json)")
    e.add_argument("prodotto")
    e.add_argument("regola")
    e.add_argument("--barre", type=int, default=60)
    e.add_argument("--specchio", action="store_true", help="prova anche la regola speculare")
    t = sub.add_parser("backtest", help="regola con stop, target e pareggio controllati sui minuti")
    t.add_argument("prodotto")
    t.add_argument("regola")
    t.add_argument("--barre", type=int, default=60)
    x = sub.add_parser("esperimento", help="controlla o lancia un file d'esperimento, o ne stampa il riassunto")
    x.add_argument("azione", choices=["controlla", "lancia", "riassunto", "arricchisci"])
    x.add_argument("bersaglio", help="file .json (controlla, lancia) o nome dell'esperimento (riassunto, arricchisci)")
    a = p.parse_args(argv)

    if a.cmd == "eventi":
        testo = Path(a.regola).read_text(encoding="utf-8") if a.regola.endswith(".json") else a.regola
        regola = json.loads(testo)
        tab = eventi.base(a.prodotto, a.barre)
        out = {"regola": eventi.prova(a.prodotto, a.barre, regola, tab)[0]}
        if a.specchio:
            out["specchio"] = eventi.prova(a.prodotto, a.barre, condizioni.specchia(regola), tab)[0]
    elif a.cmd == "backtest":
        testo = Path(a.regola).read_text(encoding="utf-8") if a.regola.endswith(".json") else a.regola
        out = {"regola": backtest.simula(a.prodotto, a.barre, json.loads(testo))[0]}
    elif a.cmd == "esperimento":
        if a.azione == "controlla":
            out = esperimento.controlla(a.bersaglio)
        elif a.azione == "lancia":
            out = esperimento.lancia(a.bersaglio)
        elif a.azione == "arricchisci":
            r = esperimento.arricchisci(a.bersaglio)
            out = {"esperimento": a.bersaglio, "candidati": [
                {"id": c["id"], "esito": c["esito"], "gruppi": c["gruppi"], "netto_euro": c.get("netto_euro")}
                for c in r["candidati"]]}
        else:
            out = esperimento.riassunto(a.bersaglio)
    elif a.cmd == "catalogo":
        out = catalogo.riassunto()
    elif a.cmd == "minbtl":
        prove = [a.prove] if a.prove else [10, 20, 50, 100, 400]
        out = {"sr": a.sr, "anni": a.anni, "prove_ammesse": round(metriche.prove_ammesse(a.anni, a.sr), 1),
               "anni_necessari": {str(n): round(metriche.min_btl(n, a.sr), 2) for n in prove}}
    elif a.cmd == "registro":
        out = validazione.conteggio(a.famiglia)
    elif a.azione == "calcola":
        out = mappa.calcola(a.prodotto, a.barre, a.ore)
    elif a.azione == "migliori":
        out = mappa.migliori(a.prodotto, a.barre, a.k, a.lati)
    else:
        out = mappa.cella(a.prodotto, a.barre, a.giorno, a.ora, a.durata)
    json.dump(out, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    print()


if __name__ == "__main__":
    main()
