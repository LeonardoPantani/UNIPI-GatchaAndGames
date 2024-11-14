-- Insert into `users` table
INSERT INTO users (uuid, email, password, role) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'user1@example.com', '$2b$12$XRQfYzKIQoyQXNUYU0lcB.p/YHN5YqXxEn62BH5WiK.w8Q.i5z7cy', 'USER'), -- password: user1_password
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'user2@example.com', '$2b$12$3nOBbi1saMMQHppfKBS.1.HAJbeZAlMWCUcn3TIe1nVxSmMAIsbZ2', 'USER'), -- password: user2_password
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 'user3@example.com', '$2b$12$jqb2pkG1hQ4j4xJkbYTt8el9iVraf9IOg5ODWR9cjHcVF9sttNTja', 'USER'), -- password: user3_password
(UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')), 'admin@example.com', '$2b$12$xesJM04e8RQTK0yd0qIuQuJFf/ZMkq4YuEHYVzT4Isdff3lSHNshG', 'ADMIN'); -- password: admin_password

-- Insert into `profiles` table
INSERT INTO profiles (uuid, username, currency, pvp_score) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'user1', 1000, 0),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'user2', 500, 0),
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 'user3', 1500, 30),
(UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')), 'admin', 2000, 50);

-- Insert into `gachas_types` table
INSERT INTO gachas_types (uuid, name, stat_power, stat_speed, stat_durability, stat_precision, stat_range, stat_potential, rarity, release_date) VALUES
(UNHEX(REPLACE('1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76', '-', '')), 'GachaType1', 10, 15, 20, 12, 8, 25, 'RARE', '2024-01-01'),
(UNHEX(REPLACE('9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632', '-', '')), 'GachaType2', 12, 14, 18, 10, 7, 22, 'EPIC', '2024-01-02'),
(UNHEX(REPLACE('b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85', '-', '')), 'GachaType3', 8, 10, 15, 18, 5, 10, 'COMMON', '2024-01-03'),
(UNHEX(REPLACE('8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7', '-', '')), 'GachaType4', 25, 20, 30, 22, 15, 35, 'LEGENDARY', '2024-01-04');

-- Insert into `inventories` table
INSERT INTO inventories (item_uuid, owner_uuid, stand_uuid, owners_no, currency_spent) VALUES
(UNHEX(REPLACE('cc7a9a44-9f0b-4b10-8c85-e19b1c474e0d', '-', '')), UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), UNHEX(REPLACE('1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76', '-', '')), 1, 100),
(UNHEX(REPLACE('d3f2abac-6d22-4c07-9e16-2f68e93bfc22', '-', '')), UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), UNHEX(REPLACE('9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632', '-', '')), 1, 150),
(UNHEX(REPLACE('bf48c432-02df-498e-85c8-2a4b2f3e6a09', '-', '')), UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), UNHEX(REPLACE('b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85', '-', '')), 1, 50);

-- Insert into `auctions` table
INSERT INTO auctions (uuid, item_uuid, starting_price, current_bid, current_bidder, end_time) VALUES
(UNHEX(REPLACE('a7d30a76-02fe-4f5e-89c1-764742b23fc4', '-', '')), UNHEX(REPLACE('cc7a9a44-9f0b-4b10-8c85-e19b1c474e0d', '-', '')), 200, 0, UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), '2024-12-31 23:59:59'),
(UNHEX(REPLACE('7a30a7d2-2fe4-4a68-9402-88b815d89df8', '-', '')), UNHEX(REPLACE('d3f2abac-6d22-4c07-9e16-2f68e93bfc22', '-', '')), 500, 0, UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), '2024-12-31 23:59:59');

-- Insert into `pvp_matches` table
INSERT INTO pvp_matches (match_uuid, player_1_uuid, player_2_uuid, winner, match_log, gachas_types_used) VALUES
(UNHEX(REPLACE('c9b8c8c7-4fc4-4962-a578-47ecf26a2278', '-', '')), UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 0, '{"actions": ["attack", "defend"]}', '{"gacha1": 30, "gacha2": 20}'),
(UNHEX(REPLACE('8a68c6c1-305b-4a3e-9c5b-b7d56f042786', '-', '')), UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 1, '{"actions": ["special_attack"]}', '{"gacha3": 40, "gacha4": 10}');

-- Insert into `bundles` table
INSERT INTO bundles (codename, currency_name, public_name, credits_obtained, price) VALUES
('launch_event_bundle_novice', 'EUR', 'Launch Event Bundle Novice', 1000, 100.00),
('launch_event_bundle_pro', 'USD', 'Launch Event Bundle Pro', 100000, 300.00),
('launch_event_bundle_expert', 'PLN', 'Launch Event Bundle Expert', 150000, 500.00);

-- Insert into `bundles_transactions` table
INSERT INTO bundles_transactions (bundle_codename, bundle_currency_name, user_uuid) VALUES
('launch_event_bundle_novice', 'EUR', UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', ''))),
('launch_event_bundle_pro', 'USD', UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', ''))),
('launch_event_bundle_expert', 'PLN', UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')));

-- Insert into `ingame_transactions` table
INSERT INTO ingame_transactions (user_uuid, credits, transaction_type) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 1000, 'bought_bundle'),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 500, 'sold_market'),
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 200, 'gacha_pull');

-- Insert into `logs` table
INSERT INTO logs (value) VALUES
('User1 bought a bundle'),
('User2 placed a bid'),
('User3 participated in PvP');

-- Insert into `feedbacks` table
INSERT INTO feedbacks (user_uuid, content) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'Great service, love the game!'),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'Could be better, but overall good experience.'),
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 'Awesome events!');

-- Insert into `gacha_pools` table
INSERT INTO gacha_pools (codename, public_name, probabilities, items) VALUES
('novice_pool', 'Novice Gacha Pool', '{"common": 0.7, "rare": 0.2, "epic": 0.1}', '{"item1": 10, "item2": 5}'),
('pro_pool', 'Pro Gacha Pool', '{"common": 0.5, "rare": 0.3, "epic": 0.15, "legendary": 0.05}', '{"item3": 15, "item4": 3}');
