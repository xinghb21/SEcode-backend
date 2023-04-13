import json
from utils import utils_time
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpRequest, HttpResponse
from django.contrib.sessions.models import Session

from user.models import User
from logs.models import Logs
from department.models import Entity,Department
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets

def userapp(id):
    if id == 1 or id == "1":
        return "110000000"
    elif id == 2 or id == "2":
        return "001110000"
    elif id == 3 or id == "3":
        return "000001110"
    elif id == 4 or id == "4":
        return "000000001"
    else:
        raise Failure("Invalid identity")

def valid_user(body):
    #获取无默认值的用户名和密码，缺失则报错
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    pwd = require(body, "password", "string", err_msg="Missing or error type of [password]")
    if not name or " " in name:
        raise Failure("姓名不可为空或有空格")
    if not pwd or " " in pwd:
        raise Failure("密码不可为空或有空格")
    #用户名不得长于128个字符
    if not 0 < len(name) <= 128:
        raise Failure("Bad length of [name]. The length should be no longer than 128.")
    identity = 4 if "identity" not in body else body["identity"]
    funclist = userapp(identity) if "funclist" not in body else body["funclist"]
    identity = int(identity)
    entity = 0
    department = 0
    #检查业务实体和部门有效性
    if identity == 2:
        entity = require(body, "entity", "string", err_msg="Missing or error type of [entity]")
        ent = Entity.objects.filter(name=entity).first()
        if not ent:
            raise Failure("业务实体不存在")
        if ent.admin != 0:
            raise Failure("该业务实体已经有系统管理员")
        entity = ent.id
    if identity == 3 or identity == 4:
        entity = require(body, "entity", "string", err_msg="Missing or error type of [entity]")
        department = require(body, "department", "string", err_msg="Missing or error type of [department]")
        dep = Department.objects.filter(name=department).first()
        ent= Entity.objects.filter(name=entity).first()
        ent= Entity.objects.filter(name=entity).first()
        if not dep:
            raise Failure("部门不存在")
        department = dep.id
        entity = ent.id
    return name,pwd,entity,department,identity,funclist


class UserViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = []
    #创建用户
    @Check
    @action(detail=False, methods=['post'])
    def createuser(self, req:Request):
        name,pwd,entity,department,identity,funclist = valid_user(req.data)
        sameuser = User.objects.filter(name=name).first()
        if sameuser:
            raise Failure("此用户名已存在")
        if identity == 3:
            dep = Department.objects.filter(id=department).first()
            if dep and dep.admin != 0:
                raise Failure("此部门资产管理员已存在")
        user = User(name=name,password=make_password(pwd),entity=entity,department=department,identity=identity,lockedapp=funclist)
        user.save()
        if identity == 3:
            dep=Department.objects.filter(id=department).first()
            if dep:
                dep.admin=user.id
                dep.save()
        Logs(entity = user.entity,content="创建用户"+user.name,type=1).save()
        return Response({"code":0,"username":name})

    #删除用户
    @Check
    @action(detail=False, methods=['delete'])
    def deleteuser(self, req:Request):
        name = require(req.data, "name", "string", err_msg="Missing or error type of [name]")
        thisuser = User.objects.filter(name=name).first()
        if thisuser:
            name = thisuser.name
            Logs(entity = thisuser.entity,content="删除用户"+thisuser.name,type=1).save()
            thisuser.delete()
            return Response({"code":0,"username":name})
        else:
            raise Failure("此用户不存在")

    #用户登录
    @Check
    @action(detail=False, methods=['post'], authentication_classes=[])
    def login(self, req:Request):
        name = require(req.data, "name", "string", err_msg="Missing or error type of [name]")
        pwd = require(req.data, "password", "string", err_msg="Missing or error type of [password]")
        user = User.objects.filter(name=name).first()
        if not user:
            # case 1 : 用户不存在
            raise Failure("用户不存在")
        elif not check_password(pwd,user.password):
            # case 2 : 密码错误
            raise Failure("密码错误")
        elif user.locked:
            # case 3 : 用户被锁定
            raise Failure("此用户已被管理员封禁")
        else:
            req._request.session[name] = True
            # cyh
            req._request.session["id"] = user.id
            # cyh
            Logs(entity=user.entity,content="用户"+user.name+"登录",type=1).save()
            return Response({"code":0,"name":name,"entity":user.entity,"department":user.department,"identity":user.identity,"funclist":user.lockedapp})

    #用户登出
    @Check
    @action(detail=False, methods=['post'])
    def logout(self, req:Request):
        name = require(req.data, "name", "string", err_msg="Missing or error type of [name]")
        user = User.objects.filter(name=name).first()
        if not user:
            # case 1 : 用户不存在
            raise Failure("用户不存在")
        else:
            req._request.session[name] = False
            return Response({"code":0,"name":name})

#进入用户界面
@Check
@api_view(['GET'])
@authentication_classes([LoginAuthentication])
@permission_classes([GeneralPermission])
def home(req:Request,username:any):
    userName = require({"username": username}, "username", "string", err_msg="Bad param [username]")
    user = User.objects.filter(name=userName).first()
    if user and userName in req._request.session and req._request.session.get(userName):
        ent = Entity.objects.filter(id=user.entity).first()
        entname = "" if not ent else ent.name
        depart = Department.objects.filter(id=user.department).first()
        departname = "" if not depart else depart.name
        return_data = {
            "funclist":user.lockedapp,
            "code":0,
            "identity":user.identity,
            "username":username,
            "entity":entname,
            "department":departname
        }
        return Response(return_data)
    else:
        raise Failure("用户不存在或未登录")

#获取当前登录的用户名
@Check
@api_view(['GET'])
@authentication_classes([LoginAuthentication])
@permission_classes([GeneralPermission])
def name(req:Request):
    if "id" not in req._request.session:
        raise Failure("无用户登录")
    user = User.objects.filter(id=req._request.session.get("id")).first()
    return Response({"code":0,"name":user.name})


