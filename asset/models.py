from utils import utils_time
from django.db import models
from utils.utils_request import return_field

# Create your models here.
class Asset(models.Model):
    #资产id，主键自增
    id = models.BigAutoField(primary_key=True)
    
    #上级资产id，根节点为0
    parent = models.BigIntegerField(default=0)

    #资产所属的部门id
    department = models.BigIntegerField()
    
    #资产名称，同一业务实体内不得重名，不同业务实体间可以
    name = models.CharField(max_length=100)
    
    #资产类型，False为条目型，True为数量型
    type = models.BooleanField(default=False)
    
    #资产数量，条目型始终为1，数量型可变动
    number = models.IntegerField(default=1)
    
    #挂账人的用户id
    belonging = models.BigIntegerField()
    
    #资产原价值
    price = models.DecimalField(max_digits=10,decimal_places=2)
    
    #资产使用年限
    life = models.IntegerField(default=0)
    
    #资产的创建时间
    create_time = models.BigIntegerField(default=utils_time.get_timestamp)
    
    #资产的说明和描述
    description = models.TextField(default="")
    
    #自定义的资产类型，以字符串存储，格式类似于json，实际处理需要解析
    additional = models.TextField(default="{}")
    
    #资产的状态，枚举类型，0闲置，1在使用，2维保，3清退，4删除
    status = models.IntegerField(default=0)
    

    class Meta:
        db_table = "Asset"
    
    def serialize(self):
        return{
            "id":self.id,
            "parent":self.id,
            "department":self.department,
            "name":self.name,
            "type":self.type,
            "number":self.number,
            "belonging":self.belonging,
            "price":self.price,
            "life":self.life,
            "create_time":self.create_time,
            "description":self.description,
            "additional":self.additional,
            "status":self.status
        }

    def __str__(self) -> str:
        return self.name