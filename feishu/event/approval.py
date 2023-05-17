# cyh
# 飞书审批对接
import yaml
from department.models import Department, Entity
from user.models import User
from pending.models import Pending

from multiprocessing import Process, Queue, Lock, Pool
import requests 
import random
import json

from feishu.tokens import get_tenant_token
from feishu.event.event_exception import CatchException
from feishu.models import Event, Feishu

from utils.utils_time import get_timestamp

file = open("config/config.yml", "r", encoding="utf-8")
env = yaml.load(file, Loader=yaml.SafeLoader)

# 审批定义标识
APPROVAL_CODE = "AFBDFE7C-4934-4F7B-98A1-94E13C06453A"

# 发出新审批通知，一次发一个，实例id和任务id相同，均取待办项的id
class newApproval(Process):
    def __init__(self, penid):
        super().__init__()
        self.penid = penid
        self.e = Event(eventid="self-created", eventtype="newApproval")
        self.e.save()
    
    @CatchException
    def run(self):
        pen = Pending.objects.filter(id=self.penid).first()
        if not pen:
            raise Exception(self.e, "审批待办项不存在")
        dep = Department.objects.filter(id=pen.department).first()
        if not dep:
            raise Exception(self.e, "待办所属部门不存在")
        ep = User.objects.filter(id=dep.admin).first()
        if not ep:
            raise Exception(self.e, "待办项所属的部门没有资产管理员")
        print(ep)
        init = User.objects.filter(id=pen.initiator).first()
        if not init:
            raise Exception(self.e, "待办发起人不存在")
        print(hasattr(ep, 'feishu'))
        if not hasattr(ep, 'feishu'):
            raise Exception(self.e, "用户%s没有绑定飞书用户" % ep.name)
        fs_ep:Feishu = ep.feishu
        print(hasattr(init, 'feishu'))
        if not hasattr(init, 'feishu'):
            raise Exception(self.e, "用户%s没有绑定飞书用户" % init.name)
        fs_init:Feishu = init.feishu
        now = int(get_timestamp() * 1000)
        req = {
            "approval_code": APPROVAL_CODE,
            "status": "PENDING",
            "instance_id" : str(pen.id),
            # 实例的链接，还不知道有什么用，先填成百度好了
            "links": {
                "pc_link": "https://www.baidu.com",
                "mobile_link": "https://www.baidu.com",
            },
            "title": "@i18n@1",
            # 发起人的openid
            "open_id": fs_init.openid,
            # 暂时不传部门id
            "department_id": "",
            "start_time": now,
            "end_time": 0,
            "update_time": now,
            "display_method": "SIDEBAR",
            "update_mode": "UPDATE",
            "task_list":[
                  {
                      "task_id": str(pen.id) + str(fs_init.id),
                      "open_id": fs_ep.openid,
                      "title": "@i18n@2",
                      "links": {
                          "pc_link": env["frontend"]+"/feishu/approval?penid%3D"+str(pen.id),
                          "mobile_link":env["frontend"]+"/feishu/approval?penid%3D"+str(pen.id),
                      },
                    "status": "PENDING",
                    "create_time": now,
                    "end_time": 0,
                    "update_time": now,
                    "action_configs": [
                    ],
                    "display_method": "SIDEBAR",
                  }
            ],
            "i18n_resources": [
                {
                    "locale": "zh-CN",
                    "texts": [
                        {
                            # 审批实例的名称
                            "key": "@i18n@1",
                            "value": "资产操作申请"
                        },
                        {
                            # 审批任务的名称
                            "key": "@i18n@2",
                            "value": "资产领用"
                        },
                    ],
                    "is_default": True,
                }
            ]
        }
        payload = json.dumps(req)
        r = requests.post("https://open.feishu.cn/open-apis/approval/v4/external_instances",
                            data=payload,
                            headers={
                                "Authorization": "Bearer "+get_tenant_token(),
                                "Content-Type": "application/json; charset=utf-8",
                            },
                            )
        if r.json()["code"] != 0:
            raise Exception(self.e, str(r.json()["code"]) + " " + r.json()["msg"])

        
        