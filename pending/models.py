from utils import utils_time
from django.db import models
from utils.utils_request import return_field

# Create your models here.

class Pending(models.Model):
    #请求的id
    id = models.BigAutoField(primary_key=True)
    
    #所属业务实体
    entity = models.BigIntegerField(default=0)
    
    #所属部门
    department = models.BigIntegerField(default=0)
    
    #申请人用户id
    initiator = models.BigIntegerField(default=0)
    
    #转移目标用户id，非转移操作则设为0
    destination = models.BigIntegerField(default=0)
    
    #目标资产名称和数量列表
    asset = models.TextField(default="[]")
    
    #申请类型，枚举，0已审批，1领用，2转移，3维保，4退库
    type = models.IntegerField(default=0)
    
    #申请人的描述信息
    description = models.CharField(max_length=100,default="")
    
    #处理人的回复
    reply = models.CharField(max_length=100,default="")
    
    #申请结果，0未处理，1成功，2失败
    result = models.IntegerField(default=0)
    
    #请求发起时间
    request_time = models.FloatField(default=utils_time.get_timestamp)
    
    #请求处理时间
    review_time = models.FloatField(default=0)

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
            "reply":self.reply,
            "result":self.result,
            "request_time":self.request_time,
            "review_time":self.review_time
        }
