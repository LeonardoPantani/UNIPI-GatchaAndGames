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
INSERT INTO gacha_pools (codename, public_name, probability_common, probability_rare, probability_epic, probability_legendary, price) VALUES
('pool_joestar', 'Joestar Legacy Pool', 0.50, 0.30, 0.15, 0.05, 1000),
('pool_passione', 'Passione Gang Pool', 0.45, 0.35, 0.15, 0.05, 1200),
('pool_duwang', 'Morioh Pool', 0.40, 0.35, 0.20, 0.05, 1500),
('pool_pucci', 'Heaven Pool', 0.30, 0.30, 0.30, 0.10, 2000),
('pool_valentine', 'Patriot Pool', 0.40, 0.30, 0.20, 0.10, 1800);


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
