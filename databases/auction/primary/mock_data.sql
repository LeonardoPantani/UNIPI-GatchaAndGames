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