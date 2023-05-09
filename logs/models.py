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
    
    re_content = models.TextField(null=True, verbose_name="请求参数")
    
    rp_content = models.TextField(null=True, verbose_name="响应内容")
    
    access_time = models.FloatField(verbose_name="耗时/ms")
    class Meta:
        db_table = 'accessTimeOutLogs'
    
    
