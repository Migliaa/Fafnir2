"""Avvio: python -m cruscotto [--porta 8765] [--no-browser]"""
import argparse

from .server import PORTA, avvia

p = argparse.ArgumentParser(prog="cruscotto")
p.add_argument("--porta", type=int, default=PORTA)
p.add_argument("--no-browser", action="store_true", help="non aprire il browser")
p.add_argument("--riavvio", action="store_true", help="uso interno: riavvio automatico dopo un cambiamento del codice")
a = p.parse_args()
avvia(a.porta, apri=not a.no_browser, riavvio=a.riavvio)
