"""Prova finale fuori campione: i due holdout si guardano una volta sola, a selezione finita.

Si fa solo per i sistemi che hanno già passato tutti i filtri e il cancello statistico sulla scoperta (al massimo
`k` per esperimento) e una sola volta per tentativo del registro: il risultato resta scritto nel campo
`holdout_usato` della sua riga, e una seconda chiamata lo restituisce senza leggere un solo dato.

Rifà `backtest.simula` (al minuto) con la stessa regola sullo stesso prodotto, sui tre periodi di `config`:
`HOLDOUT_AVANTI` (2024 → fine dei dati), `HOLDOUT_VICINO` (2011-2013) e `HOLDOUT_ANTICO` (inizio dei dati → 2010, se
ci sono). Il lettore dei dati taglia al 2025-11-21 (`config.TAGLIO`); i dati attuali finiscono a maggio 2025. Pesi
diversi in `giudizio.prova_finale_voci`: il periodo in avanti decide, gli altri due scartano solo in casi gravi.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

from . import catalogo, dati, giudizio, validazione
from .config import HOLDOUT_ANTICO, HOLDOUT_AVANTI, HOLDOUT_VICINO
from .motori import backtest, eventi


def _periodo(prodotto: str, barre: int, regola: dict, anni: tuple, m1: pl.DataFrame):
    """(misure, serie giornaliera in punti netti) di un periodo; None se nel periodo non ci sono barre."""
    tab = eventi.base(prodotto, barre, anni)
    if not tab.height:
        return None
    dati.controlla_taglio(tab)
    _, trade = backtest.simula(prodotto, barre, regola, tab, m1, anni=anni)
    date = tab["data"].unique().sort().to_numpy().astype("datetime64[D]")
    ep = catalogo.prodotto(prodotto).euro_punto
    primo, ultimo = (int(date[i].astype("datetime64[Y]").astype(int)) + 1970 for i in (0, -1))
    m = giudizio.misure(trade, date, ep, tab.height, (primo, ultimo))
    giorno = np.minimum(np.searchsorted(date, trade["uscita"].dt.date().to_numpy().astype("datetime64[D]")), len(date) - 1)
    serie = np.bincount(giorno, weights=trade["punti"].to_numpy(), minlength=len(date))
    netto = np.bincount(giorno, weights=trade["netto"].to_numpy(), minlength=len(date))
    ris = {"da": str(date[0]), "a": str(date[-1]), "n": m["n"], "utile": m["utile"], "guadagno_medio": m["guadagno_medio"],
           "drawdown": m["drawdown"], "ore_medie": m["ore_medie"], "euro_punto": ep,
           "media_esc": m["media_esc"], "dd_esc": m["dd_esc"]}
    return ris, pl.DataFrame({"data": date, "punti": serie, "netto": netto}).with_columns(pl.col("data").cast(pl.Date))


def esegui(prodotto: str, barre: int, regola: dict, id_registro: str, salva_in: Path | None = None) -> dict:
    """Esegue la prova finale del tentativo `id_registro` e la segna nel registro. Restituisce
    `{"avanti": {...}, "vicino": {...}, "antico": {...}, "quando": ..., "gia_usata": bool}` (None dove non ci sono dati).

    Se il tentativo l'ha già consumata restituisce il risultato salvato (`gia_usata` vero) senza leggere dati.
    Con `salva_in` (un file .parquet) salva le serie giornaliere dei periodi, colonne `data`, `periodo`
    (`antico`, `vicino` o `avanti`), `punti` (netti, in punti di prezzo) e `netto` (in escursioni medie)."""
    usata = validazione.holdout_usato(id_registro)
    if usata:
        return {**usata["risultato"], "quando": usata["quando"], "gia_usata": True}
    m1 = dati.minuti(prodotto)
    periodi = {nome: _periodo(prodotto, barre, regola, anni, m1)
               for nome, anni in (("antico", HOLDOUT_ANTICO), ("vicino", HOLDOUT_VICINO), ("avanti", HOLDOUT_AVANTI))}
    risultato = {nome: x[0] if x else None for nome, x in periodi.items()}
    quando = datetime.now(timezone.utc).isoformat(timespec="seconds")
    validazione.segna_holdout(id_registro, {"quando": quando, "risultato": risultato})
    if salva_in is not None:
        parti = [x[1].with_columns(pl.lit(nome).alias("periodo")).select("data", "periodo", "punti", "netto")
                 for nome, x in periodi.items() if x]
        if parti:
            Path(salva_in).parent.mkdir(parents=True, exist_ok=True)
            pl.concat(parti).write_parquet(salva_in)
    return {**risultato, "quando": quando, "gia_usata": False}
