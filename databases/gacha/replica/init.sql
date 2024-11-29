CHANGE REPLICATION SOURCE TO
    SOURCE_HOST='service_gacha_db_primary',
    SOURCE_USER='replication',
    SOURCE_PASSWORD='Slaverepl123',
    SOURCE_SSL=1,
    SOURCE_SSL_CA='/etc/mysql/ssl/ca-cert.pem',
    SOURCE_SSL_CERT='/etc/mysql/ssl/server-cert.pem',
    SOURCE_SSL_KEY='/etc/mysql/ssl/server-key.pem';

START REPLICA;