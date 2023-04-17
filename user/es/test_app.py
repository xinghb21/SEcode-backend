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
    
    def add_app(self, name, app):
        return self.client.post("/user/es/addapp", {"username": name, "appadded": app}, content_type="application/json")
    
    def delete_app(self, name, app):
        return self.client.delete("/user/es/deleteapps", {"username": name, "appdeleted": app}, content_type="application/json")
    
    def test_addapp(self):
        name = "op1"
        app = [{"name":"百度","urlvalue":"https://www.baidu.com"},{"name":"网络学堂","urlvalue":"https://learning.edu.cn"}]
        self.add_app(name,app)
        # print(resp.json())
        user = User.objects.filter(name=name).first()
        apps = user.serialize()['apps']
        self.assertEqual(apps['data'], app)
        
    def test_addapp_badparam(self):
        name = "op1"
        app = {"name":"百度","urlvalue":"https://www.baidu.com"}
        resp = self.client.post("/user/es/addapp", {"username": name, "appadded": app}, content_type="application/json")
        # print(resp.json())
        self.assertEqual(resp.json()['code'], -1)
        
    def test_addapp_add_existing_thing(self):
        name = "op1"
        app = [{"name":"百度","urlvalue":"https://www.baidu.com"},{"name":"网络学堂","urlvalue":"https://learning.edu.cn"}]
        self.client.post("/user/es/addapp", {"username": name, "appadded": app}, content_type="application/json")
        # print(resp.json())
        user = User.objects.filter(name=name).first()
        apps = user.serialize()['apps']
        self.assertEqual(apps['data'], app)
        self.client.post("/user/es/addapp", {"username": name, "appadded": app}, content_type="application/json")
        # print(resp.json())
        user = User.objects.filter(name=name).first()
        apps = user.serialize()['apps']
        self.assertEqual(apps['data'], app)
    
    def test_deleteapp(self):
        name = "op1"
        self.add_app(name, [{"name":"百度","urlvalue":"https://www.baidu.com"},{"name":"网络学堂","urlvalue":"https://learning.edu.cn"}])
        app = ["百度"]
        resp = self.delete_app(name,app)
        # print(resp.json())
        self.assertEqual(resp.json()['code'], 0)
        user = User.objects.filter(name=name).first()
        apps = user.serialize()['apps']
        # print(apps['data'])
        self.assertEqual(apps['data'], [{'name': '网络学堂', 'urlvalue': 'https://learning.edu.cn'}])
        
    def test_deleteapp_nonexist(self):
        name = "op1"
        self.add_app(name, [{"name":"百度","urlvalue":"https://www.baidu.com"},{"name":"网络学堂","urlvalue":"https://learning.edu.cn"}])
        app = ["原神"]
        resp = self.delete_app(name,app)
        # print(resp.json())
        self.assertEqual(resp.json()['code'], 0)
        user = User.objects.filter(name=name).first()
        apps = user.serialize()['apps']
        # print(apps['data'])
        self.assertEqual(apps['data'], [{"name":"百度","urlvalue":"https://www.baidu.com"},{'name': '网络学堂', 'urlvalue': 'https://learning.edu.cn'}])
        