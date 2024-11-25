FROM mysql:9.1.0

COPY ./init.sql /docker-entrypoint-initdb.d/
COPY ./mock_data.sql /docker-entrypoint-initdb.d/
COPY ./ssl/ /etc/mysql/ssl/

RUN chown -R mysql:mysql /etc/mysql/ssl/ && chmod 600 /etc/mysql/ssl/*

CMD ["mysqld", "--ssl-ca=/etc/mysql/ssl/ca.pem", "--ssl-cert=/etc/mysql/ssl/server-cert.pem", "--ssl-key=/etc/mysql/ssl/server-key.pem", "--require_secure_transport=ON"]