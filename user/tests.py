from django.test import TestCase, Client
from user.models import User
import hashlib

# Create your tests here.

class userTests(TestCase):
    def setUp(self):
        alice = User.objects.create(name="Alice", password=self.md5("GenshinImpact"))
        super_user = User.objects.create(name="chen", password=self.md5("ILoveGenshinImpact"), identity="1")
        locked_user = User.objects.create(name="locked", password=self.md5("locked"), locked=True)
        
    def md5(self, s):
        obj = hashlib.md5("wochao,O!".encode())
        obj.update(s.encode())
        return obj.hexdigest()
    
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
    
    def test_bad_username(self):
        res = self.login("abab", self.md5("GenshinImpact"))
        self.assertJSONEqual(res.content, {"code": -1, "info": "用户不存在"})
        
    def test_bad_pw(self):
        res = self.login("Alice", self.md5("GI"))
        self.assertJSONEqual(res.content, {"code": -1, "info": "密码错误"})
        
    def test_locked(self):
        res = self.login("locked", self.md5("locked"))
        self.assertJSONEqual(res.content, {"code": -1, "info": "此用户已被管理员封禁"})
        

