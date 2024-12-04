FROM mysql:9.1.0

COPY ./ssl/ /etc/mysql/ssl/

RUN chown -R mysql:mysql /etc/mysql/ssl/ && chmod 600 /etc/mysql/ssl/*

CMD ["mysqld", "--server-id=2", "--log-bin=mysql-bin", "--relay-log=mysql-relay", "--read-only=ON", "--ssl-ca=/etc/mysql/ssl/rootCA.crt", "--ssl-cert=/etc/mysql/ssl/db-auth-replica.crt", "--ssl-key=/etc/mysql/ssl/db-auth-replica.key"]