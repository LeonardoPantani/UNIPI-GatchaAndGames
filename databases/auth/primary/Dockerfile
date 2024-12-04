FROM mysql:9.1.0

COPY ./init.sql /docker-entrypoint-initdb.d/
COPY ./mock_data.sql /docker-entrypoint-initdb.d/
COPY ./ssl/ /etc/mysql/ssl/

RUN chown -R mysql:mysql /etc/mysql/ssl/* && chmod 640 /etc/mysql/ssl/*

CMD ["mysqld", "--ssl-cert=/etc/mysql/ssl/db-auth-primary.crt", "--ssl-key=/etc/mysql/ssl/db-auth-primary.key"]