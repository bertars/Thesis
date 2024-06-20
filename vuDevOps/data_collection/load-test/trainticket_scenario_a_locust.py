from locust import HttpUser, TaskSet, task, between
import base64
import random
import time
import json
# import requests
import base64
import string
from datetime import datetime

class TrainTicketUserBehavior(TaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.username = "fdse_microservice"
        self.password = "111111"
        self.bearer = ""
        self.user_id = ""
        self.host = "http://145.108.225.16:8080"
        self.contactid = ""
        self.orderid = ""
        self.paid_orderid = ""


    def login(self):
        # Perform login and store the token
        print("Trying to log in...")

        headers = {"Accept": "application/json",
                "Content-Type": "application/json"
        }

        response = self.client.post(url="/api/v1/users/login",
                                 headers=headers,
                                 json={
                                     "username": self.username,
                                     "password": self.password,
                                     "verifyCode": "1234"})

        if response.status_code == 200:
            try:
                response_as_json = response.json()["data"]
                token = response_as_json["token"]
                self.bearer = "Bearer " + token
                self.user_id = response_as_json["userId"]
                print("Logged in successfully!")
            except (ValueError, KeyError) as e:
                print(f"Error parsing login response: {e}, {response.text}")
        else:
            print(f"Failed to login: {response.status_code}, {response.text}")

    def search_ticket(self, date):
        stations = ["Shang Hai", "Tai Yuan", "Nan Jing", "Wu Xi", "Su Zhou"]
        from_station, to_station = random.sample(stations, 2)
        headers = {"Accept": "application/json",
                "Content-Type": "application/json"}
        body = {
            "departureTime": date,
            "endPlace": to_station,
            "startingPlace": from_station
        }
        
        response = self.client.post(
            url= "/api/v1/travelservice/trips/left",
            headers=headers,
            json=body)

        if response.status_code == 200:
            try:
                data = response.json()["data"]
                if not data:
                    print("No data from travelservice, trying travel2service")
                    response = self.client.post(
                        url="/api/v1/travel2service/trips/left",
                        headers=headers,
                        json=body)
                    data = response.json()["data"]
                print(from_station, to_station, date)
                print(json.dumps(data))
                if data is not None:
                    for res in data:
                        self.trip_id = res["tripId"]["type"] + res["tripId"]["number"]
                        self.start_station = res["startingStation"]
                        self.terminal_station = res["terminalStation"]
            except (ValueError, KeyError) as e:
                print(f"Error parsing search ticket response: {e}")
        else:
            print(f"Failed to search tickets: {response.status_code}, {response.text}")


    @task
    def browse_tickets(self):
        self.login()

        today = datetime.today()
        date = today.strftime('%Y-%m-%d')

        preview_count = random.randint(3, 9)
        for _ in range(preview_count):
            self.search_ticket(date)
            wait_time = random.uniform(1, 3)
            time.sleep(wait_time)


class TrainTicketUser(HttpUser):
    tasks = [TrainTicketUserBehavior]
   
