import base64
import time

from locust import HttpUser, TaskSet, task, between
from random import randint, choice
import random


class WebTasks(TaskSet):

    @task
    def survey_objects(self):      
        
        # Create a layer
        layer = self.client.get("/createlayer").json()
        time.sleep(randint(1,3))
        result = self.client.get("/createproject").json()
        
        # Access the 'projectId' property from the JSON
        project = result["projectId"]
        time.sleep(randint(1,3))
        
        for _ in range(randint(3,9)):
            self.client.post("/survey", json={"project" : project, "layer": layer})
            time.sleep(randint(1,3))
        
        # self.client.post("/deleteproject", json=result)     

class Web(HttpUser):
    tasks = [WebTasks]

    min_wait = 0
    max_wait = 0
