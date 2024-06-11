import base64
import time

from locust import HttpUser, TaskSet, task
from random import randint, choice


class WebTasks(TaskSet):

    @task
    def load(self):
        # base64string = base64.encodestring('%s:%s' % ('user', 'password')).replace('\n', '')

        credentials = bytes('%s:%s' % ('user', 'password'), 'utf-8')
        base64string = base64.b64encode(credentials).decode('utf-8')
        base64string = base64string.replace('\n', '')
        catalogue = self.client.get("/catalogue")

        if catalogue.status_code == 200:
            catalogue = catalogue.json()
            # Process the 'catalogue' data
        else:
            print("Request failed with status code:", catalogue.status_code)


        category_item = None
        for _ in range(randint(0, 9)):
            category_item = choice(catalogue)
            time.sleep(randint(1, 3))
            
        if not category_item:
            item_id = 1
        else:
            item_id = category_item["id"]

        self.client.get("/")
        self.client.get("/login", headers={"Authorization":"Basic %s" % base64string})
        self.client.get("/category.html")
        self.client.get("/detail.html?id={}".format(item_id))
        self.client.delete("/cart")
        self.client.post("/cart", json={"id": item_id, "quantity": 1})
        self.client.get("/basket.html")
        self.client.post("/orders")


class Web(HttpUser):
    tasks = [WebTasks]

    min_wait = 0
    max_wait = 0
