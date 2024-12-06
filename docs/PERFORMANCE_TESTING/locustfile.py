import os
import random
import matplotlib.pyplot as plt
from collections import defaultdict
from locust import HttpUser, between, task, SequentialTaskSet, events
import numpy as np


######################################### QUESTO FILE E' UN ESEMPIO DI ESECUZIONE COMPLETA DELLE OPERAZIONI DI UN UTENTE SUI GACHA, 
#                             PER AVERE RIFERIMENTO SULLE DISTRIBUZIONI, USARE "locustfile_gachararity.py" #########################################




# Probabilità di creare un'asta dopo aver effettuato un acquisto --> non necessariamente ogni utente mette all'asta i propri item
AUCTION_CREATION_PROBABILITY = 0.2
DELETE_ITEM_PROBABILITY = 0.1 # Probabilità di eliminare un item dall'inventario
AUCTION_BID_PROBABILITY = 0.5 # Probabilità di fare un'offerta su un'asta

class GachaStats:
    def __init__(self):
        self.pull_results = defaultdict(int)
        self.total_pulls = 0
        self.expected_probabilities = {
            "COMMON": 0.60,
            "RARE": 0.20,
            "EPIC": 0.15,
            "LEGENDARY": 0.05
        }
        self.gacha_rarities = {
    "1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76": "COMMON",
    "9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632": "COMMON",
    "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85": "COMMON",
    "8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7": "COMMON",
    "c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f": "COMMON",
    "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a": "COMMON",
    "e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b": "COMMON",
    "f1a2b3c4-d5e6-f7a8-b9c0-1d2e3f4a5b6c": "COMMON",
    "a1b2c3d4-e5f6-7890-1234-567890abcdef": "COMMON",
    "b2c3d4e5-f6a7-8901-2345-67890abcdef1": "COMMON",
    "c3d4e5f6-a7b8-9012-3456-7890abcdef12": "COMMON",
    "d4e5f6a7-b8c9-0123-4567-890abcdef123": "COMMON",
    "e5f6a7b8-c9d0-1234-5678-90abcdef1234": "COMMON",
    "f6a7b8c9-d0e1-2345-6789-0abcdef12345": "COMMON",
    "a7b8c9d0-e1f2-3456-7890-abcdef123456": "COMMON",
    "b8c9d0e1-f2a3-4567-8901-bcdef1234567": "COMMON",
    "c9d0e1f2-a3b4-5678-9012-cdef12345678": "COMMON",
    "d0e1f2a3-b4c5-6789-0123-def123456789": "COMMON",
    "e1f2a3b4-c5d6-7890-1234-ef123456789a": "COMMON",
    "f2a3b4c5-d6e7-8901-2345-f123456789ab": "COMMON",
    "a9b0c1d2-e3f4-5678-9012-cdef345678ab": "COMMON",
    "b0c1d2e3-f4a5-6789-0123-def456789abc": "COMMON",
    "c1d2e3f4-a5b6-7890-1234-5678abcdef90": "COMMON",
    "a3b4c5d6-e7f8-9012-3456-123456789abc": "RARE",
    "b4c5d6e7-f8a9-0123-4567-23456789abcd": "RARE",
    "c5d6e7f8-a9b0-1234-5678-3456789abcde": "RARE",
    "d5e6f7a8-b9c0-1234-5678-90abcdef1234": "RARE",
    "e6f7a8b9-c0d1-2345-6789-0abcdef12345": "RARE",
    "f7a8b9c0-d1e2-3456-7890-abcdef123456": "RARE",
    "a8b9c0d1-e2f3-4567-8901-123456789abc": "RARE",
    "b9c0d1e2-f3a4-5678-9012-23456789abcd": "RARE",
    "c0d1e2f3-a4b5-6789-0123-3456789abcde": "RARE",
    "d1e2f3a4-b5c6-7890-1234-456789abcdef": "RARE",
    "e2f3a4b5-c6d7-8901-2345-56789abcdef0": "RARE",
    "f3a4b5c6-d7e8-9012-3456-6789abcdef01": "RARE",
    "a4b5c6d7-e8f9-0123-4567-789abcdef012": "RARE",
    "b5c6d7e8-f9a0-1234-5678-89abcdef0123": "RARE",
    "c6d7e8f9-a0b1-2345-6789-9abcdef01234": "RARE",
    "d7e8f9a0-b1c2-3456-789a-bcdef0123456": "RARE",
    "e8f9a0b1-b2c3-4567-89cd-ef123456789a": "RARE",
    "f9a0b1c2-c3d4-5678-9abc-def23456789b": "RARE",
    "a0b1c2d3-d4e5-6789-0bca-ef3456789abc": "RARE",
    "e8f9a0b1-c2d3-4567-89ab-cdef12345678": "EPIC",
    "f9a0b1c2-d3e4-5678-90ab-def123456789": "EPIC",
    "a0b1c2d3-e4f5-6789-0abc-ef123456789a": "EPIC",
    "b1c2d3e4-f5a6-7890-1abc-f0123456789b": "EPIC",
    "c2d3e4f5-a6b7-8901-2bcd-0123456789ac": "EPIC",
    "d3e4f5a6-b7c8-9012-3cde-23456789abcd": "EPIC",
    "e4f5a6b7-c8d9-0123-4def-3456789abcde": "EPIC",
    "f5a6b7c8-d9e0-1234-5f01-456789abcdef": "EPIC",
    "a6b7c8d9-e0f1-2345-6012-56789abcdef1": "EPIC",
    "b7c8d9e0-f123-4567-7123-6789abcdef12": "EPIC",
    "c8d9e0f1-2345-6789-8123-789abcdef123": "EPIC",
    "d9e0f1a2-3456-789a-9234-89abcdef1234": "EPIC",
    "e0f1a2b3-4567-89ab-a345-90abcdef1235": "EPIC",
    "e8f9a0b1-f2c3-4567-89ab-cdef6789abcd": "EPIC",
    "f9a0b1c2-a3d4-5678-90bc-ddef12345678": "EPIC",
    "a0b1c2d3-d4e5-6789-0bca-ef3456789fff": "EPIC",
    "f1a2b3c4-5678-9abc-b456-0123456789ef": "LEGENDARY",
    "a2b3c4d5-6789-0abc-c567-123456789aef": "LEGENDARY",
    "b3c4d5e6-7890-1abc-d678-23456789abef": "LEGENDARY",
    "c4d5e6f7-8901-2bcd-e789-3456789abcef": "LEGENDARY",
    "d5e6f7a8-9012-3cde-f890-456789abcdef": "LEGENDARY",
    "e6f7a8b9-0123-4def-9012-56789abcdef0": "LEGENDARY",
    "f7a8b9c0-1234-5ef0-0123-6789abcdef01": "LEGENDARY",
    "e9f0a1b2-b3c4-5def-6789-0abcde123456": "LEGENDARY",
    "f1a2b3c4-b4c5-6789-9abc-abcdef012345": "LEGENDARY",
}

        self.pool_ids = ["bundle_heavenEUR"]

    def record_pull(self, gacha_uuid):
        rarity = self.gacha_rarities.get(gacha_uuid)
        print("Rarity:",rarity)
        if rarity:
            self.pull_results[rarity] += 1
            self.total_pulls += 1

    def get_distribution(self):
        if self.total_pulls == 0:
            return {}
        return {rarity: (count / self.total_pulls) for rarity, count in self.pull_results.items()}



