from locust import HttpUser, TaskSet, task, between
import base64
import random
import time
import json
import requests
import string

class TrainTicketUserBehavior(TaskSet):
    def __init__(self):
        self.username = "fdse_microservice"
        self.password = "111111"
        self.bearer = ""
        self.user_id = ""
        self.host = "http://145.108.225.16:8080"
        self.contactid = ""
        self.orderid = ""
        self.paid_orderid = ""


    def on_start(self):
        self.login()

    def login(self):
        # Perform login and store the token
        print("Trying to log in")
        headers = {"Accept": "application/json",
                "Content-Type": "application/json"
        }
        # response = self.client.post(url="/api/v1/users/login", headers=headers, json={
        #     "username": 'fdse_microservice',
        #     "password": '111111',
        #     "verifiCode": '1234'
        # })
        response = requests.post(url=self.host + "/api/v1/users/login",
                                 headers=headers,
                                 json={
                                     "username": self.username,
                                     "password": self.password})
        print(response.text)
        response_as_json = response.json()["data"]
        if response_as_json is not None:
            token = response_as_json["token"]
            self.bearer = "Bearer " + token
            self.user_id = response_as_json["userId"]
        # if response.status_code == 200:
        #     self.token = response.json().get("token")   
        #     self.userId = response.json().get("userId")
        #     # self.client.get("/login", headers={"Authorization":"Basic %s" % base64string})
        #     # headers: {"Authorization": "Bearer " + sessionStorage.getItem("client_token")}
        #     print("Logged in successfully!")
        # else:
        #     print(f"Failed to login: {response.text}")

    def search_ticket(self, date, from_station, to_station):
        headers = {"Accept": "application/json",
                "Content-Type": "application/json"}
        body = {
            "startingPlace": from_station,
            "endPlace": to_station,
            "departureTime": date
        }
        response = requests.post(
            url=self.host + "/api/v1/travelservice/trips/left",
            headers=headers,
            json=body)
        if not response.json()["data"]:
            print("travel 2 service")
            response = requests.post(
                url=self.host + "/api/v1/travel2service/trips/left",
                headers=headers,
                json=body)
        print(json.dumps(response.json()))
        for res in response.json()["data"]:
            self.trip_id = res["tripId"]["type"] + res["tripId"]["number"]
            self.start_station = res["startingStation"]
            self.terminal_station = res["terminalStation"]


    @task
    def browse_tickets(self):
        print("hello world")
        date = "2024-06-15"
        stations = ["Shang Hai", "Tai Yuan", "Nan Jing", "Wu Xi", "Su Zhou"]
        preview_count = random.randint(3, 9)
        for _ in range(preview_count):
            from_station, to_station = random.sample(stations, 2)
            self.search_ticket(date, from_station, to_station)
            print(from_station, to_station, date)
            wait_time = random.uniform(1, 3)
            time.sleep(wait_time)


    #     headers = {
    #         "Authorization": f"Bearer {self.token}",
    #         "Content-Type": "application/json"
    #     }
        
    #     # Send GET request to browse tickets
    #     response = self.client.get(f"/api/v1/travelservice/trips/left_tickets?departureTime={date}&startingPlace={start_city}&endPlace={destination_city}&train_type={train_type}", headers=headers)
        
    #     if response.status_code == 200:
    #         tickets = response.json().get('data', [])
    #         if tickets:
    #             selected_ticket = random.choice(tickets)
                
    #             # Preview the selected ticket a random number of times between 3-9 times
    #             preview_count = random.randint(3, 9)
    #             for _ in range(preview_count):
    #                 self.preview_ticket(selected_ticket['tripId'], headers)
    #                 wait_time = random.uniform(1, 3)
    #                 time.sleep(wait_time)
    #     else:
    #         print(f"Failed to browse tickets: {response.text}")

    # def preview_ticket(self, ticket_id, headers):
    #     response = self.client.get(f"/api/v1/travelservice/trips/{ticket_id}", headers=headers)
    #     if response.status_code == 200:
    #         print(f"Ticket {ticket_id} previewed successfully.")
    #     else:
    #         print(f"Failed to preview ticket {ticket_id}: {response.text}")

    # @task
    # def book_ticket(self):
    #     headers = {
    #         "Authorization": f"Bearer {self.token}",
    #         "Content-Type": "application/json"
    #     }
    #     ticket_data = {
    #         "tripId": "D1345",
    #         "from": "Shanghai",
    #         "to": "Beijing",
    #         "seatType": "2",
    #         "date": "2024-06-15",
    #         "assurance": 1,
    #         "foodType": 2,
    #         "stationName": "",
    #         "seatPrice": 100
    #     }
        
    #     response = self.client.post("/api/v1/preserveservice/preserve", headers=headers, json=ticket_data)
    #     if response.status_code == 200:
    #         print("Ticket booked successfully.")
    #     else:
    #         print(f"Failed to book ticket: {response.text}")

class TrainTicketUser(HttpUser):
    tasks = [TrainTicketUserBehavior]
    wait_time = between(1, 3)
