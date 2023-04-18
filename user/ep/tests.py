#hyx

from django.test import TestCase, Client
from user.models import User
from department.models import Department, Entity
from pending.models import Pending
from asset.models import Asset,AssetClass
import json
import hashlib
from django.contrib.auth.hashers import make_password, check_password

class epTest(TestCase):
    def setUp(self) -> None:
        et = Entity.objects.create(name="et")
        dep = Department.objects.create(name="dep", entity=1, admin=1)
        ep = User.objects.create(name="ep", password=make_password("ep"),identity=3, entity=1, department=1)
        ns1 = User.objects.create(name="ns1", password=make_password("ns1"),identity=4, entity=1, department=1)
        ns2 = User.objects.create(name="ns2", password=make_password("ns2"),identity=4, entity=1, department=1)
        self.login("ep", "ep")
        
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
    
    def test_get_pendings(self):
        et = Entity.objects.filter(id=1).first()
        dep = Department.objects.filter(id=1).first()
        class1 = AssetClass.objects.create(name="class1",entity=et,department=dep,type=True)
        class2 = AssetClass.objects.create(name="class2",entity=et,department=dep,type=False)
        asset1 = Asset.objects.create(name="asset1",entity=et,department=dep,category=class1,type=True,number=100,number_idle=100,price=10)
        asset2 = Asset.objects.create(name="asset2",entity=et,department=dep,category=class2,type=False,status=0,price=1000)
        pending1 = Pending.objects.create(entity=1,department=1,initiator=2,description="I want this",
                                          asset=json.dumps([{"asset1":10}]))
        pending2 = Pending.objects.create(entity=1,department=1,initiator=3,description="I want these",
                                          asset=json.dumps([{"asset1":100,"asset2":1}]))
        resp = self.client.get("/user/ep/getallapply")
        print(resp.json())
        self.assertEqual(resp.json()["info"],  [{'id': 1, 'name': 'ns1', 'oper': 0, 'reason': 'I want this'},{'id': 2, 'name': 'ns2', 'oper': 0, 'reason': 'I want these'}])
        
    def test_process_apply_pendings(self):
        et = Entity.objects.filter(id=1).first()
        dep = Department.objects.filter(id=1).first()
        ep = User.objects.filter(id=1).first()
        class1 = AssetClass.objects.create(name="class1",entity=et,department=dep,type=True)
        class2 = AssetClass.objects.create(name="class2",entity=et,department=dep,type=False)
        asset1 = Asset.objects.create(name="asset1",entity=et,department=dep,category=class1,type=True,belonging=ep, number=100,number_idle=100,price=10)
        asset2 = Asset.objects.create(name="asset2",entity=et,department=dep,category=class2,type=False,belonging=ep,status=0,price=1000)
        pending1 = Pending.objects.create(entity=1,department=1,initiator=2,description="I want this",
                                          asset=json.dumps([{"asset1":10}]))
        pending2 = Pending.objects.create(entity=1,department=1,initiator=2,description="I want this",
                                          asset=json.dumps([{"asset2":1}]))
        pending3 = Pending.objects.create(entity=1,department=1,initiator=3,description="I want these",
                                          asset=json.dumps([{"asset1":100,"asset2":1}]))
        pending3 = Pending.objects.create(entity=1,department=1,initiator=3,description="I want these",
                                          asset=json.dumps([{"asset3":1,"asset1":10}]))
        resp = self.client.post("/user/ep/reapply", 
                         {"id":1,"status":0,"reason":"success"}
                         ,content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.post("/user/ep/reapply", 
                         {"id":3,"status":0,"reason":"success"}
                         ,content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.post("/user/ep/reapply", 
                         {"id":2,"status":1,"reason":"I'm sorry"}
                         ,content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.post("/user/ep/reapply", 
                         {"id":1,"status":0,"reason":"success"}
                         ,content_type="application/json")
        self.assertEqual(resp.json()["detail"], "此待办已审批完成")
        resp = self.client.post("/user/ep/reapply", 
                         {"id":5,"status":1,"reason":"no such pending"}
                         ,content_type="application/json")
        self.assertEqual(resp.json()["detail"], "待办项不存在")
        resp = self.client.post("/user/ep/reapply", 
                         {"id":4,"status":0,"reason":"success"}
                         ,content_type="application/json")
        self.assertEqual(resp.json()["detail"],"请求中包含已失效资产，请拒绝")
        resp = self.client.post("/user/ep/reapply", 
                         {"id":4,"status":1,"reason":"no such asset"}
                         ,content_type="application/json")
        self.assertEqual(resp.json()["code"],0)

    def test_assets_in_apply(self):
        et = Entity.objects.filter(id=1).first()
        dep = Department.objects.filter(id=1).first()
        class1 = AssetClass.objects.create(name="class1",entity=et,department=dep,type=True)
        asset1 = Asset.objects.create(name="asset1",entity=et,department=dep,category=class1,type=True,number=100,number_idle=100,price=10)
        pending = Pending.objects.create(entity=1,department=1,initiator=3,description="I want these",
                                          asset=json.dumps([{"asset1":100}]))
        resp = self.client.get("/user/ep/assetsinapply?id=1",content_type="application/json")
        self.assertEqual(resp.json()["info"],[{'id': 1, 'assetname': 'asset1', 'assetclass': 'class1', 'assetcount': 100}])
    
    def test_stbd(self):
        et = Entity.objects.filter(id=1).first()
        dep = Department.objects.filter(id=1).first()
        class1 = AssetClass.objects.create(name="class1",entity=et,department=dep,type=True)
        resp = self.client.get("/user/ep/istbd",content_type="application/json")
        self.assertEqual(resp.json()["info"],False)
        asset1 = Asset.objects.create(name="asset1",entity=et,department=dep,category=class1,type=True,number=100,number_idle=100,price=10)
        pending = Pending.objects.create(entity=1,department=1,initiator=3,description="I want these",
                                          asset=json.dumps([{"asset1":100}]))
        resp = self.client.get("/user/ep/istbd",content_type="application/json")
        self.assertEqual(resp.json()["info"],True)