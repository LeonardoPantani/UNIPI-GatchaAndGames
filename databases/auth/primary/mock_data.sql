-- Insert into `users` table
INSERT INTO users (uuid, email, password, role) VALUES
(UNHEX(REPLACE('e3b0c442-98fc-1c14-b39f-92d1282048c0', '-', '')), 'jotaro@joestar.com', '$2b$12$XRQfYzKIQoyQXNUYU0lcB.p/YHN5YqXxEn62BH5WiK.w8Q.i5z7cy', 'USER'), -- password: star_platinum
(UNHEX(REPLACE('87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', '-', '')), 'dio.brando@world.com', '$2a$12$YUKGEXCU2rGtqnkeStuL6.3SA5IIsBdAC9qv9mrXm4Pa/mLIYPu/K', 'USER'), -- password: za_warudo
(UNHEX(REPLACE('a4f0c592-12af-4bde-aacd-94cd0f27c57e', '-', '')), 'giorno@passione.it', '$2b$12$jqb2pkG1hQ4j4xJkbYTt8el9iVraf9IOg5ODWR9cjHcVF9sttNTja', 'USER'), -- password: gold_experience
(UNHEX(REPLACE('b5c3d2e1-4f5e-6a7b-8c9d-0e1f2a3b4c5d', '-', '')), 'josuke@morioh.jp', '$2a$12$4N3oX0NTo5ccUZmCBpCx/uSe14rtSd1E/sZhbOK2eclfQ3o.gdHCa', 'USER'), -- password: crazy_diamond
(UNHEX(REPLACE('4f2e8bb5-38e1-4537-9cfa-11425c3b4284', '-', '')), 'speedwagon@foundation.org', '$2a$12$9HgqzV4s6zhKCBFRMuUGSONqS2bhIQqzpiF1U/K/VW1ofYWyU2mIa', 'ADMIN'), -- password: admin_foundation
(UNHEX(REPLACE('a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6', '-', '')), 'admin@admin.com', '$2a$12$Io8F/0QZ8hLSZ.CtqUvM0uK/jhmdXohCFXiby/nHk3ePmzNf1wRhe', 'ADMIN'); -- password: password -- additional admin user