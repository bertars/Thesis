import base64
import time

from locust import HttpUser, TaskSet, task, between
from random import randint, choice
import random


class WebTasks(TaskSet):

    @task
    def create_an_order(self):
        for _ in range(3,9):
            self.client.get("/transform")
            time.sleep(randint(1, 3))
            self.client.get("/calculate")
            time.sleep(randint(1, 3))         

class Web(HttpUser):
    tasks = [WebTasks]

    min_wait = 0
    max_wait = 0
