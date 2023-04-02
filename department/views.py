import json
from utils import utils_time
from django.http import HttpRequest, HttpResponse
from user.models import User
from department.models import Department,Entity
from asset.models import Asset
from logs.models import Logs
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from django.contrib.sessions.models import Session
from django.contrib.auth.hashers import make_password, check_password
import hashlib
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
            #需要删除名下所有部门、人员、资产
            name = ent.name
            crew = User.objects.filter(entity=ent.id).all()
            if crew:
                for indiv in crew:
                    indiv.delete()
            departs = Department.objects.filter(entity=ent.id).all()
            if departs:
                for depart in departs:
                    assets = Asset.objects.filter(department=depart.id).all()
                    if assets:
                        for asset in assets:
                            asset.delete()
                    depart.delete()
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
        ent.admin = es.id
        ent.save()
        return request_success({"username":es.name})
    else:
        return BAD_METHOD

#删除现有业务实体管理员
@CheckRequire
def deleteES(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "DELETE":
        entname = require(body, "entity", "string", err_msg="Missing or error type of [entity]")
        ent = Entity.objects.filter(name=entname).first()
        if not ent:
            return request_failed(-1,"此业务实体不存在")
        if ent.admin == 0:
            return request_failed(-1,"此业务实体无系统管理员")
        es = User.objects.filter(id=ent.admin).first()
        name = es.name
        es.delete()
        ent.admin = 0
        ent.save()
        Logs(entity = ent.id,content="删除系统管理员"+name,type=1).save()
        return request_success({"username":name})
    else:
        return BAD_METHOD

#获取业务实体所有信息
@CheckRequire
def getEt(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    reqname = require(body, "username", "string", err_msg="Missing or error type of [username]")
    if req.method == "GET":
        super = User.objects.filter(identity=1).first()
        m = hashlib.md5()
        m.update(super.name.encode(encoding='utf-8'))
        if m.hexdigest() != reqname:
            return request_failed(-1,"此用户不是系统超级管理员,无权查看")
        entlist = Entity.objects.all()
        return_list = []
        if entlist:
            for i in entlist:
                return_list.append({"id":i.id,"name":i.name,"admin":i.admin})
        return request_success({"data":return_list})
    else:
        return BAD_METHOD


