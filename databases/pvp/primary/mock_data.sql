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