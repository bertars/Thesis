import base64
import time

from locust import HttpUser, TaskSet, task, between
from random import randint, choice
import random


class WebTasks(TaskSet):

    @task
    def create_an_order(self):        
        credentials = bytes('%s:%s' % ('user', 'password'), 'utf-8')
        base64string = base64.b64encode(credentials).decode('utf-8')
        base64string = base64string.replace('\n', '')
        self.client.get("/")
        self.client.get("/login", headers={"Authorization":"Basic %s" % base64string})
        time.sleep(randint(1, 3))       
        
        self.client.get("/category.html")
        catalogue = self.client.get("/catalogue")

        if catalogue.status_code == 200:
            catalogue = catalogue.json()
            # Process the 'catalogue' data
        else:
            print("Request failed with status code:", catalogue.status_code)

        category_item = None
                
        for i in range(randint(3, 9)):
            time.sleep(randint(1, 3))            
            category_item = choice(catalogue)
            if not category_item:
                item_id = 1
            else:
                item_id = category_item["id"]

            self.client.post("/cart", json={"id": item_id, "quantity": 1})
            
        self.client.get("/basket.html")
        
        time.sleep(randint(1, 3))       

        self.client.post("/orders")       

class Web(HttpUser):
    tasks = [WebTasks]

    min_wait = 0
    max_wait = 0
