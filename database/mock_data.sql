-- Insert into `users` table
INSERT INTO users (uuid, email, password, role) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'jotaro@joestar.com', '$2b$12$XRQfYzKIQoyQXNUYU0lcB.p/YHN5YqXxEn62BH5WiK.w8Q.i5z7cy', 'USER'), -- password: star_platinum
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'dio.brando@world.com', '$2b$12$3nOBbi1saMMQHppfKBS.1.HAJbeZAlMWCUcn3TIe1nVxSmMAIsbZ2', 'USER'), -- password: za_warudo
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 'giorno@passione.it', '$2b$12$jqb2pkG1hQ4j4xJkbYTt8el9iVraf9IOg5ODWR9cjHcVF9sttNTja', 'USER'), -- password: gold_experience
(UNHEX(REPLACE('b5c3d2e1-4f5e-6a7b-8c9d-0e1f2a3b4c5d', '-', '')), 'josuke@morioh.jp', '$2b$12$jqb2pkG1hQ4j4xJkbYTt8el9iVraf9IOg5ODWR9cjHcVF9sttNTja', 'USER'), -- password: crazy_diamond
(UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')), 'speedwagon@foundation.org', '$2b$12$xesJM04e8RQTK0yd0qIuQuJFf/ZMkq4YuEHYVzT4Isdff3lSHNshG', 'ADMIN'), -- password: admin_foundation
(UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')), 'admin@admin.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewqkfQhrLvvD3.4K', 'ADMIN'); -- password: password -- Insert additional admin user


-- Insert into `profiles` table
INSERT INTO profiles (uuid, username, currency, pvp_score) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'JotaroKujo', 5000, 100),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'DIOBrando', 6000, 95),
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 'GiornoGiovanna', 4500, 85),
(UNHEX(REPLACE('b5c3d2e1-4f5e-6a7b-8c9d-0e1f2a3b4c5d', '-', '')), 'JosukeHigashikata', 3500, 80),
(UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')), 'SpeedwagonAdmin', 10000, 98);
(UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')), 'AdminUser', 100000000, 999);

-- Insert into `gachas_types` table (Stands with their stats)
INSERT INTO gachas_types (uuid, name, stat_power, stat_speed, stat_durability, stat_precision, stat_range, stat_potential, rarity, release_date) VALUES
(UNHEX(REPLACE('1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76', '-', '')), 'Star Platinum', 5, 5, 5, 5, 3, 5, 'LEGENDARY', '2024-01-01'),
(UNHEX(REPLACE('9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632', '-', '')), 'The World', 5, 5, 5, 5, 3, 5, 'LEGENDARY', '2024-01-02'),
(UNHEX(REPLACE('b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85', '-', '')), 'Gold Experience', 4, 4, 4, 4, 3, 5, 'EPIC', '2024-01-03'),
(UNHEX(REPLACE('8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7', '-', '')), 'Crazy Diamond', 5, 5, 4, 5, 2, 4, 'EPIC', '2024-01-04'),
(UNHEX(REPLACE('c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f', '-', '')), 'Silver Chariot', 4, 5, 3, 5, 3, 3, 'RARE', '2024-01-05'),
(UNHEX(REPLACE('d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a', '-', '')), 'Hermit Purple', 2, 3, 3, 4, 4, 2, 'COMMON', '2024-01-06'),
(UNHEX(REPLACE('e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b', '-', '')), 'Magicians Red', 4, 3, 3, 3, 4, 3, 'RARE', '2024-01-07'),
(UNHEX(REPLACE('f1a2b3c4-d5e6-f7a8-b9c0-1d2e3f4a5b6c', '-', '')), 'Hierophant Green', 3, 3, 3, 5, 5, 3, 'RARE', '2024-01-08'),
(UNHEX(REPLACE('a1b2c3d4-e5f6-7890-1234-567890abcdef', '-', '')), 'King Crimson', 5, 4, 4, 4, 2, 5, 'LEGENDARY', '2024-01-09'),
(UNHEX(REPLACE('b2c3d4e5-f6a7-8901-2345-67890abcdef1', '-', '')), 'Killer Queen', 4, 4, 4, 5, 3, 4, 'EPIC', '2024-01-10'),
(UNHEX(REPLACE('c3d4e5f6-a7b8-9012-3456-7890abcdef12', '-', '')), 'Made in Heaven', 5, 5, 5, 5, 5, 5, 'LEGENDARY', '2024-01-11'),
(UNHEX(REPLACE('d4e5f6a7-b8c9-0123-4567-890abcdef123', '-', '')), 'Sticky Fingers', 4, 4, 3, 4, 2, 3, 'RARE', '2024-01-12'),
(UNHEX(REPLACE('e5f6a7b8-c9d0-1234-5678-90abcdef1234', '-', '')), 'Purple Haze', 5, 3, 3, 2, 2, 2, 'EPIC', '2024-01-13'),
(UNHEX(REPLACE('f6a7b8c9-d0e1-2345-6789-0abcdef12345', '-', '')), 'Sex Pistols', 2, 3, 4, 5, 5, 2, 'RARE', '2024-01-14'),
(UNHEX(REPLACE('a7b8c9d0-e1f2-3456-7890-abcdef123456', '-', '')), 'Aerosmith', 3, 4, 3, 4, 5, 2, 'RARE', '2024-01-15'),
(UNHEX(REPLACE('b8c9d0e1-f2a3-4567-8901-bcdef1234567', '-', '')), 'Moody Blues', 2, 3, 3, 5, 2, 3, 'RARE', '2024-01-16'),
(UNHEX(REPLACE('c9d0e1f2-a3b4-5678-9012-cdef12345678', '-', '')), 'Beach Boy', 1, 2, 3, 5, 5, 2, 'COMMON', '2024-01-17'),
(UNHEX(REPLACE('d0e1f2a3-b4c5-6789-0123-def123456789', '-', '')), 'White Album', 3, 3, 5, 3, 2, 3, 'RARE', '2024-01-18'),
(UNHEX(REPLACE('e1f2a3b4-c5d6-7890-1234-ef123456789a', '-', '')), 'Stone Free', 4, 4, 4, 5, 3, 4, 'EPIC', '2024-01-19'),
(UNHEX(REPLACE('f2a3b4c5-d6e7-8901-2345-f123456789ab', '-', '')), 'Weather Report', 4, 3, 4, 4, 4, 5, 'EPIC', '2024-01-20'),
(UNHEX(REPLACE('a3b4c5d6-e7f8-9012-3456-123456789abc', '-', '')), 'D4C', 5, 4, 5, 4, 3, 5, 'LEGENDARY', '2024-01-21'),
(UNHEX(REPLACE('b4c5d6e7-f8a9-0123-4567-23456789abcd', '-', '')), 'Tusk Act 4', 5, 3, 5, 4, 3, 5, 'LEGENDARY', '2024-01-22'),
(UNHEX(REPLACE('c5d6e7f8-a9b0-1234-5678-3456789abcde', '-', '')), 'Soft & Wet', 4, 4, 4, 5, 2, 5, 'EPIC', '2024-01-23');


-- Insert into `gacha_pools` table
INSERT INTO gacha_pools (codename, public_name, probabilities, price, release_date) VALUES
('pool_joestar', 'Joestar Legacy Pool', '{"common": 0.5, "rare": 0.3, "epic": 0.15, "legendary": 0.05}', 1000, '2024-01-01'),
('pool_passione', 'Passione Gang Pool', '{"common": 0.45, "rare": 0.35, "epic": 0.15, "legendary": 0.05}', 1200, '2024-01-02'),
('pool_duwang', 'Morioh Pool', '{"common": 0.4, "rare": 0.35, "epic": 0.2, "legendary": 0.05}', 1500, '2024-01-03'),
('pool_pucci', 'Heaven Pool', '{"common": 0.3, "rare": 0.3, "epic": 0.3, "legendary": 0.1}', 2000, '2024-01-04'),
('pool_valentine', 'Patriot Pool', '{"common": 0.4, "rare": 0.3, "epic": 0.2, "legendary": 0.1}', 1800, '2024-01-05');

-- Insert into `gacha_pools_items` table (linking stands to their appropriate pools)
INSERT INTO gacha_pools_items (codename, gacha_uuid) VALUES
-- Joestar Legacy Pool (Stands related to the Joestar family)
('pool_joestar', UNHEX(REPLACE('1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76', '-', ''))), -- Star Platinum
('pool_joestar', UNHEX(REPLACE('d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a', '-', ''))), -- Hermit Purple
('pool_joestar', UNHEX(REPLACE('8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7', '-', ''))), -- Crazy Diamond
('pool_joestar', UNHEX(REPLACE('e1f2a3b4-c5d6-7890-1234-ef123456789a', '-', ''))), -- Stone Free
('pool_joestar', UNHEX(REPLACE('b4c5d6e7-f8a9-0123-4567-23456789abcd', '-', ''))), -- Tusk Act 4
('pool_joestar', UNHEX(REPLACE('c5d6e7f8-a9b0-1234-5678-3456789abcde', '-', ''))), -- Soft & Wet

-- Passione Gang Pool (Stands from Golden Wind)
('pool_passione', UNHEX(REPLACE('b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85', '-', ''))), -- Gold Experience
('pool_passione', UNHEX(REPLACE('d4e5f6a7-b8c9-0123-4567-890abcdef123', '-', ''))), -- Sticky Fingers
('pool_passione', UNHEX(REPLACE('e5f6a7b8-c9d0-1234-5678-90abcdef1234', '-', ''))), -- Purple Haze
('pool_passione', UNHEX(REPLACE('f6a7b8c9-d0e1-2345-6789-0abcdef12345', '-', ''))), -- Sex Pistols
('pool_passione', UNHEX(REPLACE('a7b8c9d0-e1f2-3456-7890-abcdef123456', '-', ''))), -- Aerosmith
('pool_passione', UNHEX(REPLACE('b8c9d0e1-f2a3-4567-8901-bcdef1234567', '-', ''))), -- Moody Blues

-- Morioh Pool (Stands from Diamond is Unbreakable)
('pool_duwang', UNHEX(REPLACE('8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7', '-', ''))), -- Crazy Diamond
('pool_duwang', UNHEX(REPLACE('b2c3d4e5-f6a7-8901-2345-67890abcdef1', '-', ''))), -- Killer Queen
('pool_duwang', UNHEX(REPLACE('c9d0e1f2-a3b4-5678-9012-cdef12345678', '-', ''))), -- Beach Boy
('pool_duwang', UNHEX(REPLACE('d0e1f2a3-b4c5-6789-0123-def123456789', '-', ''))), -- White Album

-- Heaven Pool (Powerful stands related to DIO and Pucci)
('pool_pucci', UNHEX(REPLACE('9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632', '-', ''))), -- The World
('pool_pucci', UNHEX(REPLACE('c3d4e5f6-a7b8-9012-3456-7890abcdef12', '-', ''))), -- Made in Heaven
('pool_pucci', UNHEX(REPLACE('a1b2c3d4-e5f6-7890-1234-567890abcdef', '-', ''))), -- King Crimson
('pool_pucci', UNHEX(REPLACE('f2a3b4c5-d6e7-8901-2345-f123456789ab', '-', ''))), -- Weather Report

-- Patriot Pool (Stands from Steel Ball Run)
('pool_valentine', UNHEX(REPLACE('a3b4c5d6-e7f8-9012-3456-123456789abc', '-', ''))), -- D4C
('pool_valentine', UNHEX(REPLACE('b4c5d6e7-f8a9-0123-4567-23456789abcd', '-', ''))), -- Tusk Act 4
('pool_valentine', UNHEX(REPLACE('c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f', '-', ''))), -- Silver Chariot
('pool_valentine', UNHEX(REPLACE('e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b', '-', ''))); -- Magicians Red


-- Insert into `inventories` table
INSERT INTO inventories (item_uuid, owner_uuid, stand_uuid, obtained_at, owners_no, currency_spent) VALUES
-- Jotaro's Inventory
(UNHEX(REPLACE('f7e6d5c4-b3a2-9180-7654-321098fedcba', '-', '')), 
 UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 
 UNHEX(REPLACE('1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76', '-', '')), -- Star Platinum
 '2024-01-01', 1, 3000),

-- DIO's Inventory
(UNHEX(REPLACE('e6d5c4b3-a291-8076-5432-109876fedcba', '-', '')), 
 UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 
 UNHEX(REPLACE('9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632', '-', '')), -- The World
 '2024-01-02', 1, 3000),

-- Giorno's Inventory
(UNHEX(REPLACE('d5c4b3a2-9180-7654-3210-9876fedcba98', '-', '')), 
 UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 
 UNHEX(REPLACE('b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85', '-', '')), -- Gold Experience
 '2024-01-03', 1, 2500);

 INSERT INTO inventories (item_uuid, owner_uuid, stand_uuid, obtained_at, owners_no, currency_spent) VALUES
(UNHEX(REPLACE('c7b6a5d4-e3f2-1098-7654-fedcba987654', '-', '')), 
 UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')), -- Speedwagon
 UNHEX(REPLACE('e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b', '-', '')), -- Magicians Red 
 '2024-01-01', 1, 5000),
(UNHEX(REPLACE('b7a6c5d4-e3f2-1098-7654-fedcba987655', '-', '')),
 UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')), -- Speedwagon
 UNHEX(REPLACE('c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f', '-', '')), -- Silver Chariot
 '2024-01-02', 1, 6000);

 INSERT INTO pvp_matches (match_uuid, player_1_uuid, player_2_uuid, winner, match_log, timestamp) VALUES
-- Jotaro vs DIO
(UNHEX(REPLACE('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '-', '')),
 UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), -- Jotaro
 UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), -- DIO
 true,
 '{
    "match": {
      "pvp_match_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "sender_id": "e3b0c442-98fc-1c14-b39f-92d1282048c0",
      "receiver_id": "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
      "teams": {
        "team1": ["1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76"],
        "team2": ["9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632"]
      },
      "winner": true,
      "match_log": {
        "pairings": [
          {
            "pair": "Jotaro StarPlatinum vs DIO TheWorld",
            "extracted_stat": "power",
            "player1": {"stand_stat": 5},
            "player2": {"stand_stat": 5}
          }
        ]
      }
    },
    "points": 25
  }',
 '2024-01-15 12:00:00'),

-- Giorno vs DIO
(UNHEX(REPLACE('b2c3d4e5-f6a7-8901-bcde-f12345678901', '-', '')),
 UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), -- Giorno
 UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), -- DIO
 true,
 '{
    "match": {
      "pvp_match_uuid": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "sender_id": "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
      "receiver_id": "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
      "teams": {
        "team1": ["b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85"],
        "team2": ["9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632"]
      },
      "winner": true,
      "match_log": {
        "pairings": [
          {
            "pair": "Giorno GoldExperience vs DIO TheWorld",
            "extracted_stat": "potential",
            "player1": {"stand_stat": 5},
            "player2": {"stand_stat": 5}
          }
        ]
      }
    },
    "points": 30
  }',
 '2024-01-16 15:30:00');

