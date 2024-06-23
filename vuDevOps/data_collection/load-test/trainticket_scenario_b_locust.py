from locust import HttpUser, TaskSet, task, between
import base64
import random
import time
import json
import base64
import string
from datetime import datetime

class BookTicketUserBehavior(TaskSet):
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
        self.trip_id = "G1234"
        self.start_station = "Shang Hai"
        self.terminal_station = "Su Zhou"



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
        headers = {"Accept": "application/json",
                "Content-Type": "application/json"}
        body = {
            "departureTime": date,
            "endPlace": "Shang Hai",
            "startingPlace": "Su Zhou"
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

    def start_booking(self, date):
        headers = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        response = self.client.get(
            url="/client_ticket_book.html?tripId=" + self.trip_id + "&from=" + self.start_station + "&to=" + self.terminal_station + "&seatType=2&seat_price=50.0" + "&date=" + date,
            headers=headers)
        if response.status_code == 200:
            print("Starting booking process...")
        else:
            print(f"Failed to go to booking page: {response.status_code}, {response.text}")

    def select_contact(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        response = self.client.get(
            url="/api/v1/contactservice/contacts/account/" + self.user_id,
            headers=head)
        # print(response.json())
        data = response.json()["data"]
        # print(json.dumps(data))
        if len(data) == 0:
            response = self.client.post(
                url="/api/v1/contactservice/contacts",
                headers=head,
                json={
                    "name": self.user_id, "accountId": self.user_id, "documentType": "1",
                    "documentNumber": self.user_id, "phoneNumber": "123456"})

            data = response.json()["data"]
            self.contactid = data["id"]
        else:
            self.contactid = data[0]["id"]

        # print(self.contactid)

    def finish_booking(self, date):
        headers = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        body = {
            "accountId": self.user_id,
            "contactsId": self.contactid,
            "tripId": self.trip_id,
            "seatType": "2",
            "date": date,
            "from": self.start_station,
            "to": self.terminal_station,
            "assurance": "0",
            "foodType": 1,
            "foodName": "Bone Soup",
            "foodPrice": 2.5,
            "stationName": "",
            "storeName": ""
        }

        response = self.client.post(
            url=self.host + "/api/v1/preserveservice/preserve",
            headers=headers,
            json=body)
        if response.status_code == 200:
            print("Booking successful!")
        else:
            print(f"Failed to finish booking: {response.status_code}, {response.text}")
    
    def order(self):
        headers = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        
        response = self.client.post(
            url="/api/v1/orderservice/order/refresh",
            headers=headers,
            json={
                "loginId": self.user_id, "enableStateQuery": "false", "enableTravelDateQuery": "false",
                "enableBoughtDateQuery": "false", "travelDateStart": "null", "travelDateEnd": "null",
                "boughtDateStart": "null", "boughtDateEnd": "null"})

        data = response.json()["data"]
        # print(data)
        if response.status_code == 200:
            print("Order successful!")
    
        for orders in data:
            if orders["status"] == 1:
                self.paid_orderid = orders["id"]
                break
        for orders in data:
            if orders["status"] == 0:
                self.orderid = orders["id"]

    @task
    def browse_tickets(self):
        self.login()

        today = datetime.today()
        date = today.strftime('%Y-%m-%d')

        self.search_ticket(date)
        wait_time = random.uniform(1, 3)
        time.sleep(wait_time)
        self.start_booking(date)
        time.sleep(wait_time)
        self.select_contact()
        time.sleep(wait_time)
        self.finish_booking(date)
        time.sleep(wait_time)
        self.order()
        

class TrainTicketUser(HttpUser):
    tasks = [BookTicketUserBehavior]