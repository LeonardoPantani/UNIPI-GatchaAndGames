USE gacha_test_db;

CREATE TABLE feedbacks (
    id INT AUTO_INCREMENT,
    user_uuid BINARY(16) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);


CREATE USER 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT ALL PRIVILEGES ON gacha_test_db.* TO 'monitor'@'%';
FLUSH PRIVILEGES;


CREATE USER 'replication'@'%' IDENTIFIED BY 'Slaverepl123';
GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%';
FLUSH PRIVILEGES;