-- Insert into `bundles` table
INSERT INTO bundles (codename, currency_name, public_name, credits_obtained, price) VALUES
('bundle_arrow', 'EUR', 'Stand Arrow Bundle', 1000, 9.99),
('bundle_requiem', 'EUR', 'Requiem Arrow Bundle', 3000, 24.99),
('bundle_heaven', 'EUR', 'Heaven\'s Bundle', 5000, 49.99),
('bundle_arrow', 'USD', 'Stand Arrow Bundle', 1000, 10.99),
('bundle_requiem', 'USD', 'Requiem Arrow Bundle', 3000, 27.99),
('bundle_heaven', 'USD', 'Heaven\'s Bundle', 5000, 54.99);

-- Insert into `bundles_transactions` table
INSERT INTO bundles_transactions (bundle_codename, bundle_currency_name, user_uuid, timestamp) VALUES
('bundle_arrow', 'EUR', UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), '2024-01-05 10:00:00'),
('bundle_heaven', 'USD', UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), '2024-01-06 11:30:00'),
('bundle_requiem', 'EUR', UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), '2024-01-07 15:45:00');

-- Insert into `ingame_transactions` table
INSERT INTO ingame_transactions (user_uuid, credits, transaction_type, timestamp) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 1000, 'bought_bundle', '2024-01-05 10:00:00'),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 5000, 'bought_bundle', '2024-01-06 11:30:00'),
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 3000, 'bought_bundle', '2024-01-07 15:45:00'),
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), -1000, 'gacha_pull', '2024-01-08 09:15:00'),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), -1200, 'gacha_pull', '2024-01-09 14:20:00');

