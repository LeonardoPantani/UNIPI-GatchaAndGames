USE gacha_test_db;

CREATE TABLE auctions (
    uuid BINARY(16),
    item_uuid BINARY(16) NOT NULL,
    starting_price INT NOT NULL,
    current_bid INT,
    current_bidder BINARY(16),
    end_time TIMESTAMP NOT NULL,
    PRIMARY KEY (uuid)
);

CREATE USER 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT ALL PRIVILEGES ON gacha_test_db.* TO 'monitor'@'%';
FLUSH PRIVILEGES;


CREATE USER 'replication'@'%' IDENTIFIED BY 'Slaverepl123';
GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%';
FLUSH PRIVILEGES;