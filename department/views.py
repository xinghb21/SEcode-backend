import json
from utils import utils_time
from django.http import HttpRequest, HttpResponse
from user.models import User
from department.models import Department,Entity
from logs.models import Logs
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from django.contrib.sessions.models import Session
from django.contrib.auth.hashers import make_password, check_password
# Create your views here.

#创建业务实体
@CheckRequire
def createEt(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "POST":
        name = require(body, "name", "string", err_msg="Missing or error type of [name]")
        ent = Entity.objects.filter(name=name).first()
        if not ent:
            entity = Entity(name=name)
            entity.save()
            return request_success({"name":name})
        else:
            return request_failed(-1,"此业务实体名称已存在")
    else:
        return BAD_METHOD

#删除业务实体
@CheckRequire
def deleteEt(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "DELETE":
        name = require(body, "name", "string", err_msg="Missing or error type of [name]")
        ent = Entity.objects.filter(name=name).first()
        if ent:
            name = ent.name
            ent.delete()
            return request_success({"name":name})
        else:
            return request_failed(-1,"此业务实体不存在")
    else:
        return BAD_METHOD

#给业务实体委派系统管理员
@CheckRequire
def assginES(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "POST":
        entname = require(body, "entity", "string", err_msg="Missing or error type of [entity]")
        username = require(body, "name", "string", err_msg="Missing or error type of [name]")
        pwd = require(body, "password", "string", err_msg="Missing or error type of [password]")
        ent = Entity.objects.filter(name=entname).first()
        user = Entity.objects.filter(name=username).first()
        if not ent:
            return request_failed(-1,"此业务实体不存在")
        if user:
            return request_failed(-1,"此用户名已存在")
        es = User(name=username,password=make_password(pwd),entity=ent.id,department=0,identity=2,lockedapp="001110000")
        es.save()
        Logs(entity = ent.id,content="创建系统管理员"+es.name,type=1).save()
        return request_success({"username":es.name})
    else:
        return BAD_METHOD