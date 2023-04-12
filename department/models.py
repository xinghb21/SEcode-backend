from utils import utils_time
from django.db import models
from utils.utils_request import return_field

# Create your models here.
class Entity(models.Model):
    #业务实体id，主键自增
    id = models.BigAutoField(primary_key=True)
    
    #业务实体名称，需要唯一化
    name = models.CharField(max_length=128,unique=True)
    
    #业务实体的系统管理员id，未创建为0
    admin = models.BigIntegerField(default=0)

    class Meta:
        db_table = "Entity"

    def serialize(self):
        return{
            "id":self.id,
            "name":self.name,
            "admin":self.admin
        }

    def __str__(self) -> str:
        return self.name

class Department(models.Model):
    #部门id，主键自增
    id = models.BigAutoField(primary_key=True)
    
    #部门名称，同一业务实体内不得重名，不同业务实体的部门间可以
    name = models.CharField(max_length=128)
    
    #部门所属实体id
    entity = models.BigIntegerField()
    
    #上一级部门id，根节点为0
    parent = models.BigIntegerField(default=0)
    
    #部门的资产管理员id
    admin = models.BigIntegerField(default=0)
    
    #用户自定义的资产标签项目，只有资产管理员可以使用,以逗号隔开
    label = models.TextField(default="")
    
    #所有自定义资产属性的json
    attributes = models.TextField(default="{}")

    class Meta:
        db_table = "Department"

    def serialize(self):
        return{
            "id":self.id,
            "name":self.name,
            "entity":self.entity,
            "parent":self.parent,
            "admin":self.admin,
            "label":self.label
        }

    def __str__(self) -> str:
        return self.name