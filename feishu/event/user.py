# cyh
# 飞书人事管理
from django.contrib.auth.hashers import make_password

from department.models import Department, Entity
from user.models import User

from multiprocessing import Process, Queue, Lock, Pool
import requests 
import random
import json
from hashlib import md5

from feishu.tokens import get_tenant_token
from feishu.event.event_exception import CatchException
from feishu.models import Event, Feishu

# 构造新业务实体和部门，返回业务实体和最后一级部门的id
def build_departments(items, e):
    parent_dept = []
    for item in items:
        parent_dept.append(item["name"])
    parent_dept.reverse()
    if len(parent_dept) == 0:
        raise Exception(e, "该用户没有所属部门")
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
    return (et, parent)

class createUser(Process):
    def __init__(self, event:dict, e:Event):
        super().__init__()
        self.event = event
        self.e = e
    
    @CatchException  
    def run(self):
        obj = self.event["object"]
        fs = Feishu.objects.filter(unionid=obj["union_id"]).first()
        if fs:
            raise Exception(self.e, "该飞书用户已经存在")
        dep_id = obj["department_ids"][0]
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
        et, parent = build_departments(items, self.e)
        resp = requests.get("https://open.feishu.cn/open-apis/contact/v3/departments/"+dep_id,
                            params={
                                "department_id_type": "open_department_id",
                            },
                            headers={
                                "Authorization": "Bearer "+ get_tenant_token(),
                            })
        res = resp.json()
        if res["code"] != 0:
            raise Exception(self.e, str(res["code"]) + res["msg"])
        dep_name = res["data"]["department"]["name"]
        dep = Department.objects.filter(entity=et.id, name=dep_name).first()
        if not dep:
            dep = Department.objects.create(name=dep_name, entity=et.id, parent=parent)
        username = obj["name"]
        user = User.objects.filter(name=username, entity=et.id, department=dep.id).first()
        if user:
            r = random.sample('0123456789', 4)
            username = obj["name"]
            for ch in r:
                username += ch
            user = User.objects.filter(name=username, entity=et.id, department=dep.id).first()
            while user:
                r = random.sample('0123456789abcdefghijklmnopqrstuvwxyz', 4)
                username = obj["name"]
                for ch in r:
                    username += ch
                user = User.objects.filter(name=username, entity=et.id, department=dep.id).first()    
        r = random.sample('zyxwvutsrqponmlkjihgfedcba',10)
        password = ""
        for ch in r:
            password += ch
        # 通过飞书告知用户初始密码
        content = {"text": "账号: "+username+"\n密码: "+password}
        req = {
            "receive_id": obj["open_id"], # chat id
            "msg_type": "text",
            "content": json.dumps(content)
        }
        payload = json.dumps(req)
        r = requests.post("https://open.feishu.cn/open-apis/im/v1/messages",
                            data=payload,
                            params={"receive_id_type":"open_id"},
                            headers={
                                "Authorization": "Bearer "+get_tenant_token(),
                                "Content-Type": "application/json; charset=utf-8",
                            },
                            )
        m = md5()
        m.update(password.encode(encoding='utf8'))
        m = m.hexdigest()
        user = User.objects.create(name=username, entity=et.id, department=dep.id, password=make_password(m))
        fs = Feishu.objects.create(user=user, name=username, userid=obj["user_id"], unionid=obj["union_id"], openid=obj["open_id"])
        if r.json()["code"] != 0:
            raise Exception(self.e, str(r.json()["code"]) + r.json()["msg"])
class deleteUser(Process):
    def __init__(self, event:dict, e:Event):
        super().__init__()
        self.event = event
        self.e = e
        
    @CatchException  
    def run(self):
        openid = self.event["object"]["open_id"]
        fs = Feishu.objects.filter(openid=openid).first()
        if not fs:
            raise Exception(self.e, "被删除的飞书用户不存在")
        user = fs.user
        if not user:
            fs.delete()
        user.delete()
        fs.delete()
    
# 只处理部门变更的情况
class updateUser(Process):
    def __init__(self, event:dict, e:Event):
        super().__init__()
        self.event = event
        self.e = e
    
    @CatchException  
    def run(self):
        old_obj = self.event["old_object"]
        obj = self.event["object"]
        if "department_ids" in old_obj.keys():
            old_dep = old_obj["department_ids"][0]
            new_dep = obj["department_ids"][0]
            if old_dep == new_dep:
                raise Exception(self.e, "用户并未变更部门")
            # 获取父部门列表
            resp = requests.get("https://open.feishu.cn/open-apis/contact/v3/departments/parent",
                                params={
                                    "department_id_type": "open_department_id",
                                    "department_id": new_dep,
                                },
                                headers={
                                    "Authorization": "Bearer " + get_tenant_token(),
                                })
            res = resp.json()
            if res["code"] != 0:
                raise Exception(self.e, str(res["code"]) + res["msg"])
            items = res["data"]["items"]
            et, parent = build_departments(items, self.e)
            resp = requests.get("https://open.feishu.cn/open-apis/contact/v3/departments/"+new_dep,
                                params={
                                    "department_id_type": "open_department_id",
                                },
                                headers={
                                    "Authorization": "Bearer "+ get_tenant_token(),
                                })
            res = resp.json()
            if res["code"] != 0:
                raise Exception(self.e, res["code"] + res["msg"])
            dep_name = res["data"]["department"]["name"]
            dep = Department.objects.filter(entity=et.id, name=dep_name).first()
            if not dep:
                dep = Department.objects.create(name=dep_name, entity=et.id, parent=parent)
            fs = Feishu.objects.filter(unionid=obj["union_id"]).first()
            if not fs:
                raise Exception(self.e, "该飞书用户不存在")
            user = fs.user
            if not user:
                raise Exception(self.e, "飞书用户 "+fs.name+" 没有绑定系统中用户")
            user.department = dep.id
            user.entity = et.id
            user.save()
                
                