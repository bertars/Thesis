from locust import HttpUser, TaskSet, task, between
import random
import time

class TrainTicketUserBehavior(TaskSet):

    def on_start(self):
        self.login()

    def login(self):
        # Perform login and store the token
        response = self.client.post("/api/v1/login", json={
            "username": "your_username",
            "password": "your_password",
            "verifyCode": "1234"
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            print("Logged in successfully!")
        else:
            print(f"Failed to login: {response.text}")

    @task
    def browse_tickets(self):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        start_city = "Shanghai"
        destination_city = "Beijing"
        date = "2024-06-15"
        train_type = 0  
        
        # Send GET request to browse tickets
        response = self.client.get(f"/api/v1/travelservice/trips/left_tickets?departureTime={date}&startingPlace={start_city}&endPlace={destination_city}&train_type={train_type}", headers=headers)
        
        if response.status_code == 200:
            tickets = response.json().get('data', [])
            if tickets:
                selected_ticket = random.choice(tickets)
                
                # Preview the selected ticket a random number of times between 3-9 times
                preview_count = random.randint(3, 9)
                for _ in range(preview_count):
                    self.preview_ticket(selected_ticket['tripId'], headers)
                    wait_time = random.uniform(1, 3)
                    time.sleep(wait_time)
        else:
            print(f"Failed to browse tickets: {response.text}")

    def preview_ticket(self, ticket_id, headers):
        response = self.client.get(f"/api/v1/travelservice/trips/{ticket_id}", headers=headers)
        if response.status_code == 200:
            print(f"Ticket {ticket_id} previewed successfully.")
        else:
            print(f"Failed to preview ticket {ticket_id}: {response.text}")

    @task
    def book_ticket(self):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        ticket_data = {
            "tripId": "D1345",
            "from": "Shanghai",
            "to": "Beijing",
            "seatType": "2",
            "date": "2024-06-15",
            "assurance": 1,
            "foodType": 2,
            "stationName": "",
            "seatPrice": 100
        }
        
        response = self.client.post("/api/v1/preserveservice/preserve", headers=headers, json=ticket_data)
        if response.status_code == 200:
            print("Ticket booked successfully.")
        else:
            print(f"Failed to book ticket: {response.text}")

class TrainTicketUser(HttpUser):
    tasks = [TrainTicketUserBehavior]
    wait_time = between(1, 3)
