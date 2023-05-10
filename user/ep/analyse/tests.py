from django.test import TestCase, Client
from user.models import User
from department.models import Department, Entity
import json
import hashlib
from django.contrib.auth.hashers import make_password, check_password

class anTest(TestCase):
    def setUp(self) -> None:
        et = Entity.objects.create(name="et")
        dep = Department.objects.create(name="dep", entity=1, admin=1)
        dep2 = Department.objects.create(name="dep2", entity=1, admin=2, parent=1)
        ep = User.objects.create(name="ep", password=make_password("ep"),identity=3, entity=1, department=1)
        ep2 = User.objects.create(name="ep2", password=make_password("ep2"),identity=3, entity=1, department=2)
        ns1 = User.objects.create(name="ns1", password=make_password("ns1"),identity=4, entity=1, department=1)
        ns2 = User.objects.create(name="ns2", password=make_password("ns2"),identity=4, entity=1, department=1)
        ns3 = User.objects.create(name="ns3", password=make_password("ns3"),identity=4, entity=1, department=2)
        self.login("ep2", "ep2")
        self.addassetclass("entry2",0)
        self.addassetclass("number2",1)
        self.addasset("e2","entry2",1,10,1000)
        self.addasset("n2","number2",10,1,10)
        self.logout("ep2")
        self.login("ep", "ep")
        self.addassetclass("entry",0)
        self.addassetclass("number",1)
        self.addasset("e","entry",1,10,2000)
        self.addasset("n","number",10,1,20)
        
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
    
    def addassetclass(self, name, type):
        return self.client.post("/asset/assetclass", {"name": name, "type": type})
    
    def addasset(self, name, cate, number,life=10,price=10):
        return self.client.post("/asset/post", [{"name": name, "category": cate,
                                                "life": life, "number": number, "price": price
                                                }], content_type="application/json")
    
    def test_totalnum(self):
        resp = self.client.get("/user/ep/as/atotal")
        self.assertEqual(resp.json()["info"], {'entryNumber': 2, 'quantTypeNumber': 2, 'quantTotalNumber': 20})
    
    def test_state(self):
        resp = self.client.get("/user/ep/as/astatotal")
        self.assertEqual(resp.json()["info"], {'freeNumber': 4, 'totccupyNumber': 0, 'partccupyNumber': 0, 'totfixNumber': 0, 'partfixNumber': 0, 'tbfixNumber': 0})

    def test_totalvalue(self):
        resp = self.client.get("/user/ep/as/totalnvalue")
        self.assertEqual(resp.json()["code"], 0)
    
    def test_departs(self):
        resp = self.client.get("/user/ep/as/departasset")
        self.assertEqual(resp.json()["info"], [{'name': 'dep', 'number': 2}, {'name': 'dep2', 'number': 2}])
    
    def test_curve(self):
        resp = self.client.get("/user/ep/as/nvcurve")
        self.assertEqual(resp.json()["code"], 0)