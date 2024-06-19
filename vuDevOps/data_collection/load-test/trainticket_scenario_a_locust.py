from locust import HttpUser, TaskSet, task, between
import base64
import random
import time
import json
# import requests
import string

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
        print("Trying to log in")
        headers = {"Accept": "application/json",
                "Content-Type": "application/json"
        }

        response = self.client.post(url="/api/v1/users/login",
                                 headers=headers,
                                 json={
                                     "username": self.username,
                                     "password": self.password})

        if response.status_code == 200:
            try:
                response_as_json = response.json()["data"]
                token = response_as_json["token"]
                self.bearer = "Bearer " + token
                self.user_id = response_as_json["userId"]
                print("Logged in successfully!")
            except (ValueError, KeyError) as e:
                print(f"Error parsing login response: {e}")
        else:
            print(f"Failed to login: {response.status_code}, {response.text}")

    def search_ticket(self, date, from_station, to_station):
        headers = {"Accept": "application/json",
                "Content-Type": "application/json"}
        body = {
            "startingPlace": from_station,
            "endPlace": to_station,
            "departureTime": date
        }
        response = self.client.post(
            url= "/api/v1/travelservice/trips/left",
            headers=headers,
            json=body)

        if response.status_code == 200:
            try:
                data = response.json()["data"]
                if not data:
                    print("travel 2 service")
                    response = self.client.post(
                        url="/api/v1/travel2service/trips/left",
                        headers=headers,
                        json=body)
                    data = response.json()["data"]
                print(json.dumps(data))
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
        # self.login()
        print("Trying to search...")
        date = "2024-06-15"
        stations = ["Shang Hai", "Tai Yuan", "Nan Jing", "Wu Xi", "Su Zhou"]
        preview_count = random.randint(3, 9)
        for _ in range(preview_count):
            from_station, to_station = random.sample(stations, 2)
            self.search_ticket(date, from_station, to_station)
            print(from_station, to_station, date)
            wait_time = random.uniform(1, 3)
            time.sleep(wait_time)


class TrainTicketUser(HttpUser):
    tasks = [TrainTicketUserBehavior]
    wait_time = between(1, 3)
