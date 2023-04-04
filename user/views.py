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
from utils.session import SessionAuthentication
from utils.exceptions import Failure, ParamErr

from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets

def userapp(id):
    if id == 1:
        return "110000000"
    if id == 2:
        return "001110000"
    if id == 3:
        return "000001110"
    if id == 4:
        return "000000001"

def valid_user(body):
    #获取无默认值的用户名和密码，缺失则报错
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    pwd = require(body, "password", "string", err_msg="Missing or error type of [password]")
    #用户名不得长于128个字符
    if not 0 < len(name) <= 128:
        raise Failure("Bad length of [name]. The length should be no longer than 128.")
    identity = 4 if "identity" not in body else body["identity"]
    funclist = userapp(identity) if "funclist" not in body else body["funclist"]
    entity = 0
    department = 0
    #检查业务实体和部门有效性
    if identity != 1:
        entity = require(body, "entity", "string", err_msg="Missing or error type of [entity]")
        ent = Entity.objects.filter(name=entity).first()
        if not ent:
            raise Failure("业务实体不存在")
        entity = ent.id
    if identity != 1 and identity != 2:
        department = require(body, "department", "string", err_msg="Missing or error type of [department]")
        dep = Department.objects.filter(name=department).first()
        if not dep:
            raise Failure("部门不存在")
        department = dep.id
    return name,pwd,entity,department,identity,funclist


class UserViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [GeneralPermission]
    #创建用户
    @action(detail=False, methods=['POST'])
    def create_user(self, req:Request):
        name,pwd,entity,department,identity,funclist = valid_user(req.data)
        sameuser = User.objects.filter(name=name).first()
        if sameuser:
            raise Failure("此用户名已存在")
        user = User(name=name,password=make_password(pwd),entity=entity,department=department,identity=identity,lockedapp=funclist)
        user.save()
        Logs(entity = user.entity,content="创建用户"+user.name,type=1).save()
        return Response({"username":name})

    #删除用户
    @action(detail=False, methods=['DELETE'])
    def delete_user(self, req:Request):
        name = require(req.data, "name", "string", err_msg="Missing or error type of [name]")
        thisuser = User.objects.filter(name=name).first()
        if thisuser:
            name = thisuser.name
            Logs(entity = thisuser.entity,content="删除用户"+thisuser.name,type=1).save()
            thisuser.delete()
            return Response({"username":name})
        else:
            raise Failure("此用户不存在")

    #用户登录
    @action(detail=False, methods=['POST'])
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
            return Response({"name":name,"entity":user.entity,"department":user.department,"identity":user.identity,"funclist":user.lockedapp})

    #用户登出
    @action(detail=False, methods=['POST'])
    def logout(self, req:Request):
        name = require(req.data, "name", "string", err_msg="Missing or error type of [name]")
        user = User.objects.filter(name=name).first()
        if not user:
            # case 1 : 用户不存在
            raise Failure("用户" + name + "不存在")
        else:
            req._request.session[name] = False
            return Response({"name":name})

#进入用户界面
@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([GeneralPermission])
def home(req:Request,username:any):
    userName = require({"username": username}, "username", "string", err_msg="Bad param [username]")
    user = User.objects.filter(name=userName).first()
    if user and userName in req._request.session and req._request.session.get(userName):
        return_data = {
            "funclist":user.lockedapp,
            "code":0,
            "identity":user.identity,
            "username":username,
            "entity":user.entity,
            "department":user.department
        }
        return Response(return_data)
    else:
        raise Failure("用户不存在或未登录")
