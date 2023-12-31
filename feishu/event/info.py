# cyh
# 飞书人事管理
from django.contrib.auth.hashers import make_password

from department.models import Department, Entity
from user.models import User
from pending.models import Pending

from multiprocessing import Process, Queue, Lock, Pool
import requests 
import random
import json
from hashlib import md5
import time

from feishu.tokens import get_tenant_token
from feishu.event.event_exception import CatchException
from feishu.models import Event, Feishu
# 申请成功提交消息卡片
APPLY_SUBMIT_ID = "ctp_AArTmUIuqcZL"
# 审批结果消息卡片
OUTCOME_ID = "ctp_AArT847gbmi2"

# 发送消息卡片，返回请求结果
def send_card(openid, content):
    req = {
        "receive_id": openid,
        "msg_type": "interactive",
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
    return r


class applySubmit(Process):
    def __init__(self, user:User, data:dict):
        super().__init__()
        self.data = data
        self.user = user
        self.e = Event(eventid="self-created", eventtype="applySubmit")
        self.e.save()
    
    # 给用户发送成功提交申请消息
    @CatchException  
    def run(self):
        if not hasattr(self.user, 'feishu'):
            raise Exception(self.e, "用户%s没有绑定飞书用户" % self.user.name)
        fs:Feishu = self.user.feishu
        content = {
            "type": "template",
            "data": {
                "template_id": APPLY_SUBMIT_ID,
                "template_variable": {
                    "assets": [
                        {
                            "assetname": asset["assetname"],
                            "number": str(asset["assetcount"]),
                        }
                        for asset in self.data["assetsapply"]
                    ],
                    "reason": self.data["reason"]
                }
            }
        }
        r = send_card(fs.openid, content)
        if r.json()["code"] != 0:
            raise Exception(self.e, str(r.json()["code"]) + " " + r.json()["msg"])
        
def get_outcome(status:int, reason:str):
    # 同意
    if status == 0:
        return  "✅<font color=green>**审批通过**</font>"
    elif status == 1:
        return  "❌<font color=red>**审批未通过**</font>\n处理人回复: "+reason
        

class applyOutcome(Process):
    def __init__(self, data:dict):
        super().__init__()
        self.data = data
        self.e = Event(eventid="self-created", eventtype="applyOutcome")
        self.e.save()
    
    # 给用户发送审批结果
    @CatchException  
    def run(self):
        pen = Pending.objects.filter(id=self.data["id"]).first()
        if not pen:
            raise Exception(self.e, "所请求的审批结果对应的待办项不存在")
        user = User.objects.filter(id=pen.initiator).first()
        if not user:
            raise Exception(self.e, "所请求的审批结果对应的发起人不存在")
        if not hasattr(user, 'feishu'):
            raise Exception(self.e, "用户%s没有绑定飞书用户" % user.name)
        fs:Feishu = user.feishu
        outcome = get_outcome(self.data["status"],self.data["reason"])
        content = {
            "type": "template",
            "data": {
                "template_id": OUTCOME_ID,
                "template_variable": {
                    "assets": [
                        {
                            "name": list(asset.keys())[0],
                            "number": str(list(asset.values())[0]),
                        }
                        for asset in json.loads(pen.asset)
                    ],
                    "outcome": outcome,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(pen.review_time))
                }
            }
        }
        print(content)
        r = send_card(fs.openid, content)
        if r.json()["code"] != 0:
            raise Exception(self.e, str(r.json()["code"]) + " " + r.json()["msg"])
        