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
        ep = User.objects.create(name="ep", password=make_password("ep"),identity=3, entity=1, department=1)
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
    
    def postaware(self,name,type,number):
        payload = {
            "assetname":name,
            "warning":type,
            "condition":number
        }
        return self.client.post("/user/ep/aw/newaw",data=payload, content_type="application/json")
    
    def deleteaware(self,id):
        payload = {
            "key":id
        }
        return self.client.delete("/user/ep/aw/deleteaw",data=payload, content_type="application/json")
    
    def deletemessage(self,id):
        payload = {
            "key":id
        }
        return self.client.delete("/user/ep/dclearmg",data=payload, content_type="application/json")
    
    def test_post_and_get(self):
        resp = self.postaware("a",1,1)
        self.assertEqual(resp.json()["detail"], "资产不存在")
        resp = self.postaware("e",1,10)
        self.assertEqual(resp.json()["detail"], "条目型资产不可设置数量告警")
        resp = self.postaware("e",0,1)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.postaware("e",0,2)
        self.assertEqual(resp.json()["detail"], "已经存在同类告警策略")
        resp = self.postaware("n",1,10)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.get("/user/ep/aw/getw")
        self.assertEqual(resp.json()["info"], [{'key': 1, 'assetname': 'e', 'warning': 0, 'condition': 1.0}, {'key': 2, 'assetname': 'n', 'warning': 1, 'condition': 10.0}])
    
    def test_delete(self):
        resp = self.postaware("n",0,1)
        resp = self.postaware("n",1,10)
        resp = self.deleteaware(3)
        self.assertEqual(resp.json()["detail"], "告警策略不存在")
        resp = self.deleteaware(1)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.get("/user/ep/aw/getw")
        self.assertEqual(resp.json()["info"], [{'key': 2, 'assetname': 'n', 'warning': 1, 'condition': 10.0}])
        
    def test_change(self):
        resp = self.postaware("n",1,10)
        resp = self.client.post("/user/ep/aw/cgcondition",{"key":2,"newcondition":5.0})
        self.assertEqual(resp.json()["detail"], "告警策略不存在")
        resp = self.client.post("/user/ep/aw/cgcondition",{"key":1,"newcondition":5.0})
        self.assertEqual(resp.json()["code"], 0)
        
    def test_alertmsg(self):
        resp = self.client.get("/user/ep/beinformed")
        self.assertEqual(resp.json()["info"], False)
        resp = self.postaware("e",0,0)
        resp = self.postaware("n",1,20)
        resp = self.client.get("/user/ep/beinformed")
        self.assertEqual(resp.json()["info"], True)
        resp = self.client.get("/user/ep/allmessage")
        self.assertEqual(resp.json()["info"], [{'key': 1, 'type': 0, 'message': 'e使用已超过0年'}, {'key': 2, 'type': 0, 'message': 'n数量不足20'}])
        resp = self.deletemessage(2)
        self.assertEqual(resp.json()["detail"],"消息不是资产折旧")
        resp = self.client.post("/user/ep/aw/cgcondition",{"key":1,"newcondition":1})
        resp = self.client.post("/user/ep/aw/cgcondition",{"key":2,"newcondition":15})
        resp = self.client.get("/user/ep/allmessage")
        self.assertEqual(resp.json()["info"], [{'key': 2, 'type': 0, 'message': 'n数量不足15'}])
        resp = self.client.post("/user/ep/aw/cgcondition",{"key":2,"newcondition":5})
        resp = self.client.get("/user/ep/beinformed")
        self.assertEqual(resp.json()["info"], False)
    
    def test_auto_expire(self):
        self.addasset("badasset","entry",1,0,10)
        resp = self.client.get("/user/ep/beinformed")
        self.assertEqual(resp.json()["info"], False)
        self.logout("ep")
        self.login("ep","ep")
        resp = self.client.get("/user/ep/allmessage")
        self.assertEqual(resp.json()["info"], [{'key': 1, 'type': 1, 'message': '资产badasset因过期自动清退'}])
        resp = self.deletemessage(2)
        self.assertEqual(resp.json()["detail"],"消息不存在")
        resp = self.deletemessage(1)
        self.assertEqual(resp.json()["code"],0)
        resp = self.client.get("/user/ep/beinformed")
        self.assertEqual(resp.json()["info"], False)