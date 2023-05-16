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
        resp = self.client.get("/user/es/getlogs?page=1&type=0")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_unlock(self):
        resp = self.client.post("/user/es/unlock", {"name": "op1"}, content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.get("/user/es/getlogs?page=1&type=1")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_apps(self):
        resp = self.client.post("/user/es/apps", {"name": "op1", "newapp": "111111111"}, content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp.json()["new_app"], "111111111")
    
    def test_reset(self):
        name = "op1"
        resp = self.client.post("/user/es/reset", {"name": name, "newpassword": name}, content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
    
    def test_bad_createdepart(self):
        resp = self.client.post("/user/es/createdepart",{"entity":"et4","depname":"dep3","parent":""})
        std ={
            "code":-1,
            "detail":"业务实体不存在"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.post("/user/es/createdepart",{"entity":"et1","depname":"dep1","parent":""})
        std ={
            "code":-1,
            "detail":"部门已存在"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.post("/user/es/createdepart",{"entity":"et3","depname":"dep3","parent":""})
        std ={
            "code":-1,
            "detail":"无权创建部门"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.post("/user/es/createdepart",{"entity":"et1","depname":"dep3","parent":"dep4"})
        std ={
            "code":-1,
            "detail":"上属部门不存在"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.get("/user/es/getlogs?page=1&type=2")
        self.assertEqual(resp.json()["code"], 0)
    
    def test_create_and_check_departs(self):
        self.login("es", "es")
        resp = self.client.post("/user/es/createdepart",{"entity":"et1","depname":"dep3","parent":""})
        std={
            "code":0,
            "name":"dep3"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.post("/user/es/createdepart",{"entity":"et1","depname":"dep4","parent":"dep2"})
        std={
            "code":0,
            "name":"dep4"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.get("/user/es/departs")
        std={
            "code":0,
            "info": {"et1":{"dep1": "$", "dep2": {"dep4": "$"}, "dep3": "$"}}
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.get("/user/es/getlogs?page=1&type=3")
        self.assertEqual(resp.json()["code"], 0)
    
    def test_delete_departs(self):
        self.login("es", "es")
        resp = self.client.delete("/user/es/deletedepart",{"name":"dep3"},content_type="application/json")
        std ={
            "code":-1,
            "detail":"该部门不存在"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.delete("/user/es/deletedepart",{"name":"dep1"},content_type="application/json")
        std ={
            "code":0,
            "name":"dep1"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.get("/user/es/getlogs?page=1&type=4")
        self.assertEqual(resp.json()["code"], 0)
    
    def test_rename_departs(self):
        self.login("es", "es")
        resp = self.client.post("/user/es/renamedepart",{"oldname":"dep3","newname":"dep4"},content_type="application/json")
        std ={
            "code":-1,
            "detail":"待修改部门不存在"
        }
        resp = self.client.post("/user/es/renamedepart",{"oldname":"dep1","newname":"dep2"},content_type="application/json")
        std ={
            "code":-1,
            "detail":"新名称部门已存在"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.post("/user/es/renamedepart",{"oldname":"dep1","newname":"dep4"},content_type="application/json")
        std ={
            "code":0,
            "oldname":"dep1",
            "newname":"dep4"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.get("/user/es/getlogs?page=1&type=0")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_check_staffs(self):
        self.login("es", "es")
        resp = self.client.get("/user/es/staffs?page=1&department=dep1")
        std={
            "code":0,
            "info": [{'id': 6, 'username': 'ep', 'number': 3}, {'id': 1, 'username': 'op1', 'number': 4}, {'id': 2, 'username': 'op2', 'number': 4}]
        }
        self.assertJSONEqual(resp.content,std)
    
    def test_check_all(self):
        resp = self.client.get("/user/es/checkall?page=1")
        self.assertEqual(resp.json()["data"][0], {'id': 1, 'name': 'op1', 'identity': 4, 'lockedapp': '000000001', 'locked': False, 'entity': 'et1', 'department': 'dep1'})
        
    def test_batch_delete(self):
        User.objects.create(name="todelete", password=make_password("yuanshen"),
                                       identity=4, entity=1, department=2)
        User.objects.create(name="todelete2", password=make_password("yuanshen"),
                                       identity=4, entity=1, department=2)    
        resp = self.client.delete("/user/es/batchdelete", {"names": ["todelete", "todelete2"]}, content_type="application/json")
        # print(resp.json())
        self.assertEqual(resp.json()["code"], 0)
        user = User.objects.filter(name="todelete").first()
        user2 = User.objects.filter(name="todelete2").first()
        self.assertEqual(user, None)
        self.assertEqual(user2, None)
        resp = self.client.get("/user/es/getlogs?page=1&type=0")
        self.assertEqual(resp.json()["code"], 0)
    
    def test_delete_dep(self):
        Department.objects.create(name="dep3", entity=1, parent=0, admin=6)
        Department.objects.create(name="dep4", entity=1, parent=0, admin=6)
        deps = Department.objects.filter(name="dep3")
        # print(Department.objects.filter(name="dep3"))
        self.client.delete("/user/es/deletealldeparts", ["dep3", "dep4"], content_type="application/json")
        self.assertEqual(Department.objects.filter(name="dep3").first(), None) 
        resp = self.client.get("/user/es/getlogs?page=1&type=0")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_searchuser(self):
        resp = self.client.post("/user/es/searchuser?page=1", {"username": "op1", "department": "dep1"})
        # print(resp.json())
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.post("/user/es/searchuser?page=1", {"department": "dep1"})
        # print(resp.json())
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.post("/user/es/searchuser?page=1", {"identity": 4})
        # print(resp.json())
        self.assertEqual(resp.json()["code"], 0)
        
    def test_change_identity(self):
        User.objects.create(name="tochange", password=make_password("yuanshen"),identity=4, entity=1, department=2)
        User.objects.create(name="tochange2", password=make_password("yuanshen"),identity=3, entity=1, department=2)
        resp = self.client.post("/user/es/changeidentity", {"name":"tochange","new":3,"department":"dep2","entity":"et1"}, content_type="application/json")
        std ={
            "code":-1,
            "detail":"该部门下已经有资产管理员"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.post("/user/es/changeidentity", {"name":"tochange2","new":5,"department":"dep2","entity":"et1"}, content_type="application/json")
        std ={
            "code":-1,
            "detail":"传入的新身份不合法"
        }
        self.assertJSONEqual(resp.content,std)
        resp = self.client.post("/user/es/changeidentity", {"name":"tochange2","new":4,"department":"dep2","entity":"et1"}, content_type="application/json")
        print(resp.json())
        self.assertEqual(User.objects.filter(name="tochange2").first().identity, 4)
        resp = self.client.get("/user/es/getlogs?page=1&type=0")
        self.assertEqual(resp.json()["code"], 0)
        