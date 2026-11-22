"""Costanti del motore di ricerca. Il taglio del fuori campione sta SOLO qui."""
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
DATI_1M = RADICE / "Dati" / "1m-20261121T225950Z-1-001" / "1m"
CACHE = RADICE / "Dati" / "_cache"

# Fuori campione di Andrea: l'ultimo anno prima di oggi (verificato su ProRealTime).
# Nessuna riga con ts >= TAGLIO arriva mai in memoria. Spostarlo solo su indicazione di Andrea.
TAGLIO = datetime(2025, 11, 21, tzinfo=timezone.utc)

FUSO = "Europe/Rome"  # tutte le logiche ragionano in ora italiana, come i sistemi ProRealTime

# Periodi della validazione interna (anni interi, ora italiana). La scoperta usa solo SCOPERTA;
# gli holdout si guardano una volta per albero, a selezione finita, e mai dai comandi di esplorazione.
# Andrea (2026-11-22): in-sample 2014-2023, perché il mercato cambia e il fuori campione recente conta di più.
# Pesi dei tre fuori campione in `giudizio.py`: in avanti decide, 2011-2013 scarta se il sistema perde o va male
# in modo disastroso, prima del 2011 solo se va in modo disastroso.
SCOPERTA = (2014, 2023)
HOLDOUT_AVANTI = (2024, 2025)
HOLDOUT_VICINO = (2011, 2013)
HOLDOUT_ANTICO = (None, 2010)
HOLDOUT_INDIETRO = (None, 2013)   # i due all'indietro insieme (vicino + antico), per chi li legge in un colpo
RECENTE = (2019, 2023)            # controllo di attualità, dentro la scoperta
WF_PRIMO_ANNO = 2017              # walk-forward della procedura: primo anno di prova (3 anni di ricerca minimi)
RISULTATI = RADICE / "risultati"
