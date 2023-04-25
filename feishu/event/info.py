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

APPLY_SUCCESS_ID = "ctp_AArTmUIuqcZL"

class applySuccess(Process):
    def __init__(self, user:User, data:dict):
        super().__init__()
        self.data = data
        self.user = user
    
    # 给用户发送成功提交申请消息
    @CatchException  
    def run(self):
        if not hasattr(self.user, 'feishu'):
            raise Exception("用户%s没有绑定飞书用户" % self.user.name)
        fs:Feishu = self.user.feishu
        content = {
            "type": "template",
            "data": {
                "template_id": APPLY_SUCCESS_ID,
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
        req = {
            "receive_id": fs.openid,
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
        if r.json()["code"] != 0:
            raise Exception(self.e, str(r.json()["code"]) + " " + r.json()["msg"])
        