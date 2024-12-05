CHANGE REPLICATION SOURCE TO
    SOURCE_HOST='service_auth_db_primary',
    SOURCE_USER='replication',
    SOURCE_PASSWORD='Slaverepl123',
    SOURCE_SSL=1,
    SOURCE_SSL_CA='/etc/mysql/certs/ca.crt',
    SOURCE_SSL_CERT='/etc/mysql/certs/db-auth-replica.crt',
    SOURCE_SSL_KEY='/etc/mysql/certs/db-auth-replica.key';

START REPLICA;