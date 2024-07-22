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
        self.gender = 0
        self.documentType = 1
        self.documentNum = ""
        self.email = ""
        self.bearer = ""
        self.user_id = ""
        self.host = "http://145.108.225.16:8080"
        self.contactid = ""
        self.orderid = ""
        self.paid_orderid = ""
        self.trip_id = "D1345"
        self.start_station = "Shang Hai"
        self.terminal_station = "Su Zhou"

    def addUser(self):
        self.client.get(url="/adminlogin.html")
        headers = {"Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json;charset=utf-8"
        }
        body = {
            "username":"admin",
            "password":"222222"
        }

        response = self.client.post(url ="/api/v1/users/login",
                                    headers = headers,
                                    json = body)

        if response.status_code == 200:
            try:
                response_as_json = response.json()["data"]
                token = response_as_json["token"]
                self.bearer = "Bearer " + token
                self.user_id = response_as_json["userId"]
                # print("Logged in successfully!")

                header2 = {"Accept" : "application/json, text/plain, */*",
                           "Authorization": self.bearer}
                self.client.get(url= "/api/v1/adminorderservice/adminorder", 
                                headers = header2)
                self.client.get(url="/api/v1/adminuserservice/users",
                                headers= header2)
                
                header3 = {"Accept" : "application/json, text/plain, */*",
                           "Content-Type" : "application/json;charset=utf-8",
                           "Authorization": self.bearer}
                new_user = {"userName":self.username,"password":self.password,"gender":self.gender,"email":self.email,"documentType":self.documentType,"documentNum":self.documentNum}
                
                response = self.client.post(url="/api/v1/adminuserservice/users",
                                 headers = header3,
                                 json= new_user)
                    
                self.client.get(url="/admin_user.html")
                self.client.get(url="/api/v1/adminuserservice/users",
                                headers=header2)               

            except (ValueError, KeyError) as e:
                # print(f"Error parsing login response: {e}, {response.text}")
                return
            

    def login(self):
        # Perform login and store the token
        # print("Trying to log in...")
        self.client.get(url="/client_login.html")

        verifycode_header = {"Accept" : "image/avif,image/webp,*/*"}
        self.client.get(url="/api/v1/verifycode/generate",
                        headers = verifycode_header)

        login_headers = {"Accept": "application/json, text/javascript, */*; q=0.01",
                         "X-Requested-With" : "XMLHttpRequest",
                         "Content-Type": "application/json"
        }
        
        response = self.client.post(url="/api/v1/users/login",
                                 headers=login_headers,
                                 json={
                                     "username": self.username,
                                     "password": self.password,
                                     "verifyCode": "1234"})

        if response.status_code == 200:
            try:
                response_as_json = response.json()["data"]
                if response_as_json is not None:
                    token = response_as_json["token"]
                    self.bearer = "Bearer " + token
                    self.user_id = response_as_json["userId"]
                    # print("Logged in successfully!")
            except (ValueError, KeyError) as e:
                # print(f"Error parsing login response: {e}, {response.text}")
                return

    def search_ticket(self, date):
        self.client.get(url="/index.html")

        verifycode_header = {"Accept" : "image/avif,image/webp,*/*"}
        self.client.get(url="/api/v1/verifycode/generate",
                        headers = verifycode_header)

        headers = {"Accept": "application/json, text/javascript, */*; q=0.01",
                   "X-Requested-With" : "XMLHttpRequest",
                   "Content-Type": "application/json"}
        body = {
            "departureTime": date,
            "endPlace": self.terminal_station,
            "startingPlace": self.start_station
        }
        
        response = self.client.post(
            url= "/api/v1/travelservice/trips/left",
            headers=headers,
            json=body)

        if response.status_code == 200:
            try:
                data = response.json()["data"]
                if not data:
                    # print("No data from travelservice, trying travel2service")
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
                # print(f"Error parsing search ticket response: {e}")
                return
        # else:
        #     # print(f"Failed to search tickets: {response.status_code}, {response.text}")
        #     return

    def start_booking(self, date):
        headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Content-Type": "application/json"}
        response = self.client.get(
            url="/client_ticket_book.html?tripId=" + self.trip_id + "&from=" + self.start_station + "&to=" + self.terminal_station + "&seatType=2&seat_price=50.0" + "&date=" + date,
            headers=headers)
        # if response.status_code != 200:
        #     print(f"Failed to go to booking page: {response.status_code}, {response.text}")
        #     return
            

    def select_contact(self):
        head = {"Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With" : "XMLHttpRequest",
                "Content-Type": "application/json", "Authorization": self.bearer}
        response = self.client.get(
            url="/api/v1/contactservice/contacts/account/" + self.user_id,
            headers=head)
        # print(response.json())
        if response.status_code == 200:
            try:
                data = response.json()["data"]
                # print(json.dumps(data))
                if len(data) == 0:
                    response = self.client.post(
                        url="/api/v1/contactservice/contacts",
                        headers=head,
                        json={
                            "name": self.username, "accountId": self.user_id, "documentType": "1",
                            "documentNumber": "P", "phoneNumber": "1321"})

                    data = response.json()["data"]
                    self.contactid = data["id"]
                else:
                    self.contactid = data[0]["id"]
            #       print(self.contactid)
            except Exception as e:
                # print(f"Error processing JSON data: {e}")
                # print(f"Response content: {response.text}")
                return

    def finish_booking(self, date):
        # assurance = self.client.get(url)

        headers = {"Accept": "application/json, text/javascript, */*; q=0.01",
                   "X-Requested-With" : "XMLHttpRequest",
                   "Content-Type": "application/json", "Authorization": self.bearer}
        body = {
            "accountId": self.user_id,
            "contactsId": self.contactid,
            "tripId": self.trip_id,
            "seatType": "2",
            "date": date,
            "from": self.start_station,
            "to": self.terminal_station,
            "assurance": "1",
            "foodType": 2,
            "foodName": "Bone Soup",
            "foodPrice": 2.5,
            "stationName": "",
            "storeName": ""
        }
        # print(self.username)
        # print(self.user_id)
        # print(self.trip_id)
        # print(self.bearer)
        response = self.client.post(
            url="/api/v1/preserveservice/preserve",
            headers=headers,
            json=body)
        if response.status_code == 200:
            print("Booking successful!")
        # else:
        #     print(f"Failed to finish booking: {response.status_code}, {response.text}")
    
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

        if response.status_code == 200:
            try:
                data = response.json()["data"]
                # print(data)
                # if response.status_code == 200:
                #     print("Order successful!")
            
                for orders in data:
                    if orders["status"] == 1:
                        self.paid_orderid = orders["id"]
                        break
                for orders in data:
                    if orders["status"] == 0:
                        self.orderid = orders["id"]
            except Exception as e:
                # print(f"Error processing JSON data: {e}")
                # print(f"Response content: {response.text}")
                return

    @task
    def browse_tickets(self):
        self.username = ''.join(random.choice(string.ascii_uppercase) for _ in range(4))
        self.password = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
        self.gender = random.randint(0,1)
        self.documentType = random.randint(0,1)
        self.documentNum = ''.join(random.choice(string.ascii_uppercase) for _ in range(4))
        self.email = ''.join(random.choice(string.ascii_uppercase) for _ in range(4)) + '@gmail.com'
        
        self.addUser()
        
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
        

class Web(HttpUser):
    tasks = [BookTicketUserBehavior]