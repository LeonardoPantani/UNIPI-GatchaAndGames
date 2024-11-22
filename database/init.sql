USE gacha_test_db;

CREATE TABLE users (
    uuid BINARY(16),
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('USER', 'ADMIN') NOT NULL,
    PRIMARY KEY (uuid)
);

CREATE TABLE profiles (
    uuid BINARY(16),
    username VARCHAR(100) NOT NULL UNIQUE,
    currency INT DEFAULT 0,
    pvp_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uuid),
    FOREIGN KEY (uuid) REFERENCES users(uuid)
);

CREATE TABLE bundles (
    codename VARCHAR(100),
    currency_name VARCHAR(3),
    public_name VARCHAR(200) NOT NULL, 
    credits_obtained INT NOT NULL,
    price DECIMAL(15,2) NOT NULL,
    PRIMARY KEY (codename, currency_name)
);

-- users can buy ingame currency with predefined ingame currency bundles like:
-- launch_event_bundle_novice [100 EUR or 110 USD or 450 PLN] -> 1000 coins
-- launch_event_bundle_pro [300 EUR or 350 USD or 1300 PLN]  -> 100000 coins
CREATE TABLE bundles_transactions (
    bundle_codename VARCHAR(100),
    bundle_currency_name VARCHAR(3),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_uuid BINARY(16),
    PRIMARY KEY (bundle_codename, bundle_currency_name, timestamp, user_uuid),
    FOREIGN KEY (bundle_codename, bundle_currency_name) REFERENCES bundles(codename, currency_name),
    FOREIGN KEY (user_uuid) REFERENCES profiles(uuid)
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
    PRIMARY KEY (user_uuid, timestamp),
    FOREIGN KEY (user_uuid) REFERENCES profiles(uuid)
);

CREATE TABLE pvp_matches (
    match_uuid BINARY(16),
    player_1_uuid BINARY(16),
    player_2_uuid BINARY(16),
    winner BINARY(1),
    match_log JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gachas_types_used JSON,
    PRIMARY KEY (match_uuid),
    FOREIGN KEY (player_1_uuid) REFERENCES profiles(uuid),
    FOREIGN KEY (player_2_uuid) REFERENCES profiles(uuid)
);

CREATE TABLE gachas_types (
    uuid BINARY(16),
    name VARCHAR(255) NOT NULL,
    stat_power INT NOT NULL,
    stat_speed INT NOT NULL,
    stat_durability INT NOT NULL,
    stat_precision INT NOT NULL,
    stat_range INT NOT NULL,
    stat_potential INT NOT NULL,
    rarity ENUM('COMMON', 'RARE', 'EPIC', 'LEGENDARY') NOT NULL,
    release_date DATE NOT NULL,
    PRIMARY KEY (uuid)
);

CREATE TABLE inventories (
    item_uuid BINARY(16),
    owner_uuid BINARY(16) NOT NULL,
    stand_uuid BINARY(16) NOT NULL,
    obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    owners_no INT NOT NULL,
    currency_spent INT NOT NULL,
    PRIMARY KEY (item_uuid),
    FOREIGN KEY (owner_uuid) REFERENCES profiles(uuid),
    FOREIGN KEY (stand_uuid) REFERENCES gachas_types(uuid)
);

CREATE TABLE auctions (
    uuid BINARY(16),
    item_uuid BINARY(16) NOT NULL,
    starting_price INT NOT NULL,
    current_bid INT,
    current_bidder BINARY(16),
    end_time TIMESTAMP NOT NULL,
    PRIMARY KEY (uuid),
    FOREIGN KEY (item_uuid) REFERENCES inventories(item_uuid),
    FOREIGN KEY (current_bidder) REFERENCES profiles(uuid)
);

CREATE TABLE logs (
    id INT AUTO_INCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    value TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE feedbacks (
    id INT AUTO_INCREMENT,
    user_uuid BINARY(16) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_uuid) REFERENCES users(uuid)
);

CREATE TABLE gacha_pools (
    codename VARCHAR(100),
    public_name VARCHAR(200) NOT NULL,
    probabilities JSON NOT NULL,
    price INT NOT NULL,
    PRIMARY KEY (codename)
);

CREATE TABLE gacha_pools_items (
    codename VARCHAR(100),
    gacha_uuid BINARY(16),
    PRIMARY KEY (codename, gacha_uuid),
    FOREIGN KEY (codename) REFERENCES gacha_pools(codename),
    FOREIGN KEY (gacha_uuid) REFERENCES gachas_types(uuid)
);