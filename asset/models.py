from utils import utils_time
from django.db import models
from utils.utils_request import return_field
from department.models import Department, Entity
from user.models import User

# Create your models here.
class Asset(models.Model):
    
    class AsserStatus(models.IntegerChoices):
        IDLE = 0
        INUSE = 1
        MAINTAIN = 2
        CLEAR = 3
        DELETE = 4
    
    #资产id，主键自增
    id = models.BigAutoField(primary_key=True)
    
    #上级资产id，可以没有上级资产
    parent = models.ForeignKey('asset.Asset', null=True, on_delete=models.SET_NULL)
    
    # 资产所属的业务实体
    # 资产必须属于某一个业务实体，实体被删除时，该实体下必须没有资产
    entity = models.ForeignKey('department.Entity', on_delete=models.PROTECT)
    
    # 资产类别
    # 资产必须属于某一个类别，类别被删除时，该类别下必须没有资产
    category = models.ForeignKey('AssetClass', on_delete=models.PROTECT) 

    # 资产所属的部门
    # 资产必须属于某一个部门，部门被删除时，该部门下必须没有资产
    department = models.ForeignKey('department.Department', on_delete=models.PROTECT)
    
    #资产名称，同一业务实体内不得重名，不同业务实体间可以
    name = models.CharField(max_length=128)
    
    #资产数量，条目型始终为1，数量型可变动
    number = models.IntegerField(default=1)
    
    #挂账人
    # 每个资产都一定要有挂账人，删除一个用户之前一定要保证这个用户下没有挂账的资产，否则这里报错: ProtectedError
    belonging = models.ForeignKey('user.User', null=False, on_delete=models.PROTECT)
    
    #资产原价值
    price = models.DecimalField(max_digits=10,decimal_places=2)
    
    #资产使用年限
    life = models.IntegerField(default=0)
    
    #资产的创建时间
    create_time = models.FloatField(default=utils_time.get_timestamp)
    
    #资产的说明和描述
    description = models.TextField(default="")
    
    #自定义的资产类型，以字符串存储，格式类似于json，实际处理需要解析
    additional = models.TextField(default="{}")
    
    #资产的状态，枚举类型，0闲置，1在使用，2维保，3清退，4删除
    status = models.IntegerField(choices=AsserStatus.choices, default=AsserStatus.IDLE)
    

    class Meta:
        db_table = "Asset"
    
    def serialize(self):
        return{
            "id":self.id,
            "parent":self.id,
            "department":self.department,
            "name":self.name,
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
    
class AssetClass(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    parent = models.ForeignKey('AssetClass', on_delete=models.CASCADE, verbose_name="父级类别")
    
    name = models.CharField(max_length=128, unique=True, verbose_name="类别名")
    
    #资产类型，False为条目型，True为数量型
    type = models.BooleanField(null=False)
    
    