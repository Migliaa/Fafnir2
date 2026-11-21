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
