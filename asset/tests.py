from django.test import TestCase, Client
from user.models import User
from department.models import Department, Entity
import hashlib
from django.contrib.auth.hashers import make_password, check_password
from urllib.parse import urlencode

class esTest(TestCase):
    def setUp(self) -> None:
        et = Entity.objects.create(name="et")
        dep = Department.objects.create(name="dep", entity=1, admin=1)
        ep = User.objects.create(name="ep", password=make_password("ep"), 
                                 identity=3, entity=1, department=1)
        op1 = User.objects.create(name="op1", password=make_password("op1"), 
                                 identity=4, entity=1, department=1)
        op2 = User.objects.create(name="op2", password=make_password("op2"), 
                                 identity=4, entity=1, department=1)
        self.login("ep", "ep")
        
    def login(self, name, pw):
        payload = {
            "name": name,
            "password": pw
        }
        return self.client.post("/user/login", data=payload, content_type="application/json")
    
    def logout(self, name):
        payload = {
            "name": name
        }
        return self.client.post("/user/logout", data=payload, content_type="application/json")        
    
    def test_post_class(self):
        resp = self.client.post("/asset/assetclass", {"name": "assetclass", "type": 1})
        # print(resp.json())
        self.assertEqual(resp.json()["code"], 0)
        
    def test_post(self):
        self.client.post("/asset/assetclass", {"name": "assetclass", "type": 1})
        self.client.post("/asset/assetclass", {"name": "yuanshen", "type": 0})
        resp = self.client.post("/asset/post", 
                                [{"category": "assetclass", "name": "keqing", "life": 100, "number": 1000, "price": 1000}, {"category": "yuanshen", "name": "keqi", "life": 100, "price": 1000}]
                                ,content_type="application/json")
        # print(resp.json())
        self.assertEqual(resp.json()["code"], 0)
        
    def test_get(self):
        self.client.post("/asset/assetclass", {"name": "assetclass", "type": 1})
        self.client.post("/asset/assetclass", {"name": "yuanshen", "type": 0})
        self.client.post("/asset/post", [{"category": "assetclass", "name": "keqing", "life": 100, "number": 1000, "price": 1000}, {"category": "yuanshen", "name": "keqi", "life": 100, "price": 1000}]
                         ,content_type="application/json")
        resp = self.client.get("/asset/get")
        print(resp.json())
        self.assertEqual(resp.json()["data"], [{'category': 'assetclass', 'type': True, 'name': 'keqing', 'description': ''}, {'category': 'yuanshen', 'type': False, 'name': 'keqi', 'description': ''}])
        
    def test_delete(self):
        self.client.post("/asset/assetclass", {"name": "assetclass", "type": 1})
        self.client.post("/asset/assetclass", {"name": "yuanshen", "type": 0})
        self.client.post("/asset/post", [{"category": "assetclass", "name": "keqing", "life": 100, "number": 1000, "price": 1000}, {"category": "yuanshen", "name": "keqi", "life": 100, "price": 1000}]
                         ,content_type="application/json")
        resp = self.client.delete("/asset/delete", ["keqi", "keqing"], content_type="application/json")
        # print(resp.json())
        self.assertEqual(resp.json()["code"], 0)
    
    # def test_get_attributes(self):
    #     self.client.post("/asset/assetclass", {"name": "assetclass", "type": 1})
    #     self.client.post("/asset/assetclass", {"name": "yuanshen", "type": 0})
    #     resp = self.client.post("/asset/post", [{"category": "assetclass", "name": "keqing", "life": 100, "number": 1000, "price": 1000, "additional": {"abab": 1}},
    #                                      {"category": "yuanshen", "name": "keqi", "life": 100, "price": 1000, "additional": {"cdcd": 2}}]
    #                      ,content_type="application/json")
    #     resp = self.client.get("/asset/getdetail", {"name": "keqi"})
    #     resp = self.client.get("/asset/get", {})
    #     print(resp.json())
        
        
        
        
