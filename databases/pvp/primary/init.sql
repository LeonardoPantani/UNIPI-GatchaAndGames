USE gacha_test_db;

CREATE TABLE pvp_matches (
    match_uuid BINARY(16),
    player_1_uuid BINARY(16),
    player_2_uuid BINARY(16),
    winner BINARY(1),
    match_log JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gachas_types_used JSON,
    PRIMARY KEY (match_uuid)
);

CREATE USER 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT ALL PRIVILEGES ON gacha_test_db.* TO 'monitor'@'%';
FLUSH PRIVILEGES;


CREATE USER 'replication'@'%' IDENTIFIED BY 'Slaverepl123';
GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%';
FLUSH PRIVILEGES;