from utils import utils_time
from django.db import models
from utils.utils_request import return_field

# Create your models here.

class Pending(models.Model):
    #请求的id
    id = models.BigAutoField(primary_key=True)
    
    #所属业务实体
    department = models.BigIntegerField()
    
    #申请人用户id
    initiator = models.BigIntegerField()
    
    #转移目标用户id，非转移操作则设为0
    destination = models.BigIntegerField(default=0)
    
    #目标资产id
    asset = models.BigIntegerField()
    
    #申请类型，枚举，1领用，2转移，3维保，4退库
    type = models.IntegerField(default=0)
    
    #申请人的描述信息
    description = models.CharField(max_length=1024,default="")
    
    #申请结果，0未处理，1成功，2失败
    result = models.IntegerField(default=0)
    
    #请求发起时间
    request_time = models.BigIntegerField(default=utils_time.get_timestamp)
    
    #请求处理时间
    review_time = models.BigIntegerField(default=0)

    class Meta:
        db_table = "Pending"

    def serialize(self):
        return{
            "id":self.id,
            "department":self.department,
            "initiator":self.initiator,
            "destination":self.destination,
            "asset":self.asset,
            "type":self.type,
            "description":self.description,
            "result":self.result,
            "request_time":self.request_time,
            "review_time":self.review_time
        }
