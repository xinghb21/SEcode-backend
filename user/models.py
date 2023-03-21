from utils import utils_time
from django.db import models
from utils.utils_request import return_field

from utils.utils_require import MAX_CHAR_LENGTH
from django.contrib.auth.hashers import make_password, check_password
# Create your models here.

# 用户信息的数据库
class User(models.Model):
    #用户id,主键自增
    id = models.BigAutoField(primary_key=True)
    
    #用户名称，需要唯一化
    name = models.CharField(max_length=128,unique=True)
    
    #用户密码，在实际存储时需要调用make_password哈希加密
    password = models.CharField(max_length=65536)
    
    #所属业务实体的id，默认值为0
    entity = models.BigIntegerField(default=0)
    
    #所属部门的id，默认值为0
    department = models.BigIntegerField(default=0)
    
    #是否为超级管理员
    system_super = models.BooleanField(default=False)
    
    #是否为系统管理员
    entity_super = models.BooleanField(default=False)
    
    #是否为资产管理员
    asset_super = models.BooleanField(default=False)
    
    #用户是否已登录
    on_log = models.BooleanField(default=False)
    
    #用户是否被锁定，只有既非超级管理员又非系统管理员的用户可被锁定
    locked = models.BooleanField(default=False)

    class Meta:
        db_table = "User"

    def serialize(self):
        return{
            "id":self.id,
            "name":self.name,
            "password":self.password,
            "entity":self.entity,
            "department":self.department,
            "system_super":self.system_super,
            "entity_super":self.entity_super,
            "asset_super":self.asset_super,
            "on_log":self.on_log,
            "locked":self.locked
        }

    def __str__(self) -> str:
        return self.name
