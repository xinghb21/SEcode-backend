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
    
# cyh
# 记录http请求的日志
class httpLogs(models.Model):
    #主键自增
    id = models.BigAutoField(primary_key=True)
    
    re_time = models.CharField(verbose_name="请求时间", max_length=255)
    
    re_url = models.TextField(verbose_name="请求url")
    
    re_method = models.CharField(verbose_name="请求方法", max_length=20)
    
    re_ip = models.CharField(max_length=32, verbose_name='请求IP')
    
    re_content = models.TextField(null=True, verbose_name="请求参数")
    
    rp_content = models.TextField(null=True, verbose_name="响应内容")
    
    access_time = models.FloatField(verbose_name="耗时/ms")
    
    class Meta:
        db_table = 'httpLogs'
    
# 超时请求单独记录
class accessTimeOutLogs(models.Model):
    #主键自增
    id = models.BigAutoField(primary_key=True)
    
    re_time = models.CharField(verbose_name="请求时间", max_length=255)
    
    re_url = models.TextField(verbose_name="请求url")
    
    re_method = models.CharField(verbose_name="请求方法", max_length=20)
    
    re_ip = models.CharField(max_length=32, verbose_name='请求IP')
    
    re_content = models.TextField(verbose_name="请求参数")
    
    rp_content = models.TextField(verbose_name="响应内容")
    
    access_time = models.FloatField(verbose_name="耗时/ms")
    class Meta:
        db_table = 'accessTimeOutLogs'
    
class AssetLog(models.Model):
    #主键自增
    id = models.BigAutoField(primary_key=True)
    
    #关联资产
    asset = models.ForeignKey('asset.Asset', null=True, on_delete=models.CASCADE)
    
    #操作类别,1创建(包括资产管理员创建和作为转移目标),2领用,3转移,4维保,5维保完成,6退库,7价值更改
    type = models.IntegerField(default=0)
    
    #更改的价值
    price = models.FloatField(default=0)
    
    #数量，条目型为1
    number = models.IntegerField(default=1)
    
    #源用户,转移，维保，退库操作应该存在
    src = models.ForeignKey("user.User",null=True ,on_delete=models.SET_NULL, related_name="src")
    
    #目的用户,领用,转移,维保,维保完成操作应该存在
    dest = models.ForeignKey("user.User",null=True ,on_delete=models.SET_NULL, related_name="dest")
    
    #操作完成时间
    time = models.FloatField(default=utils_time.get_timestamp)
    
    class Meta:
        db_table = "AssetLog"

    def serialize(self):
        return{
            "id":self.id,
            "asset":self.asset.name,
            "type":self.type,
            "number":self.number,
            "src":self.src.name,
            "dest":self.dest.name,
            "time":self.time
        }

