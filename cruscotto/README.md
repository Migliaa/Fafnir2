# Cruscotto

Dalla cartella del progetto: `python -m cruscotto` (oppure doppio clic su `cruscotto/avvia.bat`) avvia il server su `http://127.0.0.1:8765` e apre il browser; si ferma con Ctrl+C.
Legge `risultati/` e `esperimenti/`; l'unica scrittura è `risultati/cruscotto/decisioni.json` (stato, nota e verifica ProRealTime di ogni sistema).
Funziona senza internet; i dati di un esperimento nuovo compaiono dopo `python -m motore.cli esperimento arricchisci <nome>`; il commento dell'IA si legge da `risultati/esperimenti/<nome>/commenti/<id>.md` (in testa, facoltativo, un blocco `---` con righe `data: ...` e `modello: ...`).
