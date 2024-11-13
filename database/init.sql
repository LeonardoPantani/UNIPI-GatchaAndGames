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
    username VARCHAR(100) NOT NULL,
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
BIN_TO_UUID(uuid),

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
    items JSON NOT NULL,
    PRIMARY KEY (codename)
);

INSERT INTO users (uuid, email, password, role) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'user1@example.com', 'password_hash1', 'USER'),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'user2@example.com', 'password_hash2', 'USER');

INSERT INTO profiles (uuid, username, currency, pvp_score) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'user1', 1000, 0),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'user2', 500, 0);

INSERT INTO gachas_types (uuid, name, stat_power, stat_speed, stat_durability, stat_precision, stat_range, stat_potential, rarity, release_date) VALUES
(UNHEX(REPLACE('1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76', '-', '')), 'GachaType1', 10, 15, 20, 12, 8, 25, 'RARE', '2024-01-01'),
(UNHEX(REPLACE('9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632', '-', '')), 'GachaType2', 12, 14, 18, 10, 7, 22, 'EPIC', '2024-01-02');

INSERT INTO inventories (item_uuid, owner_uuid, stand_uuid, owners_no, currency_spent) VALUES
(UNHEX(REPLACE('cc7a9a44-9f0b-4b10-8c85-e19b1c474e0d', '-', '')), UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), UNHEX(REPLACE('1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76', '-', '')), 1, 100),
(UNHEX(REPLACE('d3f2abac-6d22-4c07-9e16-2f68e93bfc22', '-', '')), UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), UNHEX(REPLACE('9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632', '-', '')), 1, 150);

INSERT INTO auctions (uuid, item_uuid, starting_price, current_bid, current_bidder, end_time) VALUES
(UNHEX(REPLACE('a7d30a76-02fe-4f5e-89c1-764742b23fc4', '-', '')), UNHEX(REPLACE('cc7a9a44-9f0b-4b10-8c85-e19b1c474e0d', '-', '')), 200, 0, UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), '2024-12-31 23:59:59'),
(UNHEX(REPLACE('7a30a7d2-2fe4-4a68-9402-88b815d89df8', '-', '')), UNHEX(REPLACE('d3f2abac-6d22-4c07-9e16-2f68e93bfc22', '-', '')), 500, 0, UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), '2024-12-31 23:59:59');

INSERT INTO pvp_matches (match_uuid, player_1_uuid, player_2_uuid, winner, match_log, gachas_types_used) VALUES
(UNHEX(REPLACE('c9b8c8c7-4fc4-4962-a578-47ecf26a2278', '-', '')), UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 0, '{"actions": ["attack", "defend"]}', '{"gacha1": 30, "gacha2": 20}'),
(UNHEX(REPLACE('8a68c6c1-305b-4a3e-9c5b-b7d56f042786', '-', '')), UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 1, '{"actions": ["special_attack"]}', '{"gacha3": 40, "gacha4": 10}');

INSERT INTO bundles (codename, currency_name, public_name, credits_obtained, price) VALUES
('launch_event_bundle_novice', 'EUR', 'Launch Event Bundle Novice', 1000, 100.00),
('launch_event_bundle_pro', 'USD', 'Launch Event Bundle Pro', 100000, 300.00);

INSERT INTO bundles_transactions (bundle_codename, bundle_currency_name, user_uuid) VALUES
('launch_event_bundle_novice', 'EUR', UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', ''))),
('launch_event_bundle_pro', 'USD', UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')));

INSERT INTO ingame_transactions (user_uuid, credits, transaction_type) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 1000, 'bought_bundle'),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 500, 'sold_market');

INSERT INTO logs (value) VALUES
('User1 bought a bundle'),
('User2 placed a bid');

INSERT INTO feedbacks (user_uuid, content) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'Great service, love the game!'),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'Could be better, but overall good experience.');

INSERT INTO gacha_pools (codename, public_name, probabilities, items) VALUES
('novice_pool', 'Novice Gacha Pool', '{"common": 0.7, "rare": 0.2, "epic": 0.1}', '{"item1": 10, "item2": 5}'),
('pro_pool', 'Pro Gacha Pool', '{"common": 0.5, "rare": 0.3, "epic": 0.15, "legendary": 0.05}', '{"item3": 15, "item4": 3}');
