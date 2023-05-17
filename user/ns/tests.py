from django.test import TestCase, Client
from user.models import User
from department.models import Department, Entity
from asset.models import Asset,AssetClass
import json
from django.contrib.auth.hashers import make_password
from pending.models import Pending

class esTest(TestCase):
    def setUp(self) -> None:
        op1 = User.objects.create(name="op1", password=make_password("op1"), 
                                 identity=4, entity=1, department=1)
        op2 = User.objects.create(name="op2", password=make_password("op2"), 
                                 identity=4, entity=1, department=1)
        op3 = User.objects.create(name="op3", password=make_password("op3"), 
                                 identity=4, entity=2, department=2)
        op4 = User.objects.create(name="op4", password=make_password("op4"), 
                                 identity=4, entity=1, department=3)
        ss = User.objects.create(name="ss", password=make_password("ss"), 
                                 identity=1, entity=0, department=0)
        es = User.objects.create(name="es", password=make_password("es"), 
                                 identity=2, entity=1, department=0)
        ep = User.objects.create(name="ep", password=make_password("ep"), 
                                 identity=3, entity=1, department=1)
        es2 = User.objects.create(name="es2", password=make_password("es2"), 
                                 identity=2, entity=1, department=0),
        ep2 = User.objects.create(name="ep2", password=make_password("ep2"), 
                                 identity=3, entity=1, department=3)
        et1 = Entity.objects.create(name="et1", admin=5)
        et2 = Entity.objects.create(name="et2", admin=5)
        et3 = Entity.objects.create(name="et3",admin=7)
        dep1 = Department.objects.create(name="dep1", entity=1, parent=0, admin=6)
        dep2 = Department.objects.create(name="dep2", entity=2, parent=0, admin=6)
        dep3 = Department.objects.create(name="dep3", entity=1, parent=0, admin=6)
        self.login("ep", "ep")
        resp = self.addassetclass("yuanshen", 1)
        resp = self.addassetclass("yuanshen2",0)
        resp = self.addasset("hutao", "yuanshen", 100,True)
        resp = self.addasset("hutao2", "yuanshen2", 1,False)
        resp = self.addasset("hutao3", "yuanshen2", 1,False)
        self.logout("ep")
        self.login("ep2","ep2")
        resp = self.addassetclass("ys", 1)
        resp = self.addassetclass("ys2",0)
        self.logout("ep2")
        self.login("op1", "op1")
        resp = self.apply("hutao", 50, 1,"yuanshen")
        resp = self.apply("hutao2", 1, 2,"yuanshen2")
        resp = self.apply("hutao3", 1, 3,"yuanshen2")
        
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
    
    def addasset(self, name, cate, number,img=False):
        return self.client.post("/asset/post", [{"name": name, "category": cate,
                                                "life": 10, "number": number, "price": 10000,"hasimage":img,
                                                }], content_type="application/json")
    
    def reply(self,id,status,reply="success"):
        return self.client.post("/user/ep/reapply",{"id":id,"status":status,"reason":reply}, content_type="application/json")
    
    def apply(self, assetname, assetcount, id,assetclass, reason="abab"):
        return self.client.post("/user/ns/userapply", {"assetsapply": [{"id":id, "assetname":assetname, "assetcount":assetcount, "assetclass":assetclass}], "reason":reason}, content_type="application/json")
    
    def exchange(self,assets,reason,username):
        return self.client.post("/user/ns/exchange",{"exchange":assets,"reason":reason,"username":username}, content_type="application/json")
    
    def maintain(self,assets,reason):
        return self.client.post("/user/ns/applymainten",{"assets":assets,"reason":reason}, content_type="application/json")
    
    def returnassets(self,assets,reason):
        return self.client.post("/user/ns/returnasset",{"assets":assets,"reason":reason}, content_type="application/json")
    
    def setcat(self,assetname,label):
        return self.client.post("/user/ns/setcat",{"assetname":assetname,"label":label}, content_type="application/json")
    
    def preprocess(self):
        self.logout("op1")
        self.login("ep","ep")
        resp = self.reply(1,0)
        resp = self.reply(2,0)
        self.logout("ep")
        self.login("op1","op1")
        assets1 = [{"id": 1,"assetname": "hutao","assetnumber": 20}]
        assets2 = [{"id": 2,"assetname": "hutao2","assetnumber": 1}]
        return assets1,assets2
    
    def test_apply_and_reply(self):
        resp = self.client.get("/user/ns/getassets?page=1")
        self.assertEqual(resp.json()["info"], [{'id': 1, 'name': 'hutao', 'type': 1, 'count': 50}])
        p = Pending.objects.filter(initiator=1)
        self.assertNotEqual(p.first(), None)
        self.logout("op1")
        self.login("ep","ep")
        resp = self.reply(1,0)
        resp = self.reply(2,1,"U! OP")
        resp = self.reply(3,0)
        self.logout("ep")
        self.login("op1","op1")
        resp = self.apply("keqing", 50, 1,"yuanshen")
        self.assertEqual(resp.json()["detail"], "资产keqing不存在")
        resp = self.apply("hutao", 50, 114514,"yuanshen")
        self.assertEqual(resp.json()["detail"], "资产id错误")
        resp = self.apply("hutao", 114514,1,"yuanshen")
        self.assertEqual(resp.json()["detail"], "资产hutao闲置数量不足")
        resp = self.apply("hutao3", 1,3,"yuanshen2")
        self.assertEqual(resp.json()["detail"], "资产hutao3未处于闲置状态")
        resp = self.client.get("/user/ns/possess?page=1")
        self.assertEqual(resp.json()["assets"], [{'id': 3, 'name': 'hutao3', 'type': 0, 'state': {'1': 1},'haspic':False}, {'id': 1, 'name': 'hutao', 'type': 1, 'state': {'1': 50},'haspic':True}])
    
    def test_exchange_and_reply(self):
        assets1,assets2 = self.preprocess()
        resp = self.exchange(assets1,"I'm OP","op2")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.exchange(assets1,"I'm OP","op4")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.exchange(assets2,"I'm OP","op4")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.exchange(assets2,"I'm OP","opop")
        self.assertEqual(resp.json()["detail"], "目标用户不存在")
        resp = self.exchange(assets2,"I'm OP","ep")
        self.assertEqual(resp.json()["detail"], "目标用户不是员工")

    def test_maintain_and_reply(self):
        assets1,assets2 = self.preprocess()
        resp = self.maintain(assets1,"I'm OP")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.maintain(assets2,"I'm OP")
        self.assertEqual(resp.json()["code"], 0)
    
    def test_return_and_reply(self):
        assets1,assets2 = self.preprocess()
        resp = self.returnassets(assets1,"I'm OP")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.returnassets(assets2,"I'm OP")
        self.assertEqual(resp.json()["code"], 0)
        bad_assets1 = [{"id": 114514,"assetname": "hutao114514","assetnumber": 1}]
        bad_assets2 = [{"id": 1,"assetname": "hutao","assetnumber": 114514}]
        resp = self.maintain(bad_assets1,"bad")
        self.assertEqual(resp.json()["detail"], "资产信息错误")
        resp = self.maintain(bad_assets2,"bad")
        self.assertEqual(resp.json()["detail"], "资产数量错误")
    
    def test_getapply(self):
        resp = self.client.get("/user/ns/getallapply")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_assetsinapply(self):
        resp = self.client.get("/user/ns/assetsinapply?id=1")
        self.assertEqual(resp.json(), {'code': 0, 'info': [{'id': 1, 'assetname': 'hutao', 'assetcount': 50}],'user':''})
        
    def test_deleteapply(self):
        resp = self.client.delete("/user/ns/deleteapplys",{"id":1},content_type="application/json")
        self.assertEqual(resp.json(), {'code': -1, 'detail': '不能删除资产管理员未处理的申请'})
        pending = Pending.objects.filter(id=1).first()
        pending.result = 1
        pending.save()
        resp = self.client.delete("/user/ns/deleteapplys",{"id":1},content_type="application/json")
        self.assertEqual(resp.json(), {'code': 0, 'info': 'ok'})
    
    def test_message(self):
        self.logout("op1")
        self.login("ep","ep")
        resp = self.reply(1,0)
        resp = self.reply(2,1,"U! OP")
        self.logout("ep")
        self.login("op1","op1")
        resp = self.client.get("/user/ns/getmessage",content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.get("/user/ns/hasmessage",content_type="application/json")
        self.assertEqual(resp.json()["info"],True)
        resp = self.client.post("/user/ns/read",{"id":2},content_type="application/json")
        self.assertEqual(resp.json()["code"],0)
        resp = self.client.delete("/user/ns/deletemsg?id=2",content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_setcat(self):
        resp = self.setcat("hutao114514","yuanshen")
        self.assertEqual(resp.json()["detail"], "资产不存在")
        resp = self.setcat("hutao","yuanshen114514")
        self.assertEqual(resp.json()["detail"], "资产类别不存在")
        resp = self.setcat("hutao","yuanshen2")
        self.assertEqual(resp.json()["detail"], "资产与资产类别类型不符")
        resp = self.setcat("hutao","yuanshen")
        self.assertEqual(resp.json()["code"], 0)