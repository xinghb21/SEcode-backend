# cyh

# 企业系统管理员
import json
from utils import utils_time
from django.http import HttpRequest, HttpResponse
from user.models import User
from logs.models import Logs
from department.models import Entity,Department
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
    if not user:
        return request_failed(-1, "被查询的用户不存在")
    if user.department == 0:
        return request_failed(-1, "该用户不属于任何部门")
    if user.department != logged_user.department:
        return request_failed(-1, "系统管理员无权查看其它业务实体的用户")
    
    field_list = ["name", "entity", "department", "locked", "identity", "lockedapp"]
    
    return return_field(user.serialize(), field_list)
    
#hyx
def depart_tree(id,parent):
    roots = Department.objects.filter(entity=id,parent=parent).all()
    if not roots:
        return "$"
    else:
        res = {}
        for root in roots:
            res.update({root.name:depart_tree(root.id)})
        return res

#返回该系统管理员对应业务实体的部门树
def check_depart(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "GET":
        name = require(body, "name", "string", err_msg="Missing or error type of [name]")
        es = User.objects.filter(name=name).first()
        if not es or es.identity != 2:
            return request_failed(-1,"该用户不存在或不是系统管理员")
        ent = Entity.objects.filter(admin=es.id).first()
        if not ent:
            return request_failed(-1,"业务实体不存在")
        tree = depart_tree(ent.id,0)
        return request_success({"info":tree})
    else:
        return BAD_METHOD