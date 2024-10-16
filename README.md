# UNIPI-GatchaAndGames
Progetto per il corso di Secure Software Engineering del Corso di Cybersecurity dell'Università di Pisa.

## Per installarlo nel proprio computer (esegui i seguenti comandi in ordine)
Posizionati nella cartella "app" ed esegui:

python3 -m venv .venv
source .venv/bin/activate
sudo apt update
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config
pip3 install -r ../requirements.txt


## Per installare MySQL server (esegui i seguenti comandi in ordine)
Posizionati nella cartella "app" ed esegui:

sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql.service

sudo mysql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root';
exit

sudo mysql_secure_installation
n
y
y
y
y

mysql -u root -p < setup_db.sql
mysql -u root -p < setup_user.sql

### D'ora in poi per accedere a MySQL fare:
mysql -u root -p

... e inserire la password impostata prima.

## Prepara l'ambiente Flask
export FLASK_APP=app.py
export FLASK_ENV=development

## Per eseguire il server Flask
Posizionati nella cartella "app" ed esegui:
flask --debug run