gacha_stats = GachaStats()

class GachaTaskSequence(SequentialTaskSet):
    registered= False
    count = 0
    auth_token = None
    has_credits = False
    pools_list = ["bundle_heavenEUR"]
    inventory = []
    auction_created = False
    auction_id = None

    def on_start(self):  
        if not self.registered:
            username = f"testuser_{random.randint(1, 100000000000)}"
            self.credentials = {
                "username": username,
                "email": f"{username}@example.com",
                "password": "test1234567"
            }
            register_response = self.client.post("/auth/register", json=self.credentials, verify=False, name="/auth/register")
            if register_response.status_code == 201:
                auth_header = register_response.headers.get("Authorization")
                if auth_header and "Bearer" in auth_header:
                    self.auth_token = auth_header.split("Bearer ")[1]
                    self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.credentials["uuid"] = register_response.json().get("uuid")
                else:
                    response_json = register_response.json()
                    self.auth_token = response_json.get("token") or response_json.get("access_token")

                if self.auth_token:
                    self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    print("Registrazione effettuata con successo")
                self.registered = True 

    
    @task
    def view_gacha_pools(self):
        self.client.get("/gacha/pools", verify=False, name="/gacha/pools")

    def _buy_bundle(self): 
        response = self.client.post(f"/currency/buy/{random.choice(self.pools_list)}",catch_response=True ,verify=False, name="/currency/buy")
        if response.status_code != 200:
            response.failure(f"Failed to buy bundle: {response.status_code}")
            return False  # Indica l'errore nell'acquisto del bundle
        return True  # Acquisto del bundle avvenuto con successo

    def _add_currency(self): # Nuova funzione per aggiungere currency
        response = self.client.post("/currency/buy/add_myself_some_currency", verify=False, name="/currency/buy_myself_some_currency")
        if response.status_code != 200:
            response.failure(f"Failed to add currency: {response.status_code}")
            return False
        return True


    @task
    def view_gacha_list(self):
        self.client.get("/gacha/list", params={"not_owned": "true"}, verify=False, name="/gacha/list")

    @task
    def pull_gacha(self):
        if self._buy_bundle():
            if self._add_currency():
                
                with self.client.post(f"/gacha/pull/pool_joestar", verify=False, catch_response=True, name="/gacha/pull") as response:
                    if response.status_code == 200:
                        pull_data = response.json()
                        print("Pull data:",pull_data)
                        if "gacha_uuid" in pull_data.get("gacha", {}):
                            gacha_uuid = pull_data["gacha"]["gacha_uuid"]
                            print("Gacha UUID:",gacha_uuid)
                            gacha_stats.record_pull(gacha_uuid)
                        response.success()
                    else:
                        response.failure(f"Failed to pull: {response.status_code}")

    @task
    def view_gacha_details(self):
        gachas_id_list = list(gacha_stats.gacha_rarities.keys()) #get id from gacha_rarities
        gacha_id = random.choice(gachas_id_list)
        self.client.get(f"/gacha/{gacha_id}", verify=False, name="/gacha/details")

    @task
    def _get_user_item_id(self):
        """Fetch user's inventory and return a random item UUID"""
        response = self.client.get("/inventory?page_number=1", verify=False, name="/inventory?page_number=1")
        if response.status_code == 200:
            inventory_data = response.json()
            print("The inventory data is: ", inventory_data)
            if inventory_data:
                self.inventory = [item.get("item_id") for item in inventory_data if "item_id" in item]
                return random.choice(self.inventory) if self.inventory else None
        return None

    @task
    def get_inventory_item_info(self):
        if self.inventory:
            item_id = random.choice(self.inventory)
            self.client.get(f"/inventory/{item_id}", verify=False, name="/inventory/{item_id}")


    @task
    def create_auction(self):
        if not self.auction_created and random.random() < AUCTION_CREATION_PROBABILITY: # Create only one auction per user + random auction creation condition
            item_id = self._get_user_item_id()
            if item_id:
                response = self.client.post(f"/auction/create?starting_price=10&inventory_item_owner_id={self.credentials['uuid']}&inventory_item_id={item_id}", verify=False, name="/auction/create")
                print("Response status code:",response.status_code)
                if response.status_code == 201:
                    auction_data = response.json()
                    self.auction_id = auction_data.get("auction_uuid")
                    self.auction_created = True
                print("auction created:",self.auction_created)


    def get_auctions_list(self):
        response=self.client.get("/auction/list?status=open&page_number=1", verify=False, name="/auction/list?status=open")
        return response

    @task
    def bid_on_auction(self): # Updated bid_on_auction task
        if random.random() < AUCTION_BID_PROBABILITY:     
            if self._buy_bundle():
                self._add_currency()
                response = self.get_auctions_list()
            if response.status_code == 200:
                auctions = response.json()

                if auctions:
                    suitable_auctions = [
                        auction for auction in auctions if auction.get("inventory_item_owner_id") != self.credentials["uuid"]
                    ]

                    if suitable_auctions:
                        chosen_auction = random.choice(suitable_auctions)
                        auction_id = chosen_auction.get("auction_uuid")
                        print(auction_id)
                        print(f"/auction/bid/{auction_id}")
                        self._add_currency()
                        self.client.post(
                            f"/auction/bid/{auction_id}?bid=1",
                            verify=False,
                            name=f"/auction/bid/{auction_id}"
                        )

    @task
    def get_auction_status(self):
        if self.auction_id:
            self.client.get(f"/auction/{self.auction_id}", verify=False, name="/auction/{auction_id}")


    @task
    def get_auctions_history(self):
        self.client.get(f"/auction/history?page_number=1", verify=False, name="/auction/history")


    def get_all_auctions(self):
        all_auctions = []
        page_number = 1
        max_pages=1000000
        while True and page_number<=max_pages:
            response = self.client.get(f"/auction/list?status=open&page_number={page_number}", verify=False, name="/auction/list?status=open")
            if response.status_code != 200:
                print(f"Error getting auction list (page {page_number}): {response.status_code}")
                break  # Stop if there's an error fetching a page

            auctions = response.json()
            if not auctions:  # Check if the returned list is empty
                break  # Stop when a page returns an empty list

            all_auctions.extend(auctions)
            page_number += 1
        if page_number>max_pages:
            print("Max pages reached")
            exit()
        return all_auctions

    @task
    def delete_item(self):
        if random.random() < DELETE_ITEM_PROBABILITY:
            item_to_delete = self._get_user_item_id()
            if item_to_delete:
                all_auctions = self.get_all_auctions()  # Get all auctions across all pages
                item_in_auction = any(auction.get("inventory_item_id") == item_to_delete for auction in all_auctions)

                if not item_in_auction:
                    self.client.delete(f"/inventory/?inventory_item_owner_id={self.credentials['uuid']}&inventory_item_id={item_to_delete}", verify=False, name=f"/inventory/?inventory_item_owner_id={self.credentials['uuid']}&inventory_item_id={item_to_delete}")
                    print("url",f"/inventory/?inventory_item_owner_id={self.credentials['uuid']}&inventory_item_id={item_to_delete}")
                else:
                    print(f"Item {item_to_delete} is currently in an auction and cannot be deleted.")

        

class GachaPlayer(HttpUser):
    wait_time = between(1, 3)
    tasks = [GachaTaskSequence]


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        os.system("locust -f locustfile.py --host=http://localhost:8080")
    else:
        os.system(f"locust -f locustfile.py --host=http://localhost:8080 {' '.join(sys.argv[1:])}")