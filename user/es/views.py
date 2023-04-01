# cyh

# 企业系统管理员
import json
from utils import utils_time
from django.http import HttpRequest, HttpResponse
from user.models import User
from logs.models import Logs
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required

def check_user(req:HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    # 当前登录的用户
    logged_name = req.session.get("name")
    if not logged_name:
        return request_failed(-1, "用户未登录")
    logged_user = User.objects.filter(name=logged_name).first()
    if logged_user.identity != 2:
        return request_failed(-1, "非系统管理员操作")
    
    param = req.GET.dict()
    name = require(param, "name", err_msg="Missing or error type of [name]")
    user = User.objects.filter(name=name).first()
    if user.department == 0:
        return request_failed(-1, "该用户不属于任何部门")
    if user.department != logged_user.department:
        return request_failed(-1, "系统管理员无权查看其它业务实体的用户")
    
    field_list = ["name", "entity", "department", "locked", "identity", "lockedapp"]
    
    return return_field(user.serialize(), field_list)
    