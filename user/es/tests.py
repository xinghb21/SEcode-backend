from django.test import TestCase, Client
from user.models import User
from department.models import Department, Entity
import json
import hashlib
from django.contrib.auth.hashers import make_password, check_password

class esTest(TestCase):
    def setUp(self) -> None:
        op1 = User.objects.create(name="op1", password=make_password("op1"), 
                                 identity=4, entity=1, department=1)
        op2 = User.objects.create(name="op2", password=make_password("op2"), 
                                 identity=4, entity=1, department=2)
        op3 = User.objects.create(name="op3", password=make_password("op3"), 
                                 identity=4, entity=2, department=2)
        ss = User.objects.create(name="ss", password=make_password("ss"), 
                                 identity=1, entity=0, department=0)
        es = User.objects.create(name="es", password=make_password("es"), 
                                 identity=2, entity=1, department=0)
        ep = User.objects.create(name="ep", password=make_password("ep"), 
                                 identity=3, entity=1, department=1)
        et1 = Entity.objects.create(name="et1", admin=4)
        et2 = Entity.objects.create(name="et2", admin=4)
        dep1 = Department.objects.create(name="dep1", entity=1, parent=0, admin=5)
        dep2 = Department.objects.create(name="dep2", entity=1, parent=0, admin=5)
        self.login("es", "es")
        
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
    def identity(self, id):
        if id == 1:
            return "超级管理员"
        elif id == 2:
            return "系统管理员"
        elif id == 3:
            return "资产管理员"
        elif id == 4:
            return "员工"
    
    def test_check(self):
        op1 = User.objects.filter(name="op1").first()
        dep = Department.objects.filter(id=op1.department).first()
        et = Entity.objects.filter(id=op1.entity).first()
        resp = self.client.get("/user/es/check", {"name": "op1"})
        std = {
            "code": 0,
            "name": op1.name,
            "entity": et.name,
            "department": dep.name,
            "identity": op1.identity,
            "lockedapp": op1.lockedapp,
            "locked": op1.locked,
        }
        self.assertJSONEqual(resp.content, std)
    
    def test_check_bad_user(self):
        resp = self.client.get("/user/es/check", {"name": "ayaka"})
        std = {
            "detail": "被查询的用户不存在",
            "code": -1
        }
        self.assertJSONEqual(resp.content, std)
        resp = self.client.get("/user/es/check", {"name": "op3"})
        std = {
            "detail": "系统管理员无权操作其它业务实体的用户",
            "code": -1
        }
        self.assertJSONEqual(resp.content, std)
    
    def test_check_bad_identity(self):
        resp = self.client.get("/user/es/check", {"name": "ss"})
        std = {
            "detail": "系统管理员无权操作超级管理员",
            "code": -1
        }
        self.assertJSONEqual(resp.content, std)
        resp = self.client.get("/user/es/check", {"name": "es"})
        std = {
            "detail": "系统管理员无权操作系统管理员",
            "code": -1
        }
        self.assertJSONEqual(resp.content, std)
    
    def test_alter(self):
        resp = self.client.post("/user/es/alter", {"name": "op1", "department": "dep2"})
        std = {
            "code": 0,
            "name": "op1",
            "old_department": "dep1",
            "new_department": "dep2",
        }
        self.assertJSONEqual(resp.content, std)
        
    def test_lock(self):
        resp = self.client.post("/user/es/lock", data={"name": "op1"}, content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_unlock(self):
        resp = self.client.post("/user/es/unlock", {"name": "op1"}, content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_apps(self):
        resp = self.client.post("/user/es/apps", {"name": "op1", "newapp": "111111111"}, content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp.json()["new_app"], "111111111")
    
    def test_reset(self):
        resp = self.client.post("/user/es/reset", {"name": "op1", "newpassword": "abababab"}, content_type="application/json")
        self.assertEqual(resp.json()["code"], 0) 
    
    def test_create_and_delete_depart(self):
        es = User.objects.filter(name="es").first()
        et = Entity.objects.create(name="newet", admin=es.id)
        resp = self.client.post("/user/es/createdepart", {"entity": "newet", "depname": "newdep", "parent": ""})
        std={
            "code": 0,
            "name": "newdep",
        }
        self.assertJSONEqual(resp.content, std)
        resp2 = self.client.delete("/user/es/deletedepart", {"name": "newdep"})
        std2 = {
            "code": 0,
            "name": "newdep"
        }
        self.assertJSONEqual(resp.content, std2)
        
