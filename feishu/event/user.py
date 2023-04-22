# cyh
from django.contrib.auth.hashers import make_password

from department.models import Department, Entity
from user.models import User

from multiprocessing import Process, Queue, Lock, Pool
import requests 
import random
from hashlib import md5

from feishu.tokens import get_tenant_token
from feishu.event.event_exception import CatchException
from feishu.models import Event, Feishu
   


class createUser(Process):
    def __init__(self, event:dict, e:Event):
        super.__init__()
        self.event = event
        self.e = e
    
    @CatchException  
    def run(self):
        obj = self.event["object"]
        fs = Feishu.objects.filter(unionid=obj["union_id"]).first()
        if fs:
            raise Exception(self.e, "该飞书用户已经存在")
        dep_id = obj["department_ids"][0]
        # 父部门名称列表
        parent_dept = []
        # 获取父部门列表
        resp = requests.get("https://open.feishu.cn/open-apis/contact/v3/departments/parent",
                            params={
                                "department_id_type": "open_department_id",
                                "department_id": dep_id
                            },
                            headers={
                                "Authorization": "Bearer " + get_tenant_token(),
                            })
        res = resp.json()
        if res["code"] != 0:
            raise Exception(self.e, res["msg"])
        items = res["data"]["items"]
        for item in items:
            parent_dept.append(item["name"])
        parent_dept.reverse()
        entity = parent_dept[0]
        et = Entity.objects.filter(name=entity).first()
        if not et:
            et = Entity.objects.create(name=entity)
        parent = 0
        for i in range(1, len(parent_dept)):
            dep = Department.objects.filter(entity=et.id, name=parent_dept[i]).first()
            if not dep:
                dep = Department.objects.create(name=parent_dept[i], entity=et.id, parent=parent)
            parent = dep.id
        resp = requests.get("https://open.feishu.cn/open-apis/contact/v3/departments/"+dep_id,
                            params={
                                "department_id_type": "open_department_id",
                            },
                            headers={
                                "Authorization": "Bearer "+ get_tenant_token(),
                            })
        res = resp.json()
        if res["code"] != 0:
            raise Exception(self.e, res["msg"])
        dep_name = res["data"]["department"]["name"]
        dep = Department.objects.filter(entity=et.id, name=dep_name).first()
        if not dep:
            dep = Department.objects.create(name=dep_name, entity=et.id, parent=parent)
        username = obj["name"]
        user = User.objects.filter(name=username, entity=et.id, department=dep.id).first()
        if user:
            raise Exception(self.e, "用户已经存在")
        else:
            password = random.sample('zyxwvutsrqponmlkjihgfedcba',10)
            m = md5()
            m.update(password.encode(encoding='utf8'))
            m = m.hexdigest()
            user = User.objects.create(name=username, entity=et.id, department=dep.id, password=make_password(m))
        fs = Feishu.objects.create(user=user, name=username, userid=obj["user_id"], unionid=obj["union_id"], openid=obj["open_id"])
        
            
        
            
        
    
class deleteUser(Process):
    def __init__(self, event:dict):
        super.__init__()
        self.event = event
        
    def run(self):
        pass
    
class updateUser(Process):
    def __init__(self, event:dict):
        super.__init__()
        self.event = event
    
    def run(self):
        pass
            