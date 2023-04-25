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
    
    def addassetclass(self, name, type):
        return self.client.post("/asset/assetclass", {"name": name, "type": type})
    
    def addasset(self, name, cate, number,life=10,expire = False):
        return self.client.post("/asset/post", [{"name": name, "category": cate,
                                                "life": life, "number": number, "price": 10000,"expire" : expire,
                                                }], content_type="application/json")
    
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
    
    def test_clear(self):
        resp = self.addassetclass("yuanshen", 1)
        resp = self.addassetclass("yuanshen2",0)
        resp = self.addasset("hutao", "yuanshen", 100,0)
        resp = self.addasset("hutao2", "yuanshen2", 1)
        resp = self.client.get("/user/ep/assetstbc",content_type="application/json")
        self.assertEqual(resp.json()["code"],0)
    
    def test_query(self):
        et = Entity.objects.filter(id=1).first()
        dep = Department.objects.filter(id=1).first()
        ns1 = User.objects.filter(name="ns1").first()
        ns2 = User.objects.filter(name="ns2").first()
        class1 = AssetClass.objects.create(name="class1",entity=et,department=dep,type=False)
        class2 = AssetClass.objects.create(name="class2",entity=et,department=dep,type=True)
        asset1 = Asset.objects.create(name="asset1",entity=et,department=dep,category=class1,type=False,price=10,create_time=114514,additional=json.dumps({"size":"large"}))
        asset2 = Asset.objects.create(name="asset2",entity=et,parent=asset1,department=dep,category=class1,type=False,price=100,status=1,user=ns2)
        asset3 = Asset.objects.create(name="asset3",entity=et,department=dep,category=class2,type=True,price=5,number=100,number_idle=50,usage=json.dumps([{"ns1":25}]),maintain=json.dumps([{"ns2":25}]))
        asset4 = Asset.objects.create(name="asset4",entity=et,department=dep,category=class1,type=False,life=0,price=233,user=ns1,additional=json.dumps({"color":"red"}))
        resp = self.client.post("/user/ep/queryasset",{"parent":"asset1","pricefrom":50,"status":1,"user":"ns2"},content_type="application/json")
        self.assertEqual(resp.json()["data"],[{'name': 'asset2', 'key': 2, 'description': '', 'assetclass': 'class1', 'type': False}])
        resp = self.client.post("/user/ep/queryasset",{"id":1,"to":114515,"custom":"size","status":-1},content_type="application/json")
        print(resp.json()["data"])
        self.assertEqual(resp.json()["data"],[{'name': 'asset1', 'key': 1, 'description': '', 'assetclass': 'class1', 'type': False}])