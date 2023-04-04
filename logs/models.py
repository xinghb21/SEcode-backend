from utils import utils_time
from django.db import models
from utils.utils_request import return_field

# Create your models here.
class Logs(models.Model):
    #主键自增
    id = models.BigAutoField(primary_key=True)
    
    #业务实体id，用于筛选对应系统管理员
    entity = models.BigIntegerField(default=0)
    
    #内容，手动填入
    content = models.TextField(default="{}")
    
    #时间戳
    time = models.FloatField(default=utils_time.get_timestamp)
    
    #日志类型，1人员，2部门，3资产
    type = models.IntegerField(default=1)

    class Meta:
        db_table = "Logs"

    def serialize(self):
        return{
            "id":self.id,
            "entity":self.entity,
            "content":self.content,
            "time":self.time,
            "type":self.type
        }
