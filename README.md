# UNIPI-GachaAndGames

Il progetto **UNIPI-GachaAndGames** è un sistema Gacha sviluppato per il corso di Secure Software Engineering all'Università di Pisa. Il sistema utilizza un'architettura a microservizi, dove ogni servizio gestisce una specifica funzionalità dell'applicazione.

## File e Directory Principali

- **docker-compose.yml**: Orchestrazione dei container Docker per i vari servizi.
- **gachaandgames_complete.yaml**: Specifica OpenAPI completa dell'intero sistema.
- **README.md**: Documentazione generale del progetto con istruzioni per l'installazione e l'esecuzione.
- **setup.py**, **test-requirements.txt**, **tox.ini**: File di configurazione per la gestione del progetto e dei test.
- **api_gateway**: Contiene la configurazione per l'API Gateway basato su Nginx.
  - **api_gateway.conf**: File di configurazione Nginx che instrada le richieste ai vari servizi.

### Esempio di configurazione in `api_gateway.conf`:

```nginx
events {}

http {
    upstream service_profile {
        least_conn;
        server service_profile:8080 max_fails=3 fail_timeout=10s;
    }

    # Configurazione di altri servizi...

    server {
        listen 80;

        location /profile/ {
            proxy_pass http://service_profile;
        }

        # Altre location per gli altri servizi...
    }
}
```

## Database

- **database**: Contiene tutto il necessario per il database MySQL.
  - **db.env**: Variabili d'ambiente per la configurazione del database.
  - **Dockerfile**: Dockerfile per creare l'immagine Docker del database.
  - **init.sql**: Script SQL per l'inizializzazione dello schema del database.
  - **mock_data.sql**: Script SQL per popolare il database con dati di test.

## DB Manager

- **db_manager**: Servizio che gestisce le interazioni dirette con il database.
  - **.env**: Variabili d'ambiente per la configurazione del servizio.
  - **openapi_server/**: Codice sorgente del servizio.

## Servizi

I servizi sono organizzati nella directory **services**, ognuno con la propria directory dedicata:

- **admin/**: Funzionalità amministrative.
- **auth/**: Gestione dell'autenticazione degli utenti.
- **profile/**: Gestione dei profili utente.
- **gacha/**: Meccaniche del gioco Gacha.
- **inventory/**: Gestione degli inventari degli utenti.
- **auctions/**: Gestione delle aste tra utenti.
- **currency/**: Gestione della valuta di gioco.
- **pvp/**: Funzionalità Player vs Player.
- **feedback/**: Raccolta dei feedback dagli utenti.

Ogni servizio contiene:

- **Dockerfile**: Per la containerizzazione del servizio.
- **requirements.txt**: Elenco delle dipendenze Python.
- **openapi_server/**: Codice sorgente specifico del servizio, strutturato come segue:
  - **__main__.py**: Punto di ingresso dell'applicazione Flask. Qui viene creata l'istanza dell'applicazione, configurato il server e vengono registrate le blueprint dei controller.
  - **controllers/**: Contiene i controller che gestiscono le richieste HTTP in arrivo. Ogni controller è responsabile di una specifica parte delle API e definisce le funzioni che vengono chiamate in risposta alle varie rotte definite.
    - Esempio: `auth_controller.py`, `profile_controller.py`.
    - All'interno dei controller si gestiscono le logiche di business, si interagisce con i modelli e si preparano le risposte da inviare al client.
  - **models/**: Definisce le classi dei modelli dati utilizzati nell'applicazione. Questi modelli rappresentano le strutture dati che vengono scambiate tra client e server, e sono basati sulle specifiche definite nel file OpenAPI.
    - Esempio: `user.py`, `item.py`.
  - **openapi/**: Contiene il file `openapi.yaml` che definisce le specifiche delle API per il servizio. Questo file descrive le rotte disponibili, i parametri accettati, le risposte possibili e gli schemi dei dati.
  - **__init__.py**: Indica a Python che la directory è un pacchetto Python.
- **.gitignore**, **.dockerignore**, **.openapi-generator-ignore**: File per specificare esclusioni nel controllo di versione, build Docker e generazione del codice.

## Gestione delle Dipendenze e Build

- **setup.py**: Script di setup per l'installazione dei pacchetti Python.
- **test-requirements.txt**: Elenco delle dipendenze necessarie per eseguire i test.
- **tox.ini**: Configurazione per il tool di test Tox.

## Installazione ed Esecuzione

### Esecuzione con Docker

Costruire le immagini Docker:

```bash
docker compose build
```

Avviare i container Docker:

```bash
docker compose up
```

## Dettagli Tecnici Aggiuntivi

### Servizio `auth`

Nella funzione `login` nel file `auth_controller.py`, dopo aver verificato le credenziali dell'utente, l'UUID viene salvato nella sessione:

```python
session['uuid'] = data["uuid"]
```

### Configurazioni Nginx

Il file `api_gateway.conf` gestisce l'indirizzamento delle richieste ai servizi appropriati, utilizzando blocchi `upstream` e `location` per ciascun servizio.

### Esecuzione dei Test

Per eseguire i test, utilizzare il comando:

```bash
tox
```

## Note per la consegna del 22/11/2024

1. Pvp è stato temporaneamente disattivato, a causa della mancata conformità con le specifiche richieste (Work in progress)
2. I test sono principalmente integration tests eseguiti con postman, il cui json si trova, come richiesto, nella cartella docs. Attualmente non coprono ogni test case, ma almeno il codice 200 per ogni metodo di ogni microservizio. Gli unit tests insieme al performance testing saranno consegnati successivamente.
3. Per fare i test si possono usare i seguenti admin: (username= SpeedwagonAdmin password=admin_foundation ; username = AdminUser password= password). Purtroppo non abbiamo implementato ancora un metodo per registrarsi come admin.

