from django.test import TestCase, Client
from user.models import User
from department.models import Department, Entity
import json
from django.contrib.auth.hashers import make_password
from pending.models import Pending

class esTest(TestCase):
    def setUp(self) -> None:
        op1 = User.objects.create(name="op1", password=make_password("op1"), 
                                 identity=4, entity=1, department=1)
        op2 = User.objects.create(name="op2", password=make_password("op2"), 
                                 identity=4, entity=1, department=1)
        op3 = User.objects.create(name="op3", password=make_password("op3"), 
                                 identity=4, entity=2, department=2)
        ss = User.objects.create(name="ss", password=make_password("ss"), 
                                 identity=1, entity=0, department=0)
        es = User.objects.create(name="es", password=make_password("es"), 
                                 identity=2, entity=1, department=0)
        ep = User.objects.create(name="ep", password=make_password("ep"), 
                                 identity=3, entity=1, department=1)
        es2 = User.objects.create(name="es2", password=make_password("es2"), 
                                 identity=2, entity=1, department=0)
        et1 = Entity.objects.create(name="et1", admin=5)
        et2 = Entity.objects.create(name="et2", admin=5)
        et3 = Entity.objects.create(name="et3",admin=7)
        dep1 = Department.objects.create(name="dep1", entity=1, parent=0, admin=6)
        dep2 = Department.objects.create(name="dep2", entity=1, parent=0, admin=6)
        self.login("ep", "ep")
        resp = self.addassetclass("yuanshen", 1)
        # print(resp.json())
        resp = self.addasset("hutao", "yuanshen", 100)
        # print(resp.json())
        self.logout("ep")
        self.login("op1", "op1")
        
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
    
    def addasset(self, name, cate, number):
        return self.client.post("/asset/post", [{"name": name, "category": cate,
                                                "life": 10, "number": number, "price": 10000,
                                                }], content_type="application/json")
    
    def apply(self, assetname, assetcount, assetclass, reason="abab"):
        return self.client.post("/user/ns/userapply", {"assetsapply": [{"id":1, "assetname":assetname, "assetcount":assetcount, "assetclass":assetclass}], "reason":reason}, content_type="application/json")
    
    def test_apply(self):
        resp = self.apply("hutao", 50, "yuanshen")
        # print(resp.json())
        self.assertEqual(resp.json()["code"], 0)
        p = Pending.objects.filter(initiator=1)
        # print(p.first().serialize())
        self.assertNotEqual(p.first(), None)
        
    def test_getapply(self):
        self.apply("hutao", 50, "yuanshen")
        # print(resp.json())
        resp = self.client.get("/user/ns/getallapply")
        # print(resp.json())
        self.assertEqual(resp.json(), {'code': 0, 'info': [{'id': 1, 'reason': 'abab', 'status': 0, 'message': ''}]})
        
    def test_assetsinapply(self):
        self.apply("hutao", 50, "yuanshen")
        resp = self.client.get("/user/ns/assetsinapply?id=1")
        # print(resp.json())
        self.assertEqual(resp.json(), {'code': 0, 'info': [{'id': 1, 'assetname': 'hutao', 'assetcount': 50}]})
        
    def test_deleteapply(self):
        self.apply("hutao", 50, "yuanshen")
        resp = self.client.delete("/user/ns/deleteapplys",{"id":1},content_type="application/json")
        self.assertEqual(resp.json(), {'code': -1, 'detail': '不能删除资产管理员未处理的申请'})
        pending = Pending.objects.filter(id=1).first()
        pending.result = 1
        pending.save()
        resp = self.client.delete("/user/ns/deleteapplys",{"id":1},content_type="application/json")
        self.assertEqual(resp.json(), {'code': 0, 'detail': 'ok'})