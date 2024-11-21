# UNIPI-GatchaAndGames
Progetto per il corso di Secure Software Engineering del Corso di Cybersecurity dell'Università di Pisa.

## Come eseguire il progetto (senza just)
Per inizializzare il progetto:
```bash
docker compose build
```

Per avviare i servizi:
```
docker compose up
```

Per stoppare i servizi:
```bash
docker compose stop
```

Per rimuovere tutti i servizi (e riportare il database allo stato originale):
```bash
docker compose down -v
```


## Come eseguire il progetto (con just)
Per inizializzare e avviare il progetto:
```bash
just start
```

Per avviare i servizi:
```
just up
```

Per stoppare i servizi:
```bash
just stop
```

Per rimuovere tutti i servizi (e riportare il database allo stato originale):
```bash
just down
```

Per collegarsi al database:
```bash
just db
```

Per vedere i log di un particolare servizio:
```bash
just logs <nome_servizio>
```

# Links utili

- [Come usare Git](https://nvie.com/posts/a-successful-git-branching-model/)
- [Convenzione dei commit](https://www.conventionalcommits.org/en/v1.0.0/)