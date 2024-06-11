import base64
import time
from locust import HttpUser, TaskSet, task
from random import randint, choice


class BrowseCatalogueUser(TaskSet):    
    @task
    def browse_catalogue(self):        
        credentials = bytes('%s:%s' % ('user', 'password'), 'utf-8')
        base64string = base64.b64encode(credentials).decode('utf-8')
        base64string = base64string.replace('\n', '')
        self.client.get("/")
        self.client.get("/login", headers={"Authorization":"Basic %s" % base64string})
        time.sleep(randint(1, 3))      
        
        for i in range(randint(3,9)):
            self.client.get("/category.html")
            catalogue = self.client.get("/catalogue")

            if catalogue.status_code == 200:
                catalogue = catalogue.json()
                # Process the 'catalogue' data
            else:
                print("Request failed with status code:", catalogue.status_code)

            time.sleep(randint(1, 3))

            category_item = None
            category_item = choice(catalogue)
                
            if not category_item:
                item_id = 1
            else:
                item_id = category_item["id"]
            
            self.client.get("/detail.html?id={}".format(item_id))
            
            time.sleep(randint(1, 3))
        
class Web(HttpUser):
    tasks = [BrowseCatalogueUser]
    min_wait = 0
    max_wait = 0
