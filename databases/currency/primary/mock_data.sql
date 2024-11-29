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