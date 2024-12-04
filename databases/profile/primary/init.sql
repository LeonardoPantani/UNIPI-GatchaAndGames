USE gacha_test_db;

CREATE TABLE profiles (
    uuid BINARY(16),
    username VARCHAR(100) NOT NULL UNIQUE,
    currency INT DEFAULT 0,
    pvp_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uuid)
);

CREATE USER 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT ALL PRIVILEGES ON gacha_test_db.* TO 'monitor'@'%';
FLUSH PRIVILEGES;


CREATE USER 'replication'@'%' IDENTIFIED BY 'Slaverepl123';
GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%';
FLUSH PRIVILEGES;