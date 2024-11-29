USE gacha_test_db;

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

-- DECIMAL (3, 2) 3: total number of digits, 2: number of digits after comma
CREATE TABLE gacha_pools (
    codename VARCHAR(100),
    public_name VARCHAR(200) NOT NULL, 
    probability_common DECIMAL(3, 2) NOT NULL,
    probability_rare DECIMAL(3, 2) NOT NULL,
    probability_epic DECIMAL(3, 2) NOT NULL,
    probability_legendary DECIMAL(3, 2) NOT NULL,
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


CREATE USER 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT ALL PRIVILEGES ON gacha_test_db.* TO 'monitor'@'%';
FLUSH PRIVILEGES;


CREATE USER 'replication'@'%' IDENTIFIED BY 'Slaverepl123';
GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%';
FLUSH PRIVILEGES;