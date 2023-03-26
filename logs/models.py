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
    content = models.CharField(max_length=65535,default="")
    
    #时间戳
    time = models.BigIntegerField(default=utils_time.get_timestamp)
    
    class Meta:
        db_table = "Logs"

    def serialize(self):
        return{
            "id":self.id,
            "entity":self.entity,
            "content":self.content,
            "time":self.time
        }
