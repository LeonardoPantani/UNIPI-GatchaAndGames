USE gacha_test_db;

CREATE TABLE bundles (
    codename VARCHAR(100),
    currency_name VARCHAR(3),
    public_name VARCHAR(200) NOT NULL, 
    credits_obtained INT NOT NULL,
    price DECIMAL(15,2) NOT NULL,
    PRIMARY KEY (codename)
);

-- users can buy ingame currency with predefined ingame currency bundles like:
-- launch_event_bundle_novice [100 EUR or 110 USD or 450 PLN] -> 1000 coins
-- launch_event_bundle_pro [300 EUR or 350 USD or 1300 PLN]  -> 100000 coins
CREATE TABLE bundles_transactions (
    bundle_codename VARCHAR(100),
    bundle_currency_name VARCHAR(3),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_uuid BINARY(16),
    PRIMARY KEY (bundle_codename, timestamp, user_uuid),
    FOREIGN KEY (bundle_codename) REFERENCES bundles(codename)
);

-- transactions can be of 4 types:
-- > user buys a bundle (credits obtained, +)
-- > user sells something on the market (credits obtained, +)
-- > user buys something from the market (credits deduced, -)
-- > user pulls a gacha from a pool (credits deduced, -)
CREATE TABLE ingame_transactions (
    user_uuid BINARY(16),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    credits INT NOT NULL,
    transaction_type ENUM('bought_bundle', 'sold_market', 'bought_market', 'gacha_pull') NOT NULL,
    PRIMARY KEY (user_uuid, timestamp)
);


CREATE USER 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT ALL PRIVILEGES ON gacha_test_db.* TO 'monitor'@'%';
FLUSH PRIVILEGES;


CREATE USER 'replication'@'%' IDENTIFIED BY 'Slaverepl123';
GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%';
FLUSH PRIVILEGES;