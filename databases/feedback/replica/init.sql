CHANGE REPLICATION SOURCE TO
    SOURCE_HOST='service_feedback_db_primary',
    SOURCE_USER='replication',
    SOURCE_PASSWORD='Slaverepl123',
    SOURCE_SSL=1,
    SOURCE_SSL_CA='/etc/mysql/certs/ca.crt',
    SOURCE_SSL_CERT='/etc/mysql/certs/db-feedback-replica.crt',
    SOURCE_SSL_KEY='/etc/mysql/certs/db-feedback-replica.key';

START REPLICA;