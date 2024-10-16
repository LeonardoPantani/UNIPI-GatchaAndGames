CREATE USER 'gatcha_backend'@'localhost' IDENTIFIED BY 'prova';
GRANT SELECT, INSERT, UPDATE, DELETE ON gatcha.* TO 'gatcha_backend'@'localhost';
FLUSH PRIVILEGES;