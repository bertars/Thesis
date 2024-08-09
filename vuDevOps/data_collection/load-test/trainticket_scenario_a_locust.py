from locust import HttpUser, TaskSet, task, between
import base64
import random
import time
import json
import base64
import string
from datetime import datetime
import os
import csv
import random

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

    def user_exists(self, users, username):
        for user in users:
            if user['userName'] == username:
                self.username = user['userName']
                self.password = user['password']
                return True
        return False
    
    def addUser(self, user):
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

                header2 = {"Accept" : "application/json, text/plain, */*",
                           "Authorization": self.bearer}
                self.client.get(url= "/api/v1/adminorderservice/adminorder", 
                                headers = header2)
                users_response = self.client.get(url="/api/v1/adminuserservice/users",
                                headers= header2)
                
                if users_response.status_code == 200:
                    users_data = users_response.json()
                    if "data" in users_data:
                        if self.user_exists(users_data["data"], user["username"]):
                            return
                        else:
                            header3 = {"Accept" : "application/json, text/plain, */*",
                                    "Content-Type" : "application/json;charset=utf-8",
                                    "Authorization": self.bearer}
                            new_user = {"userName":user["username"],"password":user["password"],"gender":int(user["gender"]),"email":user["email"],"documentType":int(user["documentType"]),"documentNum":user["documentNum"]}
                            
                            response = self.client.post(url="/api/v1/adminuserservice/users",
                                            headers = header3,
                                            json= new_user)
                            if response.status_code == 200:
                                self.username = user["username"]
                                self.password = user["password"]
                                self.gender = user["gender"]
                                self.email = user["email"]
                                self.documentType = user["documentType"]
                                self.documentNum = user["documentNum"]
                                
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
        stations = ["Shang Hai", "Tai Yuan", "Nan Jing", "Wu Xi", "Su Zhou"]
        from_station, to_station = random.sample(stations, 2)
        
        self.client.get(url="/index.html")

        verifycode_header = {"Accept" : "image/avif,image/webp,*/*"}
        self.client.get(url="/api/v1/verifycode/generate",
                        headers = verifycode_header)

        headers = {"Accept": "application/json, text/javascript, */*; q=0.01",
                   "X-Requested-With" : "XMLHttpRequest",
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
                    # print("No data from travelservice, trying travel2service")
                    response = self.client.post(
                        url="/api/v1/travel2service/trips/left",
                        headers=headers,
                        json=body)
                    data = response.json()["data"]
                # print(from_station, to_station, date)
                # print(json.dumps(data))
                if data is not None:
                    for res in data:
                        self.trip_id = res["tripId"]["type"] + res["tripId"]["number"]
                        self.start_station = res["startingStation"]
                        self.terminal_station = res["terminalStation"]
            except (ValueError, KeyError) as e:
                # print(f"Error parsing search ticket response: {e}")
                return
        # else:
        #     print(f"Failed to search tickets: {response.status_code}, {response.text}")

    def read_users_from_csv(self, file_path):
        users = []
        if os.path.exists(file_path):
            with open(file_path, mode='r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    users.append({
                        "username": row[0],
                        "password": row[1],
                        "gender": int(row[2]),
                        "documentType": int(row[3]),
                        "documentNum": row[4],
                        "email": row[5]
                    })
        return users
    
    @task
    def browse_tickets(self):
        # self.username = ''.join(random.choice(string.ascii_uppercase) for _ in range(4))
        # self.password = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
        # self.gender = random.randint(0,1)
        # self.documentType = random.randint(0,1)
        # self.documentNum = ''.join(random.choice(string.ascii_uppercase) for _ in range(4))
        # self.email = ''.join(random.choice(string.ascii_uppercase) for _ in range(4)) + '@gmail.com'
        users = self.read_users_from_csv("../vuDevOps/data_collection/load-test/users.csv")
        user = random.choice(users)
        self.addUser(user)
        self.login()

        today = datetime.today()
        date = today.strftime('%Y-%m-%d')

        preview_count = random.randint(3, 9)
        for _ in range(preview_count):
            self.search_ticket(date)
            wait_time = random.uniform(1, 3)
            time.sleep(wait_time)


class Web(HttpUser):
    tasks = [TrainTicketUserBehavior]
   
