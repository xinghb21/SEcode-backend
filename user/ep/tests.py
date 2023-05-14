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
        dep2 = Department.objects.create(name="dep2", entity=1, admin=2)
        ep = User.objects.create(name="ep", password=make_password("ep"),identity=3, entity=1, department=1)
        ep2 = User.objects.create(name="ep2", password=make_password("ep2"),identity=3, entity=1, department=2)
        ns1 = User.objects.create(name="ns1", password=make_password("ns1"),identity=4, entity=1, department=1)
        ns2 = User.objects.create(name="ns2", password=make_password("ns2"),identity=4, entity=1, department=1)
        ns3 = User.objects.create(name="ns3", password=make_password("ns3"),identity=4, entity=1, department=2)
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
    
    def apply(self, assetname, assetcount, id,assetclass, reason="abab"):
        return self.client.post("/user/ns/userapply", {"assetsapply": [{"id":id, "assetname":assetname, "assetcount":assetcount, "assetclass":assetclass}], "reason":reason}, content_type="application/json")
    
    def exchange(self,assets,reason,username):
        return self.client.post("/user/ns/exchange",{"exchange":assets,"reason":reason,"username":username}, content_type="application/json")
    
    def reply(self,id,status,reply="success"):
        return self.client.post("/user/ep/reapply",{"id":id,"status":status,"reason":reply}, content_type="application/json")
    
    def maintain(self,assets,reason):
        return self.client.post("/user/ns/applymainten",{"assets":assets,"reason":reason}, content_type="application/json")
    
    def maintainover(self,id,assets):
        return self.client.post("/user/ep/matianover",{"id":id,"assets":assets}, content_type="application/json")
    
    def returnassets(self,assets,reason):
        return self.client.post("/user/ns/returnasset",{"assets":assets,"reason":reason}, content_type="application/json")
    
    def transfer(self,assets,department,reason):
        return self.client.post("/user/ep/transfer",{"transfer":assets,"department":department,"reason":reason}, content_type="application/json")

    def replytransfer(self,assets,id,status,reply="success"):
        payload = {
            "id":id,
            "status":status,
            "reason":reply,
            "asset":assets
        }
        return self.client.post("/user/ep/setcat",payload,content_type="application/json")
    
    def preprocess(self):
        resp = self.addassetclass("class1", 1)
        resp = self.addassetclass("class2",0)
        resp = self.addasset("asset1", "class1", 100)
        resp = self.addasset("asset2", "class2", 1)
        self.logout("ep")
        self.login("ns1","ns1")
        resp = self.apply("asset1", 100, 1,"class1")
        resp = self.apply("asset2", 1, 2,"class2")
        self.logout("ns1")
        self.login("ep","ep")
        resp = self.reply(1,0)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.reply(2,0)
        self.assertEqual(resp.json()["code"], 0)
        self.logout("ep")
        self.login("ns1","ns1")
        
    def test_get_pendings(self):
        et = Entity.objects.filter(id=1).first()
        dep = Department.objects.filter(id=1).first()
        class1 = AssetClass.objects.create(name="class1",entity=et,department=dep,type=True)
        class2 = AssetClass.objects.create(name="class2",entity=et,department=dep,type=False)
        asset1 = Asset.objects.create(name="asset1",entity=et,department=dep,category=class1,type=True,number=100,number_idle=100,price=10)
        asset2 = Asset.objects.create(name="asset2",entity=et,department=dep,category=class2,type=False,status=0,price=1000)
        pending1 = Pending.objects.create(entity=1,department=1,initiator=3,description="I want this",
                                          asset=json.dumps([{"asset1":10}]))
        pending2 = Pending.objects.create(entity=1,department=1,initiator=4,description="I want these",
                                          asset=json.dumps([{"asset1":100,"asset2":1}]))
        resp = self.client.get("/user/ep/getallapply")
        self.assertEqual(resp.json()["info"],  [{'id': 2, 'name': 'ns2', 'reason': 'I want these', 'oper': 0}, {'id': 1, 'name': 'ns1', 'reason': 'I want this', 'oper': 0}])
        
    def test_reply_pendings(self):
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
        pending4 = Pending.objects.create(entity=1,department=1,initiator=3,description="I want these",
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

    def test_exchange(self):
        self.preprocess()
        assets1 = [{"id": 1,"assetname": "asset1","assetnumber": 20}]
        assets2 = [{"id": 2,"assetname": "asset2","assetnumber": 1}]
        assets3 = [{"id": 1,"assetname": "asset1","assetnumber": 30}]
        resp = self.exchange(assets1,"exchange","ns2")
        resp = self.exchange(assets2,"exchange","ns3")
        resp = self.exchange(assets3,"exchange","ns3")
        self.logout("ns1")
        self.login("ep","ep")
        resp = self.reply(3,0)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.reply(4,0)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.reply(5,0)
        self.assertEqual(resp.json()["code"], 0)
        
    def test_maintain_and_return(self):
        self.preprocess()
        assets1 = [{"id": 1,"assetname": "asset1","assetnumber": 20}]
        assets2 = [{"id": 2,"assetname": "asset2","assetnumber": 1}]
        assets3 = [{"id": 1,"assetname": "asset1","assetnumber": 30}]
        resp = self.maintain(assets1,"maintain")
        resp = self.maintain(assets2,"maintain")
        resp = self.maintain(assets3,"maintain")
        resp = self.maintain(assets1,"maintain")
        self.logout("ns1")
        self.login("ep","ep")
        resp = self.reply(3,0)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.reply(4,0)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.reply(5,1,"Fail")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.get("/user/ep/getallmatain")
        self.assertEqual(resp.json()["info"], [{'id': 3, 'assets': [{'id': 1, 'name': 'asset1'}]}, {'id': 4, 'assets': [{'id': 2, 'name': 'asset2'}]}])
        resp = self.reply(6,0)
        self.assertEqual(resp.json()["code"], 0)
        expireasset = [{"id": 1,"name": "asset1","state": 1}]
        backasset = [{"id": 2,"name": "asset2","state": 0}]
        backasset2 = [{"id": 1,"name": "asset1","state": 0}]
        resp = self.maintainover(3,expireasset)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.maintainover(4,backasset)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.maintainover(6,backasset2)
        self.assertEqual(resp.json()["code"], 0)
        self.logout("ep")
        self.login("ns1","ns1")
        assets4 = [{"id": 1,"assetname": "asset1","assetnumber": 20}]
        resp = self.returnassets(assets4,"return")
        self.logout("ns1")
        self.login("ep","ep")
        resp = self.reply(7,0)
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.get("/asset/history?id=1&page=1")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.get("/asset/history?id=2&page=1")
        self.assertEqual(resp.json()["code"], 0)

    def test_assets_in_apply(self):
        et = Entity.objects.filter(id=1).first()
        dep = Department.objects.filter(id=1).first()
        class1 = AssetClass.objects.create(name="class1",entity=et,department=dep,type=True)
        resp = self.client.get("/user/ep/istbd",content_type="application/json")
        self.assertEqual(resp.json()["info"],False)
        asset1 = Asset.objects.create(name="asset1",entity=et,department=dep,category=class1,type=True,number=100,number_idle=100,price=10)
        pending = Pending.objects.create(entity=1,department=1,initiator=3,description="I want these",
                                          asset=json.dumps([{"asset1":100}]))
        resp = self.client.get("/user/ep/assetsinapply?id=1",content_type="application/json")
        self.assertEqual(resp.json()["info"],[{'id': 1, 'assetname': 'asset1', 'assetclass': 'class1', 'assetcount': 100}])
        resp = self.client.get("/user/ep/istbd",content_type="application/json")
        self.assertEqual(resp.json()["info"],True)
    
    def test_clear(self):
        resp = self.addassetclass("yuanshen", 1)
        resp = self.addassetclass("yuanshen2",0)
        resp = self.addasset("hutao", "yuanshen", 100,0)
        resp = self.addasset("hutao2", "yuanshen2", 1)
        resp = self.client.get("/user/ep/assetstbc",content_type="application/json")
        self.assertEqual(resp.json()["code"],0)
        resp = self.client.post("/user/ep/assetclear",{"name":["hutao2"]},content_type="application/json")
        self.assertEqual(resp.json()["detail"],"资产尚未报废或达到年限")
        resp = self.client.post("/user/ep/assetclear",{"name":["hutao3"]},content_type="application/json")
        self.assertEqual(resp.json()["detail"],"资产不存在")
        resp = self.client.post("/user/ep/assetclear",{"name":["hutao"]},content_type="application/json")
        self.assertEqual(resp.json()["code"],0)
    
    def test_query(self):
        et = Entity.objects.filter(id=1).first()
        dep = Department.objects.filter(id=1).first()
        ns1 = User.objects.filter(name="ns1").first()
        ns2 = User.objects.filter(name="ns2").first()
        class1 = AssetClass.objects.create(name="class1",entity=et,department=dep,type=False)
        class2 = AssetClass.objects.create(name="class2",entity=et,department=dep,type=True)
        asset1 = Asset.objects.create(name="asset1",entity=et,department=dep,category=class1,type=False,price=10,create_time=114514,additional=json.dumps({"size":"large"}))
        asset2 = Asset.objects.create(name="asset2",entity=et,parent=asset1,department=dep,category=class1,type=False,price=10,status=1,user=ns2)
        asset3 = Asset.objects.create(name="asset3",entity=et,department=dep,category=class2,type=True,price=100,number=100,number_idle=50,usage=json.dumps([{"ns1":25}]),maintain=json.dumps([{"ns2":25}]))
        asset4 = Asset.objects.create(name="asset4",entity=et,department=dep,belonging=ns1,category=class1,type=False,price=10,status=3,user=ns1,additional=json.dumps({"color":"red"}))
        resp = self.client.post("/user/ep/queryasset",{"parent":"asset1","priceto":50,"status":1,"user":"ns2"},content_type="application/json")
        self.assertEqual(resp.json()["data"],[{'name': 'asset2', 'key': 2, 'description': '', 'assetclass': 'class1', 'type': False}])
        resp = self.client.post("/user/ep/queryasset",{"id":1,"to":114515,"custom":"size","status":-1},content_type="application/json")
        self.assertEqual(resp.json()["data"],[{'name': 'asset1', 'key': 1, 'description': '', 'assetclass': 'class1', 'type': False}])
        resp = self.client.post("/user/ep/queryasset",{"pricefrom":50,"user":"ns1","status":5,"name":"asset3","from":114514},content_type="application/json")
        self.assertEqual(resp.json()["data"],[{'name': 'asset3', 'key': 3, 'description': '', 'assetclass': 'class2', 'type': True}])
        resp = self.client.post("/user/ep/queryasset",{"custom":"color","content":"red","status":3,"belonging":"ns1"},content_type="application/json")
        self.assertEqual(resp.json()["data"],[{'name': 'asset4', 'key': 4, 'description': '', 'assetclass': 'class1', 'type': False}])
    
    def test_modify(self):
        et = Entity.objects.filter(id=1).first()
        dep = Department.objects.filter(id=1).first()
        ns1 = User.objects.filter(name="ns1").first()
        ns2 = User.objects.filter(name="ns2").first()
        class1 = AssetClass.objects.create(name="class1",entity=et,department=dep,type=False)
        class2 = AssetClass.objects.create(name="class2",entity=et,department=dep,type=True)
        asset1 = Asset.objects.create(name="asset1",entity=et,department=dep,category=class1,type=False,price=2000,create_time=114514,additional=json.dumps({"size":"large"}))
        asset2 = Asset.objects.create(name="asset2",entity=et,department=dep,category=class2,type=True,price=1,number=1000,number_idle=1000,status=1,user=ns2)
        resp = self.client.post("/user/ep/modifyasset",{"name":"asset3"})
        self.assertEqual(resp.json()["detail"],"资产不存在")
        resp = self.client.post("/user/ep/modifyasset",{"name":"asset2","parent":"asset1","number":2000,"description":"hehe"})
        self.assertEqual(resp.json()["code"],0)
        resp = self.client.post("/user/ep/modifyasset",{"name":"asset1","parent":"asset3"})
        self.assertEqual(resp.json()["detail"],"父级资产不存在")
        resp = self.client.post("/user/ep/modifyasset",{"name":"asset1","parent":"asset2"})
        self.assertEqual(resp.json()["detail"],"资产类别关系存在自环")
    
    def test_transfer(self):
        resp = self.addassetclass("class1", 1)
        resp = self.addassetclass("class2",0)
        resp = self.addasset("asset1", "class1", 100)
        resp = self.addasset("asset2", "class2", 1)
        assets1 = [{"id":1,"assetname":"asset1","assetnumber":50}]
        assets2 = [{"id":2,"assetname":"asset2","assetnumber":1}]
        assets3 = [{"id":1,"assetname":"asset1","assetnumber":30}]
        resp = self.transfer(assets1,"dep2","transfer")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.transfer(assets2,"dep2","transfer")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.transfer(assets3,"dep2","transfer")
        self.assertEqual(resp.json()["code"], 0)
        self.logout("ep")
        self.login("ep2","ep2")
        resp = self.transfer(assets3,"dep3","transfer")
        resp = self.addassetclass("class3", 1)
        resp = self.addassetclass("class4",0)
        replyassets1 = [{"id":1,"label":"class3","number":50}]
        resp = self.replytransfer(replyassets1,1,0,"success")
        self.assertEqual(resp.json()["code"], 0)
        replyassets2 = [{"id":2,"label":"class4","number":1}]
        resp = self.replytransfer(replyassets2,2,0,"success")
        self.assertEqual(resp.json()["code"], 0)
        replyassets3 = [{"id":1,"label":"class5","number":30}]
        resp = self.replytransfer(replyassets3,3,0,"fail")
        self.assertEqual(resp.json()["detail"], "资产类别不存在")
        replyassets4 = [{"id":1,"label":"class4","number":30}]
        resp = self.replytransfer(replyassets4,3,0,"fail")
        self.assertEqual(resp.json()["detail"], "资产与资产类别类型不符")
        replyassets5 = [{"id":1,"label":"class3","number":30}]
        resp = self.replytransfer(replyassets5,3,1,"reject")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.transfer(assets3,"dep114514","transfer")
        self.assertEqual(resp.json()["detail"], "目标部门不存在")
        dep4 = Department.objects.create(name="dep4", entity=1)
        resp = self.transfer(assets3,"dep4","transfer")
        self.assertEqual(resp.json()["detail"], "目标部门无资产管理员")
        assets4 = [{"id":1,"assetname":"asset1","assetnumber":10}]
        resp = self.transfer(assets4,"dep2","transfer")
        self.assertEqual(resp.json()["detail"], "资产asset1在目标用户所在部门存在同名资产")