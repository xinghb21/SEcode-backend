from utils import utils_time
from django.db import models
from utils.utils_request import return_field
from department.models import Department, Entity
from user.models import User
from utils.exceptions import Failure

import json

class Feishu(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    
    token_create_time = models.FloatField(default=utils_time.get_timestamp)
    
    access_token = models.TextField()
    
    access_expires_in = models.PositiveIntegerField()
    
    refresh_token = models.TextField()
    
    refresh_expires_in = models.PositiveIntegerField()
    
    name = models.TextField()
    
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
                "create_time": self.create_time,
                "access_token": self.access_token,
                "access_expires_in": self.access_expires_in,
                "refresh_token": self.refresh_token,
                "refresh_expires_in": self.refresh_expires_in,
            }
            return ret
        except Exception:
            raise Failure("序列化失败")
        
# 记录到达的事件以检测重复事件
class Event(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    event_id = models.TextField(verbose_name="事件唯一标识", unique=True)
    
    # 整数，单位为秒
    create_time = models.BigIntegerField(verbose_name="创建时间", default=utils_time.get_timestamp)

