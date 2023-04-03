from django.test import TestCase, Client
from user.models import User
import hashlib
from django.contrib.auth.hashers import make_password, check_password
# Create your tests here.

class userTests(TestCase):
    def setUp(self):
        alice = User.objects.create(name="Alice", password=make_password("GenshinImpact"))
    
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
    
    def test_login(self):
        res = self.login("Alice", "GenshinImpact")
        print(res.content)
        # std_output = {
        #     "code": 0,
        #     "name": "Alice",
        #     "entity": "0",
        # }
        # self.assertJSONEqual(res.content, )
    
    def test_bad_username(self):
        res = self.login("abab", "GenshinImpact")
        print(res.content)
        self.assertJSONEqual(res.content, {"code": -1, "info": "用户不存在"})
        
    def test_bad_pw(self):
        res = self.login("Alice", "GI")
        print(res.content)
        self.assertJSONEqual(res.content, {"code": -1, "info": "密码错误"})
    
