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
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.request import Request

# Create your views here.
#hanyx
#创建业务实体
@CheckRequire
def createEt(req:HttpRequest):
    super = User.objects.filter(identity=1).first()
    if not super:
        return request_failed(-1,"此用户不存在")
    if super.name not in req.session or not req.session.get(super.name):
        return request_failed(-1,"此用户不是系统超级管理员或未登录,无权查看")
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

#删除单个业务实体
def singleDelete(ent):
    crew = User.objects.filter(entity=ent.id).all()
    #需要删除名下所有人员、部门和资产
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

#删除单个业务实体
@CheckRequire
def deleteEt(req:HttpRequest):
    super = User.objects.filter(identity=1).first()
    if not super:
        return request_failed(-1,"此用户不存在")
    if super.name not in req.session or not req.session.get(super.name):
        return request_failed(-1,"此用户不是系统超级管理员或未登录,无权查看")
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "DELETE":
        name = require(body, "name", "string", err_msg="Missing or error type of [name]")
        ent = Entity.objects.filter(name=name).first()
        if ent:
            singleDelete(ent)
            return request_success({"name":name})
        else:
            return request_failed(-1,"此业务实体不存在")
    else:
        return BAD_METHOD

#批量删除业务实体
@CheckRequire
def deleteAllEt(req:HttpRequest):
    super = User.objects.filter(identity=1).first()
    if not super:
        return request_failed(-1,"此用户不存在")
    if super.name not in req.session or not req.session.get(super.name):
        return request_failed(-1,"此用户不是系统超级管理员或未登录,无权查看")
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "DELETE":
        names = require(body, "name", "string", err_msg="Missing or error type of [name]")
        names = names[1:len(names)-1:1].replace('\'','').replace('\"','').replace(" ","").split(',')
        for name in names:
            ent = Entity.objects.filter(name=name).first()
            if ent:
                print(ent.name)
                singleDelete(ent)
                return request_success()
            else:
                return request_failed(-1,"业务实体"+name+"不存在")
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

#删除单个业务实体的管理员
def deleteSingleES(ent):
    es = User.objects.filter(id=ent.admin).first()
    name = es.name
    es.delete()
    ent.admin = 0
    ent.save()
    Logs(entity = ent.id,content="删除系统管理员"+name,type=1).save()

#删除单个业务实体管理员
@CheckRequire
def deleteES(req:HttpRequest):
    super = User.objects.filter(identity=1).first()
    if not super:
        return request_failed(-1,"此用户不存在")
    if super.name not in req.session or not req.session.get(super.name):
        return request_failed(-1,"此用户不是系统超级管理员或未登录,无权查看")
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "DELETE":
        entname = require(body, "entity", "string", err_msg="Missing or error type of [entity]")
        ent = Entity.objects.filter(name=entname).first()
        if not ent:
            return request_failed(-1,"此业务实体不存在")
        if ent.admin == 0:
            return request_failed(-1,"此业务实体无系统管理员")
        name = User.objects.filter(id=ent.admin).first().name
        deleteSingleES(ent)
        return request_success({"username":name})
    else:
        return BAD_METHOD

#批量删除业务实体管理员
@CheckRequire
def deleteAllES(req:HttpRequest):
    super = User.objects.filter(identity=1).first()
    if not super:
        return request_failed(-1,"此用户不存在")
    if super.name not in req.session or not req.session.get(super.name):
        return request_failed(-1,"此用户不是系统超级管理员或未登录,无权查看")
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "DELETE":
        names = require(body, "entity", "string", err_msg="Missing or error type of [name]")
        entnames = names[1:len(names)-1:1].replace('\'','').replace('\"','').replace(" ","").split(',')
        print(entnames)
        for entname in entnames:
            ent = Entity.objects.filter(name=entname).first()
            if not ent:
                return request_failed(-1,"此业务实体"+entname+"不存在")
            if ent.admin == 0:
                return request_failed(-1,"此业务实体"+entname+"无系统管理员")
            name = User.objects.filter(id=ent.admin).first().name
            deleteSingleES(ent)
            return request_success()
    else:
        return BAD_METHOD

#获取业务实体所有信息
@CheckRequire
def getEt(req:HttpRequest):
    if req.method == "GET":
        super = User.objects.filter(identity=1).first()
        if not super:
            return request_failed(-1,"此用户不存在")
        if super.name not in req.session or not req.session.get(super.name):
            return request_failed(-1,"此用户不是系统超级管理员或未登录,无权查看")
        entlist = Entity.objects.all()
        return_list = []
        if entlist:
            for i in entlist:
                es = User.objects.filter(id=i.admin).first()
                esname = "" if not es else es.name
                return_list.append({"id":i.id,"name":i.name,"admin":esname})
        return request_success({"data":return_list})
    else:
        return BAD_METHOD

# cyh
# 返回所有部门
@Check
@api_view(['GET'])
@authentication_classes([LoginAuthentication])
def getAllDep(req:Request):
    if req.user.identity != 2:
        raise PermissionError
    et = req.user.entity
    dep = Department.objects.filter(entity=et)
    data = [d.name for d in dep]
    return Response({
        "code": 0,
        "data": data,
    })
