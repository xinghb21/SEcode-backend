from utils import utils_time
from django.db import models
import django.utils.timezone as timezone
from utils.utils_request import return_field
from department.models import Department, Entity
from user.models import User
from utils.exceptions import Failure

import json

class Feishu(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    user = models.OneToOneField("user.User", on_delete=models.CASCADE, null=True, related_name="feishu")
    
    token_create_time = models.FloatField(default=utils_time.get_timestamp)
    
    access_token = models.TextField(default="")
    
    access_expires_in = models.PositiveIntegerField(default=0)
    
    refresh_token = models.TextField(default="")
    
    refresh_expires_in = models.PositiveIntegerField(default=0)
    
    name = models.TextField()
    
    mobile = models.TextField(default="")
    
    # 用户在企业内的唯一标识
    userid = models.TextField(default="")
    
    # 单一飞书应用内的唯一id
    openid = models.TextField(default="")
    
    # 一个飞书企业内的唯一id
    unionid = models.TextField()
    
    def serialize(self):
        try:
            ret = {
                "id": self.id,
                "user": self.user.name,
                "token_create_time": self.token_create_time,
                "access_token": self.access_token,
                "access_expires_in": self.access_expires_in,
                "refresh_token": self.refresh_token,
                "refresh_expires_in": self.refresh_expires_in,
            }
            return ret
        except Exception:
            raise Failure("序列化失败")
        
    class Meta:
        db_table = "feishu"
        
# 记录到达的事件以检测重复事件
class Event(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    eventid = models.CharField(verbose_name="事件唯一标识", max_length=255)
    
    eventtype = models.CharField(verbose_name="事件类型", max_length=255, default="")
    
    # 整数，单位为秒
    create_time = models.BigIntegerField(verbose_name="创建时间", default=utils_time.get_timestamp)
    
    # 整数，单位为秒
    create_time_format = models.CharField(verbose_name="创建时间", default=utils_time.get_time, max_length=255)
    
    class Meta:
        db_table = "Event"
    
# 记录处理事件时的异常情况
class EventException(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    event = models.OneToOneField(Event, on_delete=models.CASCADE, null=True)
    
    msg = models.TextField(verbose_name="报错信息")
    
    class Meta:
        db_table = "EventException"

