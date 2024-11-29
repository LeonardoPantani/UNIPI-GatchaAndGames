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

-- Speedwagon's Inventory (7 Stands)
INSERT INTO inventories (item_uuid, owner_uuid, stand_uuid, obtained_at, owners_no, currency_spent) VALUES
(UNHEX(REPLACE('c7b6a5d4-e3f2-1098-7654-fedcba987654', '-', '')), 
 UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')), -- Speedwagon
 UNHEX(REPLACE('1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76', '-', '')), -- Star Platinum (LEGENDARY)
 '2024-01-01', 1, 5000),
(UNHEX(REPLACE('b7a6c5d4-e3f2-1098-7654-fedcba987655', '-', '')),
 UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')),
 UNHEX(REPLACE('9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632', '-', '')), -- The World (LEGENDARY)
 '2024-01-02', 1, 5000),
(UNHEX(REPLACE('a7b6c5d4-e3f2-1098-7654-fedcba987656', '-', '')),
 UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')),
 UNHEX(REPLACE('b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85', '-', '')), -- Gold Experience (EPIC)
 '2024-01-03', 1, 3000),
(UNHEX(REPLACE('97b6c5d4-e3f2-1098-7654-fedcba987657', '-', '')),
 UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')),
 UNHEX(REPLACE('8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7', '-', '')), -- Crazy Diamond (EPIC)
 '2024-01-04', 1, 3000),
(UNHEX(REPLACE('87b6c5d4-e3f2-1098-7654-fedcba987658', '-', '')),
 UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')),
 UNHEX(REPLACE('c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f', '-', '')), -- Silver Chariot (RARE)
 '2024-01-05', 1, 2000),
(UNHEX(REPLACE('77b6c5d4-e3f2-1098-7654-fedcba987659', '-', '')),
 UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')),
 UNHEX(REPLACE('d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a', '-', '')), -- Hermit Purple (COMMON)
 '2024-01-06', 1, 1000),
(UNHEX(REPLACE('67b6c5d4-e3f2-1098-7654-fedcba987660', '-', '')),
 UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')),
 UNHEX(REPLACE('e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b', '-', '')), -- Magicians Red (RARE)
 '2024-01-07', 1, 2000);

-- AdminUser's Inventory (7 different Stands)
INSERT INTO inventories (item_uuid, owner_uuid, stand_uuid, obtained_at, owners_no, currency_spent) VALUES
(UNHEX(REPLACE('57b6c5d4-e3f2-1098-7654-fedcba987661', '-', '')),
 UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')), -- AdminUser
 UNHEX(REPLACE('c3d4e5f6-a7b8-9012-3456-7890abcdef12', '-', '')), -- Made in Heaven (LEGENDARY)
 '2024-01-08', 1, 5000),
(UNHEX(REPLACE('47b6c5d4-e3f2-1098-7654-fedcba987662', '-', '')),
 UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')),
 UNHEX(REPLACE('a1b2c3d4-e5f6-7890-1234-567890abcdef', '-', '')), -- King Crimson (LEGENDARY)
 '2024-01-09', 1, 5000),
(UNHEX(REPLACE('37b6c5d4-e3f2-1098-7654-fedcba987663', '-', '')),
 UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')),
 UNHEX(REPLACE('b2c3d4e5-f6a7-8901-2345-67890abcdef1', '-', '')), -- Killer Queen (EPIC)
 '2024-01-10', 1, 3000),
(UNHEX(REPLACE('27b6c5d4-e3f2-1098-7654-fedcba987664', '-', '')),
 UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')),
 UNHEX(REPLACE('e5f6a7b8-c9d0-1234-5678-90abcdef1234', '-', '')), -- Purple Haze (EPIC)
 '2024-01-11', 1, 3000),
(UNHEX(REPLACE('17b6c5d4-e3f2-1098-7654-fedcba987665', '-', '')),
 UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')),
 UNHEX(REPLACE('f6a7b8c9-d0e1-2345-6789-0abcdef12345', '-', '')), -- Sex Pistols (RARE)
 '2024-01-12', 1, 2000),
(UNHEX(REPLACE('07b6c5d4-e3f2-1098-7654-fedcba987666', '-', '')),
 UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')),
 UNHEX(REPLACE('c9d0e1f2-a3b4-5678-9012-cdef12345678', '-', '')), -- Beach Boy (COMMON)
 '2024-01-13', 1, 1000),
(UNHEX(REPLACE('f6b6c5d4-e3f2-1098-7654-fedcba987667', '-', '')),
 UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')),
 UNHEX(REPLACE('a7b8c9d0-e1f2-3456-7890-abcdef123456', '-', '')), -- Aerosmith (RARE)
 '2024-01-14', 1, 2000);