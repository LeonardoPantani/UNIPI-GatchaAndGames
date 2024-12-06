USE gacha_test_db;

CREATE TABLE inventories (
    item_uuid BINARY(16),
    owner_uuid BINARY(16) NOT NULL,
    stand_uuid BINARY(16) NOT NULL,
    obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    owners_no INT NOT NULL,
    currency_spent INT NOT NULL,
    PRIMARY KEY (item_uuid)
);

CREATE USER 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT ALL PRIVILEGES ON gacha_test_db.* TO 'monitor'@'%';
FLUSH PRIVILEGES;


CREATE USER 'replication'@'%' IDENTIFIED BY 'Slaverepl123';
GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%';
FLUSH PRIVILEGES;