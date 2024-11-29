FROM mysql:9.1.0

COPY ./ssl/ /etc/mysql/ssl/

RUN chown -R mysql:mysql /etc/mysql/ssl/ && chmod 600 /etc/mysql/ssl/*

CMD ["mysqld", "--server-id=2", "--log-bin=mysql-bin", "--relay-log=mysql-relay", "--read-only=ON", "--ssl-ca=/etc/mysql/ssl/ca-cert.pem", "--ssl-cert=/etc/mysql/ssl/server-cert.pem", "--ssl-key=/etc/mysql/ssl/server-key.pem"]