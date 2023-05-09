from multiprocessing import Process
from user.models import User
from asset.models import Asset
import pandas as pd
from pandas import DataFrame
import os
from asset.models import gettype
import datetime

from asynctask.models import Async_import_export_task
from utils.exceptions import Failure

from asynctask.task.oss import get_bucket

class AssetExport(Process):
    def __init__(self, user:User):
        super().__init__()
        self.user = user
        
    def run(self):
        task = Async_import_export_task.objects.filter(pid=self.pid).first()
        if not task:
            raise Failure("任务不存在")
        task.status = 2
        task.process_time = datetime.datetime.now().timestamp()
        task.save()
        if not os.path.exists("./tmp"+self.pid+"/"):
            os.mkdir("./tmp"+self.pid+"/")
        if not os.path.exists("./tmp/"+self.pid+"/tmp.xlsx"):
            os.mknod("./tmp/"+self.pid+"/tmp.xlsx")
        path = "./tmp/"+self.pid+"/tmp.xlsx"
        df = pd.read_excel("./tmp/"+self.pid+"/tmp.xlsx")  
        total = Asset.objects.count()
        ids = Asset.objects.values_list("id", flat=True)
        cnt = 0
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
        for i in range(total):
            asset = Asset.objects.filter(id=ids[i]).first()
            df.loc[i] = [asset.parent.name if asset.parent else "", \
                         asset.department.name if asset.department else "", \
                         asset.entity.name if asset.entity else "", \
                         asset.category.name, \
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
                task.process = process
                cnt = 0
                task.save()
        DataFrame(df).to_excel(path, sheet_name="Sheet1", index=False, header=True) 
        bucket = get_bucket()
        bucket.put_object_from_file(path, path)
        task.process = 100
        task.status = 1
        task.finish_time = datetime.datetime.now().timestamp()
        task.save()
            