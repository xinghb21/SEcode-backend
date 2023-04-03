from django.test import TestCase
from user.models import User
from department.models import Department,Entity
import hashlib
from django.contrib.auth.hashers import make_password, check_password
# Create your tests here.

#hyx
class superAdminTest(TestCase):
    def setUp(self):
        aliceEntity = Entity.objects.create(name="Alice")
        bobEnntity = Entity.objects.create(name="Bob")

    def md5(self, s):
        obj = hashlib.md5()
        obj.update(s.encode())
        return obj.hexdigest()

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
    
    def assgin(self,entity,name,password):
        payload={
            "entity" : entity,
            "name" : name,
            "password" : password
        }
        return self.client.post("/entity/assgin", data=payload,content_type="application/json")

    def get_entity(self):
        res = self.assgin("Alice","David","qwertyuiop")
        return self.client.get("/entity/superget", content_type="application/json")

    def test_good_create(self):
        res = self.create("Coco")
        self.assertJSONEqual(res.content,{"code":0,"name":"Coco"})
    
    def test_bad_create(self):
        res = self.create("Alice")
        self.assertJSONEqual(res.content,{"code":-1,"info":"此业务实体名称已存在"})
    
    def test_good_delete(self):
        res = self.delete("Bob")
        self.assertJSONEqual(res.content,{"code":0,"name":"Bob"})
    
    def test_bad_delete(self):
        res = self.delete("David")
        self.assertJSONEqual(res.content,{"code":-1,"info":"此业务实体不存在"})
    
    def test_assgin_not_entity(self):
        res = self.assgin("David","hanyx","qwertyuiop")
        print(res.content)
        self.assertJSONEqual(res.content,{"code":-1,"info":"此业务实体不存在"})
    
    def test_good_assgin(self):
        res = self.assgin("Alice","David","qwertyuiop")
        self.assertJSONEqual(res.content,{"code":0,"username":"David"})

    def test_get_entity(self):
        res = self.get_entity()
        self.assertJSONEqual(res.content,{"code":0,"data":[{"id":1,"name":"Alice","admin":"David"},{"id":2,"name":"Bob","admin":""}]})
