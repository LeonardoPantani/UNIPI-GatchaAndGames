-- Insert into `feedbacks` table
INSERT INTO feedbacks (user_uuid, content, timestamp) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'Yare yare daze... Great game!', '2024-01-10 12:00:00'),
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'WRYYYYY! Amazing stands!', '2024-01-11 13:30:00'),
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 'This is... Requiem. Awesome gameplay!', '2024-01-12 15:45:00');