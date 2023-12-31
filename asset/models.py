from utils import utils_time
from django.db import models
from utils.utils_request import return_field
from department.models import Department, Entity
from user.models import User

import json

def gettype(type):
    if type:
        return "数量型"
    else:
        return "条目型"

# Create your models here.
class Asset(models.Model):
    
    class AsserStatus(models.IntegerChoices):
        IDLE = 0 # 闲置
        INUSE = 1 # 使用中
        MAINTAIN = 2 # 维修
        CLEAR = 3 # 清退
        DELETE = 4 # 删除 应该没用?
        PROCESS = 5 # 处理中
    
    #资产id，主键自增
    id = models.BigAutoField(primary_key=True)
    
    #上级资产，可以没有上级资产
    parent = models.ForeignKey('Asset', null=True, on_delete=models.SET_NULL)
    
    # 资产所属的部门
    department = models.ForeignKey('department.Department', null=True, on_delete=models.CASCADE)
    
    # 资产所属的业务实体
    entity = models.ForeignKey('department.Entity', null=True, on_delete=models.CASCADE)
    
    # 资产类别
    # 资产必须属于某一个类别，类别被删除时，该类别下资产均被删除
    category = models.ForeignKey('AssetClass', null=True, on_delete=models.CASCADE) 
    
    # True为数量型，False为条目型
    type = models.BooleanField(null=True)
    
    #资产名称，同一部门内不得重名，不同部门，业务实体间间可以
    name = models.CharField(max_length=128)
    
    #挂账人
    # 每个资产都一定要有挂账人，删除一个用户之前一定要保证这个用户下没有挂账的资产，否则这里报错: ProtectedError
    belonging = models.ForeignKey('user.User', null=True, on_delete=models.CASCADE, related_name="belonging")
    
    #资产原价值
    price = models.DecimalField(max_digits=10,decimal_places=2,default=1000.00)
    
    #资产使用年限
    life = models.IntegerField(default=0)
    
    #资产的创建时间
    create_time = models.FloatField(default=utils_time.get_timestamp)
    
    #资产价值更新时间
    renew_time =  models.FloatField(default=utils_time.get_timestamp,null=True)

    #资产的说明和描述
    description = models.TextField(default="")
    
    #html格式补充说明
    additionalinfo = models.TextField(default="")
    
    #自定义的资产类型，以字符串存储，格式类似于json，实际处理需要解析
    additional = models.TextField(default="{}")
    
    # -----------条目型资产使用------------
    # 资产使用者
    user = models.ForeignKey("user.User",null=True ,on_delete=models.SET_NULL, related_name="user")
    
    #资产的状态，枚举类型，0闲置，1在使用，2维保，3清退，4转移或清退变空(区分于删除), 5处理中
    status = models.IntegerField(choices=AsserStatus.choices, default=AsserStatus.IDLE)
    # -----------------------------------
    
    # ----------数量型资产使用-------------
    # 资产数量
    number = models.IntegerField(null=True,default=1)
    
    # 闲置数量
    number_idle = models.IntegerField(null=True)
    
    # 使用情况，是一个可序列化的字符串，记录了谁在使用，使用多少
    usage = models.TextField(null=False, default="[]")
    
    # 维保情况，是一个可序列化的字符串，记录了谁是维保责任人，维保多少
    maintain = models.TextField(null=False, default="[]")
    
    # 待处理情况，是一个可序列化的字符串，记录了谁是发起人，待处理多少
    process = models.TextField(null=False, default="[]")
    
    # 报废数量
    number_expire = models.IntegerField(null=False, default=0)
    
    # 是否完全报废
    expire = models.BooleanField(null=False, default=False)
    # ---------数量型资产使用----------------
    
    #有无图片
    haspic = models.BooleanField(default=False)

    class Meta:
        db_table = "Asset"
    
    def serialize(self):
        ret = {
                "id":self.id,
                "parent":self.parent.name if self.parent else "",
                "department":self.department.name,
                "entity": self.entity.name,
                "category": self.category.name if self.category else "",
                "type": self.type,
                "name":self.name,
                "belonging":self.belonging.name if self.belonging else "",
                "price":float(self.price),
                "new_price":round(float(self.price) * (1 - (utils_time.get_timestamp() - self.create_time) / (self.life * 31536000)),2) if float(self.price) * (1 - (utils_time.get_timestamp() - self.create_time) / (self.life * 31536000)) < float(self.price) else float(self.price),
                "life":self.life,
                "create_time":self.create_time,
                "description":self.description,
                "additionalinfo":self.additionalinfo,
                "additional": json.loads(self.additional),
                "haspic":self.haspic
            }
        if self.type:
            ret["number"] = self.number
            ret["number_idle"] = self.number_idle
            ret["usage"] = json.loads(self.usage)
            ret["maintain"] = json.loads(self.maintain)
            ret["process"] = json.loads(self.process)
            ret["number_expire"] = self.number_expire
            ret["expire"] = self.expire
            return ret
        else:
            ret["user"] = self.user.name if self.user else None
            ret["status"] = self.status
            ret["number"] = 1
            ret["number_idle"] = 0 if self.status else 1
            ret["number_expire"] = 1 if self.expire else 0
            return ret
    
    def is_expire(self):
        return utils_time.get_timestamp() - self.create_time > self.life * 31536000

    def __str__(self) -> str:
        return self.name
    
class AssetClass(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    parent = models.ForeignKey('AssetClass', null=True, on_delete=models.CASCADE, verbose_name="父级类别")
    
    entity = models.ForeignKey('department.Entity', null=True, on_delete=models.CASCADE, verbose_name="所属业务实体")
    
    department = models.ForeignKey('department.Department', null=True, on_delete=models.CASCADE, verbose_name="所属部门")
    
    # 同一业务实体，同一部门内不允许重名
    name = models.CharField(max_length=128, verbose_name="类别名")
    
    #资产类型，False为条目型，True为数量型
    type = models.BooleanField(null=False, default=False)

#告警策略
class Alert(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    entity = models.ForeignKey('department.Entity', null=True, on_delete=models.CASCADE, verbose_name="所属业务实体")
    
    department = models.ForeignKey('department.Department', null=True, on_delete=models.CASCADE, verbose_name="所属部门")
    
    asset = models.ForeignKey('Asset', null=True, on_delete=models.CASCADE)
    
    #0按年限告警，1按数量告警
    type = models.IntegerField(default=0)
    
    #具体数值
    number = models.FloatField(default=0)