from django.test import TestCase, Client
from user.models import User
from department.models import Department, Entity
from utils.utils_time import get_timestamp
from django.contrib.auth.hashers import make_password, check_password

class esTest(TestCase):
    def setUp(self) -> None:
        et = Entity.objects.create(name="et")
        dep = Department.objects.create(name="dep", entity=1, admin=1)
        ep = User.objects.create(name="ep", password=make_password("ep"), 
                                 identity=3, entity=1, department=1)
        op1 = User.objects.create(name="op1", password=make_password("op1"), 
                                 identity=4, entity=1, department=1)
        op2 = User.objects.create(name="op2", password=make_password("op2"), 
                                 identity=4, entity=1, department=1)
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
    
    def test_post_class(self):
        resp = self.client.post("/asset/assetclass", {"name": "assetclass", "type": 1})
        self.assertEqual(resp.json()["code"], 0)
        
    def test_post(self):
        self.client.post("/asset/assetclass", {"name": "assetclass", "type": 1})
        self.client.post("/asset/assetclass", {"name": "yuanshen", "type": 0})
        resp = self.client.post("/asset/post", 
                                [{"category": "assetclass", "name": "keqing", "life": 100, "number": 1000, "price": 1000}, {"category": "yuanshen", "name": "keqi", "life": 100, "price": 1000}]
                                ,content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.get("/asset/allhistory?page=1")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_get(self):
        self.client.post("/asset/assetclass", {"name": "assetclass", "type": 1})
        self.client.post("/asset/assetclass", {"name": "yuanshen", "type": 0})
        resp = self.client.post("/asset/post", [{"category": "assetclass", "name": "keqing", "life": 100, "number": 1000, "price": 1000}, {"category": "yuanshen", "name": "keqi", "life": 100, "price": 1000}]
                         ,content_type="application/json")
        resp = self.client.get("/asset/get?page=1")
        self.assertEqual(resp.json()["data"], [{'key': 1, 'name': 'keqing', 'category': 'assetclass', 'description': '', 'type': True}, {'key': 2, 'name': 'keqi', 'category': 'yuanshen', 'description': '', 'type': False}])
        
    def test_delete(self):
        self.client.post("/asset/assetclass", {"name": "assetclass", "type": 1})
        resp = self.client.post("/asset/assetclass", {"name": "yuanshen", "type": 0})
        resp = self.client.post("/asset/post", [{"category": "assetclass", "name": "keqing", "life": 100, "number": 1000, "price": 1000}, {"category": "yuanshen", "name": "keqi", "life": 100, "price": 1000}],content_type="application/json")
        resp = self.client.delete("/asset/delete", ["keqi", "keqing"], content_type="application/json")
        self.assertEqual(resp.json()["code"], 0)
    
    def test_get_attributes(self):
        self.client.post("/asset/assetclass", {"name": "assetclass", "type": 1})
        self.client.post("/asset/assetclass", {"name": "yuanshen", "type": 0})
        resp = self.client.post("/asset/post", [{"category": "assetclass", "name": "keqing", "life": 100, "number": 1000, "price": 1000, "additional": {"abab": 1}},
                                        {"category": "yuanshen", "name": "keqi", "life": 100, "price": 1000, "additional": {"cdcd": 2}}]
                        ,content_type="application/json")
        resp = self.client.get("/asset/getdetail", {"id": 1})
        self.assertEqual(resp.json()["code"], 0)
        resp = self.client.get("/asset/fulldetail/1",content_type="application/json")
        resp = self.client.get("/asset/get?page=1")
        self.assertEqual(resp.json()["code"], 0)
        
    def test_create_and_get_attributes(self):
        self.client.post("/asset/createattributes", {"name": "attribute1"})
        resp = self.client.get("/asset/attributes")
        self.assertEqual(resp.json()["info"], ['attribute1'])
    
    def test_create_and_get_label(self):
        labels = ["a","b"]
        resp = self.client.post("/asset/setlabel",data = {"label": labels}, content_type="application/json")
        resp = self.client.get("/asset/usedlabel")
        self.assertEqual(resp.json()["info"], ['a','b'])
        
    def test_asset_class_tree(self):
        self.client.post("/asset/assetclass", {"name": "class1","type":0})
        self.client.post("/asset/assetclass", {"name": "class2","parent":"class1","type":0})
        self.client.post("/asset/assetclass", {"name": "class3","type":1})
        self.client.delete("/asset/assetclass", {"name": "class3"})
        self.client.post("/asset/assetclass", {"name": "class4","type":0})
        self.client.put("/asset/assetclass", {"oldname": "class4","newname":"class3","type":0})
        resp = self.client.get("/asset/assetclasstree")
        self.assertEqual(resp.json()["info"], {'dep': {'class1,0': {'class2,0': '$'}, 'class3,1': '$', 'class4,0': '$'}})

    def test_get_by_condition(self):
        self.client.post("/asset/assetclass", {"name": "class1","type":0})
        resp = self.client.post("/asset/post", 
                         [{"category": "class1", "name": "keqing", "life": 100, "price": 1000}, 
                          {"category": "class1", "name": "keqi", "life": 100, "price": 1000},
                          ]
                         ,content_type="application/json")
        resp = self.client.post("/asset/post", 
                         [{"category": "class1", "name": "ningguang", "parent": "keqi", "life": 100, "price": 1000}]
                         ,content_type="application/json")
        
        resp = self.client.get("/asset/get?page=1")
        self.assertEqual(resp.json()["code"], 0)
    
    def test_get_belonging(self):
        resp = self.client.get("/asset/getbelonging")
        self.assertEqual(resp.json(), {'code': 0, 'entity': 'et', 'department': 'dep'})
    

