-- Insert into `profiles` table
INSERT INTO profiles (uuid, username, currency, pvp_score) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'JotaroKujo', 5000, 100),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'DIOBrando', 6000, 95),
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 'GiornoGiovanna', 4500, 85),
(UNHEX(REPLACE('b5c3d2e1-4f5e-6a7b-8c9d-0e1f2a3b4c5d', '-', '')), 'JosukeHigashikata', 3500, 80),
(UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')), 'SpeedwagonAdmin', 10000, 98),
(UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')), 'AdminUser', 100000000, 999);