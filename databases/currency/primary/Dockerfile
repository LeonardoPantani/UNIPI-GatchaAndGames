FROM mysql:9.1.0

COPY ./init.sql /docker-entrypoint-initdb.d/
COPY ./mock_data.sql /docker-entrypoint-initdb.d/
COPY ./ssl/ /etc/mysql/certs/

RUN chown -R mysql:mysql /etc/mysql/certs && chmod 600 /etc/mysql/certs/*

CMD ["mysqld", "--max_connections=500", "--require_secure_transport=ON", "--ssl-ca=/etc/mysql/certs/ca.crt", "--ssl-cert=/etc/mysql/certs/db-currency-primary.crt", "--ssl-key=/etc/mysql/certs/db-currency-primary.key"]