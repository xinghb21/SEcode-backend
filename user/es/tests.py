from django.test import TestCase, Client
from user.models import User
import hashlib
from django.contrib.auth.hashers import make_password, check_password

class esTest(TestCase):
    def setUp(self) -> None:
        es = User.objects.create(name="es", password=make_password("es"), 
                                 identity=2, entity=1, department=0)
        op1 = User.objects.create(name="op1", password=make_password("op1"), 
                                 identity=4, entity=1, department=5)
        op2 = User.objects.create(name="op2", password=make_password("op2"), 
                                 identity=4, entity=1, department=5)
        ss = User.objects.create(name="ss", password=make_password("ss"), 
                                 identity=1, entity=0, department=0)
        ep = User.objects.create(name="ep", password=make_password("ep"), 
                                 identity=3, entity=1, department=5)
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
    
    def test_check(self):
        op1 = User.objects.filter(name="op1").first()
        resp = self.client.get("/user/es/check", {"name": "op1"})
        print(resp.content)
        std = {
            "name": op1.name,
            "entity": op1.entity,
            "department": op1.department,
            "identity": op1.identity,
            "lockedapp": op1.lockedapp,
            "locked": op1.locked,
        }
        self.assertJSONEqual(resp.content, std)
    
    def test_check_bad_user(self):
        resp = self.client.get("/user/es/check", {"name": "ayaka"})
        print(resp.content)
    
    # def test_alter(self):
    #     op3 = User.objects.create(name="op3", password=make_password("op3"), 
    #                              identity=4, entity=1, department=0)
    #     resp = self.client.post("/user/es/alter", {"name": "op3", "department": 3})
    #     print(resp.content)
    #     std = {
    #         "code": 0,
    #         "name": op3.name,
    #         "old_department": 0,
    #         "new_department": op3.department,
    #         "info": "转移成功",
    #     }
    #     self.assertJSONEqual(resp.content, std)
