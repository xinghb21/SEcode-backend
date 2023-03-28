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

'''
#给业务实体委派系统管理员
@CheckRequire
def assginES(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "PUT":
        entname = require(body, "entity", "string", err_msg="Missing or error type of [entity]")
        oldname = require(body, "old", "string", err_msg="Missing or error type of [old]")
        newname = require(body, "new", "string", err_msg="Missing or error type of [new]")
        ent = Entity.objects.filter(name=entname).first()
        old = Entity.objects.filter(name=oldname).first()
        new = Entity.objects.filter(name=newname).first()
        if not ent:
            return request_failed(-1,"此业务实体不存在")
        elif not new:
            return request_failed(-1,"用户"+newname+"不存在")
        else:
            if oldname == "":
                ent.admin = new.id
                ent.save()
                return request_success({"info":new + "成为了" + ent +"的系统管理员"})
            else:
                if not old:
                    return request_failed(-1,"用户"+oldname+"不存在")
                elif new == old:
                    return request_failed(-1,"更改前后为同一用户")
                else:
                    ent.admin = new.id
                    ent.save()
    else:
        return BAD_METHOD
'''