-- Insert into `auctions` table
INSERT INTO auctions (uuid, item_uuid, starting_price, current_bid, current_bidder, end_time) VALUES
(UNHEX(REPLACE('aabbccdd-eeff-0011-2233-445566778899', '-', '')),
 UNHEX(REPLACE('f7e6d5c4-b3a2-9180-7654-321098fedcba', '-', '')),
 5000, 6000,
 UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')),
 '2024-02-01 00:00:00');

 INSERT INTO auctions (uuid, item_uuid, starting_price, current_bid, current_bidder, end_time) VALUES
(UNHEX(REPLACE('a9b8c7d6-e5f4-3210-9876-fedcba987654', '-', '')),
 UNHEX(REPLACE('c7b6a5d4-e3f2-1098-7654-fedcba987654', '-', '')), -- Magicians Red item UUID
 5000, -- starting price
 6500, -- current bid
 UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), -- Jotaro as current bidder
 '2024-02-01 00:00:00'); -- end time

-- Insert into `feedbacks` table
INSERT INTO feedbacks (user_uuid, content, timestamp) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'Yare yare daze... Great game!', '2024-01-10 12:00:00'),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'WRYYYYY! Amazing stands!', '2024-01-11 13:30:00'),
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 'This is... Requiem. Awesome gameplay!', '2024-01-12 15:45:00');

-- Insert into `logs` table 
INSERT INTO logs (value, timestamp) VALUES
('User JotaroKujo logged in', '2024-01-05 10:00:00'),
('User DIOBrando purchased Heaven\'s Bundle', '2024-01-06 11:30:00'),
('User GiornoGiovanna pulled from Passione Gang Pool', '2024-01-07 15:45:00'),
('PvP match started: JotaroKujo vs DIOBrando', '2024-01-15 12:00:00'),
('New auction created for Star Platinum', '2024-01-20 09:00:00');
