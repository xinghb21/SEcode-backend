from multiprocessing import Process
from user.models import User
from asset.models import Asset
import pandas as pd
from pandas import DataFrame
import os
import json
from asset.models import gettype
from asynctask.models import status
import datetime

from asynctask.models import Async_import_export_task
from utils.exceptions import Failure
from department.models import Entity, Department

from asynctask.task.oss import get_bucket

class Export(Process):
    def __init__(self, taskid, test):
        super().__init__()
        self.taskid = taskid
        self.test = test
        
    def get_basic(self):
        self.task = Async_import_export_task.objects.filter(id=self.taskid).first()
        if not self.task:
            raise Failure("任务不存在")
        self.task.pid = self.pid
        self.task.status = 2
        self.task.process_time = datetime.datetime.now().timestamp()
        self.task.save()
        if not os.path.exists("./tmp"):
            os.mkdir("./tmp")
        if not os.path.exists("./tmp/"+str(self.pid)):
            os.mkdir("./tmp/"+str(self.pid))
        if not os.path.exists("./tmp/"+str(self.pid)+"/tmp.xlsx"):
            pd.DataFrame().to_excel("./tmp/"+str(self.pid)+"/tmp.xlsx", sheet_name="Sheet1", index=False, header=True)
        path = "./tmp/"+str(self.pid)+"/tmp.xlsx"
        self.path = path
        self.df = pd.read_excel("./tmp/"+str(self.pid)+"/tmp.xlsx") 
        ids = self.task.ids
        if not ids:
            et = Entity.objects.filter(id=self.task.user.entity).first()
            dep = Department.objects.filter(id=self.task.user.department).first()
            ids = Asset.objects.filter(entity=et, department=dep).values_list("id", flat=True)
            total = Asset.objects.count()
            self.task.ids = json.dumps(list(ids))
            self.task.save()
        else:
            ids = json.loads(ids)
            total = len(ids)
        self.ids = ids
        self.total = total
        
    def finish(self):
        DataFrame(self.df).to_excel(self.path, sheet_name="Sheet1", index=False, header=True) 
        if not self.test:
            bucket = get_bucket()
            bucket.put_object_from_file(self.task.file_path, self.path)
        os.remove(self.path)
        os.rmdir("./tmp/"+str(self.pid)+"/")
        self.task.process = 100
        self.task.status = 1
        self.task.finish_time = datetime.datetime.now().timestamp()
        self.task.save()

class AssetExport(Export):
    def __init__(self, taskid, test):
        super().__init__(taskid, test)
        
    def run(self):
        self.get_basic()
        cnt = 0
        df = self.df
        df['上级资产名称'] = None
        df['部门'] = None
        df['业务实体'] = None
        df['类别'] = None
        df['种类'] = None
        df['名称'] = None
        df['挂账人'] = None
        df['资产原价值'] = None
        df['资产使用年限'] = None
        df['资产创建时间'] = None
        df['描述'] = None
        ids = self.ids
        total = self.total
        for i in range(total):
            asset = Asset.objects.filter(id=ids[i]).first()
            df.loc[i] = [asset.parent.name if asset.parent else "", \
                         asset.department.name if asset.department else "", \
                         asset.entity.name if asset.entity else "", \
                         asset.category.name if asset.category else "", \
                         gettype(asset.type), \
                         asset.name, \
                         asset.belonging.name if asset.belonging else "", \
                         asset.price, \
                         asset.life, \
                        datetime.datetime.fromtimestamp(asset.create_time).strftime("%Y-%m-%d %H:%M:%S"), \
                         asset.description, \
                         ]
            cnt += 1
            if cnt == 100:
                process = int(i/total*100)
                self.task.process = process
                cnt = 0
                self.task.save()
        self.finish()
        
class TaskExport(Export):
    def __init__(self, taskid, test):
        super().__init__(taskid, test)
        
    def run(self):
        self.get_basic()
        cnt = 0
        df = self.df
        df['任务名称'] = None
        df['任务发起人'] = None
        df['任务创建时间'] = None
        df['任务状态'] = None
        df['任务处理时间'] = None
        df['任务完成时间'] = None
        df['处理进度'] = None
        ids = self.ids
        total = self.total
        for i in range(total):
            task = Async_import_export_task.objects.filter(id=ids[i]).first()
            df.loc[i] = [task.name, \
                         task.user.name if task.user else "", \
                         datetime.datetime.fromtimestamp(task.create_time).strftime("%Y-%m-%d %H:%M:%S"), \
                         status(task.status), \
                         datetime.datetime.fromtimestamp(task.process_time).strftime("%Y-%m-%d %H:%M:%S"), \
                         datetime.datetime.fromtimestamp(task.finish_time).strftime("%Y-%m-%d %H:%M:%S"), \
                         task.process, \
                         ]
            cnt += 1
            if cnt == 100:
                process = int(i/total*100)
                self.task.process = process
                cnt = 0
                self.task.save()
        self.finish()