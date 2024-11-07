# UNIPI-GatchaAndGames
Progetto per il corso di Secure Software Engineering del Corso di Cybersecurity dell'Università di Pisa.

## Per installarlo nel proprio computer (esegui i seguenti comandi in ordine)
Posizionati nella cartella del progetto (UNIPI-GachaAndGames):
```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python3 -m openapi_server
```

Una volta installato ed avviato esegui questo comando per aprire la UI:
```
http://localhost:8080/ui/
```

La definizione OpenAPI sta qui:
```
http://localhost:8080/openapi.json
```

Per lanciare gli integration test esegui:
```
tox
```


## Esecuzione con Docker (non usare, per ora)
Posizionati nella cartella del progetto (UNIPI-GachaAndGames):

```bash
# costruzione immagine
docker build -t openapi_server .
```

```bash
# avvio del container
docker run -p 8080:8080 openapi_server
```