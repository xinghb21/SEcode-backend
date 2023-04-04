from django.test import TestCase, Client
from user.models import User
from department.models import Department, Entity
import json
import hashlib
from django.contrib.auth.hashers import make_password, check_password
# Create your tests here.

class userTest(TestCase):
    def setup(self)->None:
        alice = User.objects.create(name="alice",password=make_password("alice"),identity=1)
        self.login("alice","alice")

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
    
    def test_bad_login(self):
        bob = User.objects.create(name="bob",password=make_password("bob"),identity=2,entity=1)
        coco = User.objects.create(name="coco",password=make_password("coco"),identity=3,entity=1,department=1,lockedapp="000001010")
        david = User.objects.create(name="david",password=make_password("david"),identity=4,entity=1,department=1,locked=True)
        resp = self.login("hanyx","hanyx")
        std={
            "code":-1,
            "detail":"用户不存在"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.login("bob","alice")
        std={
            "code":-1,
            "detail":"密码错误"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.login("david","david")
        std={
            "code":-1,
            "detail":"此用户已被管理员封禁"
        }
        self.assertJSONEqual(resp.content,std)
    
    def test_bad_logout(self):
        resp = self.logout("francis")
        std={
            "code":-1,
            "detail":"用户不存在"
        }
        self.assertJSONEqual(resp.content,std)
    
    def test_bad_create(self):
        et = Entity.objects.create(name="et")
        dep = Department.objects.create(name="dep", entity=1)
        bob = User.objects.create(name="bob",password=make_password("bob"),identity=2,entity=1)
        coco = User.objects.create(name="coco",password=make_password("coco"),identity=3,entity=1,department=1,lockedapp="000001010")
        david = User.objects.create(name="david",password=make_password("david"),identity=4,entity=1,department=1,locked=True)
        bobpw = "bob"
        resp = self.client.post("/user/createuser",{"name":"bob","password":bobpw,"identity":2,"entity":"et"})
        std={
            "code":-1,
            "detail":"此用户名已存在"
        }
        frpw = "francis"
        self.assertJSONEqual(resp.content,std)
        resp = self.client.post("/user/createuser",{"name":"francis","password":frpw,"identity":2,"entity":"et2"})
        std={
            "code":-1,
            "detail":"业务实体不存在"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.post("/user/createuser",{"name":"francis","password":frpw,"identity":3,"entity":"et","department":"dep2"})
        std={
            "code":-1,
            "detail":"部门不存在"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.post("/user/createuser",{"name":"bob","password":bobpw,"identity":"WTF","entity":"et"})
        std={
            "code":-1,
            "detail":"Invalid identity"
        }
        self.assertJSONEqual(resp.content,std)

    def test_create(self):
        et = Entity.objects.create(name="et")
        frpw = "francis"
        resp = self.client.post("/user/createuser",{"name":"francis","password":frpw,"identity":2,"entity":"et"})
        std={
            "username":"francis"
        }
        self.assertJSONEqual(resp.content,std)

    def test_bad_delete(self):
        resp = self.client.delete("/user/deleteuser",{"name":"bob"},content_type="application/json")
        std={
            "code":-1,
            "detail":"此用户不存在"
        }
        self.assertJSONEqual(resp.content,std)
    
    def test_delete(self):
        bob = User.objects.create(name="bob",password=make_password("bob"),identity=2,entity=1)
        resp = self.client.delete("/user/deleteuser",{"name":"bob"},content_type="application/json")
        std={
            "username":"bob"
        }
        self.assertJSONEqual(resp.content,std)
    
    def test_get_home(self):
        bob = User.objects.create(name="bob",password=make_password("bob"),identity=4,entity=1,department=1,lockedapp="000000000")
        self.login("bob","bob")
        resp = self.client.get("/user/home/bob")
        std={
            "code":0,
            "department":1,
            "entity":1,
            "funclist":"000000000",
            "identity":4,
            "username":"bob"
        }
        self.assertJSONEqual(resp.content,std)