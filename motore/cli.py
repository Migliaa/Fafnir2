"""Comandi per l'IA. Ogni comando stampa un riassunto JSON compatto su stdout.

Uso (dalla cartella del progetto):
  python -m motore.cli catalogo
  python -m motore.cli mappa calcola AUDJPY --barre 60 --ore 72
  python -m motore.cli mappa migliori AUDJPY --barre 60 --k 10
  python -m motore.cli mappa cella AUDJPY --barre 60 --giorno lun --ora 03:00 --durata 67
"""
from __future__ import annotations

import argparse
import json
import sys

from . import catalogo
from .motori import mappa


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
    a = p.parse_args(argv)

    if a.cmd == "catalogo":
        out = catalogo.riassunto()
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
