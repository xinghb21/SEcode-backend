from django.db import models
from department.models import Department, Entity
from user.models import User
from utils.utils_time import get_timestamp
from utils.exceptions import Failure

# Create your models here.

class Async_import_export_task(models.Model):
    id = models.AutoField(primary_key=True)
    
    name = models.CharField(max_length=255, blank=True, null=True)
    
    entity = models.ForeignKey(Entity, models.DO_NOTHING, blank=True, null=True)
    
    # 异步任务的发起人
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    
    # 异步任务的创建时间
    create_time = models.FloatField(default=get_timestamp)
    
    # 异步任务状态,0为失败，1为成功完成，2为进行中，3为未开始，4为已隐藏
    status = models.SmallIntegerField(default=3)
    
    # 处理时间
    process_time = models.FloatField(default=0)
    
    # 完成时间
    finish_time = models.FloatField(default=0)
    
    # 异步任务的类型,0:资产导出,1:异步任务导出
    type = models.SmallIntegerField(default=0)
    
    # 文件路径
    file_path = models.CharField(max_length=255, blank=True, null=True)
    
    # 对应的进程id
    pid = models.IntegerField(default=0)
    
    # 处理进度 0-100
    process = models.IntegerField(default=0)
    
    # 要导出的内容
    ids = models.CharField(max_length=255, blank=True, null=True, default=None)
    
    def serialize(self):
        try:
            return {
                "id": self.id,
                "name": self.name,
                "entity": self.entity.name if self.entity else None,
                "user": self.user.name if self.user else None,
                "create_time": self.create_time,
                "status": self.status,
                "process_time": self.process_time,
                "finish_time": self.finish_time,
                "type": self.type,
                "file_path": self.file_path,
                "pid": self.pid
            }
        except Exception:
            raise Failure("序列化失败")
    
    def respond(self):
        try:
            return {
                "id": self.id,
                "person": self.user.name if self.user else None,
                "time": self.create_time,
                "state": self.status,
                "type": self.type,
                "fileurl": self.file_path,
            }
        except Exception:
            raise Failure("转换失败")
        
        
    def __str__(self):
        return self.name
            
    
    