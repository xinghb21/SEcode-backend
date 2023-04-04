from django.test import TestCase, Client
from user.models import User
import hashlib
from django.contrib.auth.hashers import make_password, check_password

class esTest(TestCase):
    def setUp(self) -> None:
        es = User.objects.create(name="es", password=make_password("es"), 
                                 identity=2, entity=1, department=0)
        user1 = User.objects.create(name="op1", password=make_password("user1"), 
                                 identity=4, entity=1, department=5)
        user2 = User.objects.create(name="op2", password=make_password("user2"), 
                                 identity=4, entity=1, department=5)
        ss = User.objects.create(name="ss", password=make_password("ss"), 
                                 identity=1, entity=0, department=0)
        ep = User.objects.create(name="ep", password=make_password("ep"), 
                                 identity=3, entity=1, department=5)
    
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
    
    # def test_
        
