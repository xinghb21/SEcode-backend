from django.test import TestCase
from django.contrib.auth.hashers import make_password, check_password
from asynctask.models import Async_import_export_task
from department.models import Department, Entity
from user.models import User
from utils.exceptions import Failure
from asset.models import Asset
import time
# Create your tests here.
class asyncTest(TestCase):
    def setUp(self) -> None:
        ent = Entity.objects.create(name="ent")
        dep = Department.objects.create(name="dep", entity=1)
        alice = User.objects.create(name="alice",password=make_password("alice"),identity=2,entity=1)
        bob = User.objects.create(name="bob",password=make_password("bob"),identity=3,entity=1,department=1,lockedapp="000001010")
        asset1 = Asset.objects.create(name="asset1",entity=ent,department=dep)
    
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
    
    def test_newtask(self):
        self.login("bob", "bob")
        resp = self.client.post("/async/newouttask?test=1", content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["code"], 0)
        
    def test_getprocess(self):
        self.login("bob", "bob")
        resp = self.client.post("/async/newouttask?test=1", content_type="application/json")
        resp = self.client.post("/async/getprocess", data={"taskid":1}, content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_restart(self):
        self.login("bob", "bob")
        resp = self.client.post("/async/newouttask?test=1", content_type="application/json")
        resp = self.client.post("/async/restarttask?test=1", data={"taskid":1}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["code"], 0)
    
    def test_getsuccess(self):
        self.login("alice", "alice")
        resp = self.client.post("/async/newouttask?test=1", content_type="application/json")
        resp = self.client.post("/async/getsuccess?test=1", content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_getfailed(self):
        self.login("alice", "alice")
        resp = self.client.post("/async/newouttask?test=1", content_type="application/json")
        resp = self.client.post("/async/getfailed?test=1", content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_esgetall(self):
        self.login("bob", "bob")
        resp = self.client.post("/async/newouttask?test=1", content_type="application/json")
        self.logout("bob")
        
        self.login("alice", "alice")
        resp = self.client.get("/async/esgetalltask?test=1", content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_getalive(self):
        self.login("bob", "bob")
        resp = self.client.post("/async/newouttask?test=1", content_type="application/json")
        resp = self.client.get("/async/getalivetasks?test=1", content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        