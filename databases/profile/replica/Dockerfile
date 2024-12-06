FROM mysql:9.1.0

COPY ./ssl/ /etc/mysql/certs/

RUN chown -R mysql:mysql /etc/mysql/certs/ && chmod 600 /etc/mysql/certs/*

CMD ["mysqld", "--require_secure_transport=ON", "--server-id=2", "--log-bin=mysql-bin", "--relay-log=mysql-relay", "--read-only=ON", "--ssl-ca=/etc/mysql/certs/ca.crt", "--ssl-cert=/etc/mysql/certs/db-profile-replica.crt", "--ssl-key=/etc/mysql/certs/db-profile-replica.key"]