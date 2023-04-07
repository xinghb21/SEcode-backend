from django.test import TestCase
from user.models import User
from department.models import Department,Entity
import hashlib
from django.contrib.auth.hashers import make_password, check_password
from user.views import UserViewSet
# Create your tests here.

#hyx
class superAdminTest(TestCase):
    def setUp(self):
        aliceEntity = Entity.objects.create(name="Alice")
        bobEntity = Entity.objects.create(name="Bob")
        cindyDepart = Department.objects.create(name="Cindy",entity=2)
        admin = User.objects.create(name="admin",password=make_password("hh"),identity=1)
        loginres = self.login("admin","hh")

    def md5(self, s):
        obj = hashlib.md5()
        obj.update(s.encode())
        return obj.hexdigest()

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

    def create(self,name):
        payload = {
            "name" : name
        }
        return self.client.post("/entity/create", data=payload,content_type="application/json")
    
    def delete(self,name):
        payload = {
            "name" : name
        }
        return self.client.delete("/entity/delete", data=payload,content_type="application/json")
    
    def deleteAll(self,name):
        payload = {
            "name" : name
        }
        return self.client.delete("/entity/deleteall", data=payload,content_type="application/json")
    
    def assgin(self,entity,name,password):
        payload={
            "entity" : entity,
            "name" : name,
            "password" : password
        }
        return self.client.post("/entity/assgin", data=payload,content_type="application/json")
    
    def deleteadmin(self,entity):
        payload={
            "entity":entity
        }
        return self.client.delete("/entity/deleteadmin",data=payload,content_type="application/json")
    
    def deletealladmins(self,entity):
        payload={
            "entity":entity
        }
        return self.client.delete("/entity/deletealladmins",data=payload,content_type="application/json")

    def get_entity(self):
        res = self.assgin("Alice","David","qwertyuiop")
        return self.client.get("/entity/superget", content_type="application/json")

    def test_good_create(self):
        res = self.create("Coco")
        self.assertJSONEqual(res.content,{"code":0,"name":"Coco"})
    
    def test_bad_create(self):
        res = self.create("Alice")
        self.assertJSONEqual(res.content,{"code":-1,"detail":"此业务实体名称已存在"})
    
    def test_good_delete(self):
        res = self.delete("Bob")
        self.assertJSONEqual(res.content,{"code":0,"name":"Bob"})
    
    def test_bad_delete(self):
        res = self.delete("David")
        self.assertJSONEqual(res.content,{"code":-1,"detail":"此业务实体不存在"})
    
    def test_all_delete(self):
        hyxEntity = Entity.objects.create(name="hanyx")
        yhyEntity = Entity.objects.create(name="yanghy")
        res = self.deleteAll(["hanyx","yanghy"])
        self.assertJSONEqual(res.content,{"code":0})

    def test_assgin_not_entity(self):
        res = self.assgin("David","hanyx","qwertyuiop")
        self.assertJSONEqual(res.content,{"code":-1,"detail":"此业务实体不存在"})
    
    def test_good_assgin(self):
        res = self.assgin("Alice","Francis","qwertyuiop")
        self.assertJSONEqual(res.content,{"code":0,"username":"Francis"})
    
    def test_bad_delete_admin(self):
        res = self.deleteadmin("Francis")
        self.assertJSONEqual(res.content,{"code":-1,"detail":"此业务实体不存在"})
        res = self.deleteadmin("Bob")
        self.assertJSONEqual(res.content,{"code":-1,"detail":"此业务实体无系统管理员"})
    
    def test_good_delete_admin(self):
        self.assgin("Alice","Francis","qwertyuiop")
        res = self.deleteadmin("Alice")
        self.assertJSONEqual(res.content,{"code":0,"username":"Francis"})
        
    def test_delete_all_admins(self):
        self.assgin("Alice","Eric","qwertyuiop")
        self.assgin("Bob","Francis","qwertyuiop")
        res = self.deletealladmins(["Bob","Alice"])
        self.assertJSONEqual(res.content,{"code":0})
        
    def test_not_qualified_get_entity(self):
        client = User.objects.create(name="client",password="huwid",identity=2,entity=1)
        lohout = self.logout("admin")
        logres = self.login("client","huwid")
        res = self.get_entity()
        self.assertJSONEqual(res.content,{"code":-1,"detail":"此用户不是系统超级管理员或未登录,无权查看"})

    def test_good_get_entity(self):
        res = self.get_entity()
        self.assertJSONEqual(res.content,{"code":0,"data":[{"id":1,"name":"Alice","admin":"David"},{"id":2,"name":"Bob","admin":""}]})