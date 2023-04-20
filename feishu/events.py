# cyh 2023.4.20
# 处理飞书事件
from multiprocessing import Process, Queue, Lock, Pool 

from utils.exceptions import Check, Failure
from utils.utils_time import get_timestamp

from feishu.models import Event

@Check
def dispatch_event(body: dict):
    # 清理超时事件
    # 7.5小时为超时时间
    expire_delta = 7.5 * 60 * 60
    expire_time = get_timestamp() - expire_delta
    Event.objects.filter(create_time__lt=expire_time).delete()
    # 检测此次事件是否重复，不重复则存下此次事件
    if "schema" in body.keys():
        event_id = body["header"]["event_id"]
        if Event.objects.filter(event_id=event_id).first():
            return
        e = Event(event_id=event_id, create_time=body["header"]["create_time"])
        e.save()
        event_type = body["header"]["event_type"]
        if event_type == "contact.user.created_v3":
            # 员工入职
            p = createUser(body["event"])
            p.start()
        elif event_type == "contact.user.deleted_v3":
            # 员工离职
            p = deleteUser(body["event"])
            p.start()
        elif event_type == "contact.user.updated_v3":
            # 员工信息变更
            p = updateUser(body["event"])
            p.start()
    else:
        event_id = body["uuid"]
        if Event.objects.filter(event_id=event_id).first():
            return
        e = Event(event_id=event_id, create_time=int(body["ts"]))
        e.save()
        event_type = body["event"]["type"]
            
        
class createUser(Process):
    def __init__(self, event:dict):
        super.__init__()
        self.event = event
    @Check
    def run(self):
        pass
    
class deleteUser(Process):
    def __init__(self, event:dict):
        super.__init__()
        self.event = event
    @Check
    def run(self):
        pass
    
class updateUser(Process):
    def __init__(self, event:dict):
        super.__init__()
        self.event = event
    @Check
    def run(self):
        pass
            