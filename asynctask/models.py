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
    
    # 异步任务状态,0:未开始,1:进行中,2:已完成,3:已取消,4:已失败
    status = models.SmallIntegerField(default=0)
    
    # 处理时间
    process_time = models.FloatField(default=get_timestamp)
    
    # 完成时间
    finish_time = models.FloatField(default=get_timestamp)
    
    # 异步任务的类型,0:导入,1:导出
    type = models.SmallIntegerField(default=0)
    
    # 文件路径
    file_path = models.CharField(max_length=255, blank=True, null=True)
    
    def serialize(self):
        try:
            return {
                "id": self.id,
                "name": self.name,
                "entity": self.entity.name if self.entity else None,
                "user": self.user.username if self.user else None,
                "create_time": self.create_time,
                "status": self.status,
                "process_time": self.process_time,
                "finish_time": self.finish_time,
                "type": self.type,
                "file_path": self.file_path,
            }
        except Exception:
            raise Failure("序列化失败")
        
    def __str__(self):
        return self.name
            
    
    