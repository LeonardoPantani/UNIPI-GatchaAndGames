(crea ed entra nella cartella "GachaAndGames-Certs"...)


# Genera una chiave privata per la CA radice
openssl genrsa -out rootCA.key 4096

# Genera il certificato della CA radice (self-signed)
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 3650 -out rootCA.crt -subj "/C=IT/ST=Tuscany/L=Pisa/O=GachaAndGames/OU=RootCA/CN=Root CA"


(crea ed entra nella cartella "dbCA"...)


# Crea chiave privata della databaseCA
openssl genrsa -out dbCA.key 4096

# Crea richiesta di firma del certificato (CSR) della databaseCA
openssl req -new -key dbCA.key -out dbCA.csr -subj "/C=IT/ST=Tuscany/L=Pisa/O=GachaAndGames/OU=DbCA/CN=Db CA"

# Come rootCA, approva la richiesta di firma del certificato della databaseCA generandone il certificato
openssl x509 -req -in dbCA.csr -CA ../rootCA.crt -CAkey ../rootCA.key -CAcreateserial -out dbCA.crt -days 1825 -sha256 -extfile <(echo "basicConstraints=CA:TRUE")


(torna a "GachaAndGames-Certs", crea ed entra nella cartella "redisCA"...)


# Crea chiave privata della redisCA
openssl genrsa -out redisCA.key 4096

# Crea richiesta di firma del certificato (CSR) della redisCA
openssl req -new -key redisCA.key -out redisCA.csr -subj "/C=IT/ST=Tuscany/L=Pisa/O=GachaAndGames/OU=RedisCA/CN=Redis CA"

# Come rootCA, approva la richiesta di firma del certificato della redisCA generandone il certificato
openssl x509 -req -in redisCA.csr -CA ../rootCA.crt -CAkey ../rootCA.key -CAcreateserial -out redisCA.crt -days 1825 -sha256 -extfile <(echo "basicConstraints=CA:TRUE")


(torna a "GachaAndGames-Certs", crea ed entra nella cartella "cdnCA"...)


# Crea chiave privata della cdnCA
openssl genrsa -out cdnCA.key 4096

# Crea richiesta di firma del certificato (CSR) della cdnCA
openssl req -new -key cdnCA.key -out cdnCA.csr -subj "/C=IT/ST=Tuscany/L=Pisa/O=GachaAndGames/OU=CdnCA/CN=Cdn CA"

# Come rootCA, approva la richiesta di firma del certificato della cdnCA generandone il certificato
openssl x509 -req -in cdnCA.csr -CA ../rootCA.crt -CAkey ../rootCA.key -CAcreateserial -out cdnCA.crt -days 1825 -sha256 -extfile <(echo "basicConstraints=CA:TRUE")


(torna a "GachaAndGames-Certs", crea ed entra nella cartella "serviceCA"...)


# Crea chiave privata della serviceCA
openssl genrsa -out serviceCA.key 4096

# Crea richiesta di firma del certificato (CSR) della serviceCA
openssl req -new -key serviceCA.key -out serviceCA.csr -subj "/C=IT/ST=Tuscany/L=Pisa/O=GachaAndGames/OU=ServiceCA/CN=Service CA"

# Come rootCA, approva la richiesta di firma del certificato della cdnCA generandone il certificato
openssl x509 -req -in serviceCA.csr -CA ../rootCA.crt -CAkey ../rootCA.key -CAcreateserial -out serviceCA.crt -days 1825 -sha256 -extfile <(echo "basicConstraints=CA:TRUE")




(torna a "redisCA", crea ed entra nella cartella "redis")


# Crea chiave privata di redis
openssl genrsa -out redis.key 4096

# Crea richiesta di firma del certificato (CSR) di redis
openssl req -new -key redis.key -out redis.csr -subj "/C=IT/ST=Tuscany/L=Pisa/O=GachaAndGames/OU=Develop/CN=redis"

(torna a "redisCA")
(esegui: touch index.txt)
(esegui: echo 01 > serial)
# Come redisCA, approva la richiesta di firma del certificato di redis generandone il certificato
openssl ca -in redis/redis.csr -out redis/redis.crt -config createCSR.conf


(torna a "serviceCA", crea ed entra nella cartella "service")


# Crea chiave privata di un servizio
openssl genrsa -out redis.key 4096

# Crea richiesta di firma del certificato (CSR) di un servizio
openssl req -new -key auth.key -out auth.csr -subj "/C=IT/ST=Tuscany/L=Pisa/O=GachaAndGames/OU=Develop/CN=auth"

(torna a "serviceCA")
(esegui: touch index.txt)
(esegui: echo 01 > serial)
# Come serviceCA, approva la richiesta di firma del certificato di un servizio generandone il certificato
openssl ca -in service/auth.csr -out service/auth.crt -config createCSR.conf


(torna a "dbCA", crea ed entra nella cartella "db")


# Crea chiave privata di un db
openssl genrsa -out db-auth.key 4096

# Crea richiesta di firma del certificato (CSR) di un db
openssl req -new -key db-auth.key -out db-auth.csr -subj "/C=IT/ST=Tuscany/L=Pisa/O=GachaAndGames/OU=Develop/CN=service_auth_db_proxy"

(torna a "dbCA")
(esegui: touch index.txt)
(esegui: echo 01 > serial)
# Come dbCA, approva la richiesta di firma del certificato di un db generandone il certificato
openssl ca -in db/db-auth.csr -out db/db-auth.crt -config createCSR.conf


(torna a "cdnCA", crea ed entra nella cartella "cdn")


# Crea chiave privata di una cdn
openssl genrsa -out cdn.key 4096

# Crea richiesta di firma del certificato (CSR) di una cdn
openssl req -new -key cdn.key -out cdn.csr -subj "/C=IT/ST=Tuscany/L=Pisa/O=GachaAndGames/OU=Develop/CN=cdn"

(torna a "cdnCA")
(esegui: touch index.txt)
(esegui: echo 01 > serial)
# Come cdnCA, approva la richiesta di firma del certificato di una cdn generandone il certificato
openssl ca -in cdn/cdn.csr -out cdn/cdn.crt -config createCSR.conf