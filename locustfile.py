from locust import HttpUser, task, between, events
import random
import json
count=0


class GachaPlayer(HttpUser):
    wait_time = between(1, 3)
    auth_token = None
    has_credits = False
    
    def on_start(self):
        """Login before starting tests"""
        username = f"testuser_{random.randint(1,1000)}"
        self.credentials = {
            "username": username,
            "email": f"{username}@example.com", 
            "password": "test1234567"
        }
        
        # Register new user
        register_response = self.client.post(
            "/auth/register",
            json=self.credentials,
            verify=False
        )
        
        if register_response.status_code == 201:
            auth_header = register_response.headers.get("Authorization")
            if auth_header and "Bearer" in auth_header:
                self.auth_token = auth_header.split("Bearer ")[1]
                self.client.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                # Buy initial currency
                self._buy_initial_currency()

    def _buy_initial_currency(self):
        global count
        if count>=2:
            """Buy initial currency to have funds for gacha"""
            response = self.client.post(
                    "/currency/buy/add_myself_some_currency",
                    verify=False,
                    name="/currency/buy"  # Group these requests in statistics
                )
            count=0
        else:

            """Buy initial currency to have funds for gacha"""
            response = self.client.post(
                "/currency/buy/bundle_heavenEUR",
                verify=False,
                name="/currency/buy"  # Group these requests in statistics
            )
            if response.status_code == 200:
                self.has_credits = True
                count+=1

    @task(2)
    def view_gacha_pools(self):
        """Get list of available gacha pools"""
        self.client.get("/gacha/pools", 
                       verify=False,
                       name="/gacha/pools")

    @task(3)
    def view_gacha_list(self):
        """Get list of all gachas"""
        self.client.get("/gacha/list",
                       params={"not_owned": "true"},
                       verify=False,
                       name="/gacha/list")

    @task(4)
    def pull_gacha(self):
        """Pull a gacha from a pool"""
        self._buy_initial_currency()
            
        pool_ids = ["pool_joestar", "pool_passione", "pool_duwang"]
        with self.client.post(
            f"/gacha/pull/{random.choice(pool_ids)}", 
            verify=False,
            catch_response=True,
            name="/gacha/pull"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to pull gacha: {response.status_code}")


    @task(1)
    def view_gacha_details(self):
        """View details of a specific gacha"""
        # Using a real gacha UUID from your mock data
        gacha_id = "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85"  # Gold Experience from pool_passione
        self.client.get(f"/gacha/{gacha_id}",
                       verify=False,
                       name="/gacha/details")

if __name__ == "__main__":
    # Run Locust in headless mode with these parameters
    import sys
    if len(sys.argv) == 1:
        os.system("locust -f locustfile.py --host=http://localhost:8080")
    else:
        os.system(f"locust -f locustfile.py --host=http://localhost:8080 {' '.join(sys.argv[1:])}")