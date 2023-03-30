import json
from utils import utils_time
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpRequest, HttpResponse
from user.models import User
from logs.models import Logs
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from django.contrib.sessions.models import Session
# Create your views here.

'''
@CheckRequire
def start(req: HttpRequest):
    return HttpResponse("Start!")
'''


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
    assert 0 < len(name) <= 128, "Bad length of [name]. The length should be no longer than 128."
    identity = 4 if "identity" not in body else body["identity"]
    funclist = userapp(identity)
    entity = 0
    department = 0
    #检查业务实体和部门有效性
    if identity != 1:
        entity = require(body, "entity", "string", err_msg="Missing or error type of [entity]")
    if identity != 1 and identity != 2:
        identity = require(body, "department", "string", err_msg="Missing or error type of [department]")
    return name,pwd,entity,department,identity,funclist

#创建用户
@CheckRequire
def create_user(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "POST":
        name,pwd,entity,department,identity,funclist = valid_user(body)
        sameuser = User.objects.filter(name=name).first()
        if sameuser:
            return request_failed(-1,"此用户名已存在")
        user = User(name=name,password=make_password(pwd),entity=entity,department=department,identity=identity,lockedapp=funclist)
        user.save()
        Logs(entity = user.entity,content="创建用户"+user.name,type=1).save()
        return request_success({"username":name})

    else:
        return BAD_METHOD

#删除用户
@CheckRequire
def delete_user(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "DELETE":
        name = require(body, "name", "string", err_msg="Missing or error type of [name]")
        thisuser = User.objects.filter(name=name).first()
        if thisuser:
            name = thisuser.name
            Logs(entity = thisuser.entity,content="删除用户"+thisuser.name,type=1).save()
            thisuser.delete()
            return request_success({"username":name})
        else:
            return request_failed(-1,"此用户不存在")

    else:
        return BAD_METHOD

#用户登录
@CheckRequire
def login(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    pwd = require(body, "password", "string", err_msg="Missing or error type of [password]")
    user = User.objects.filter(name=name).first()
    if req.method == "POST":
        if not user:
            # case 1 : 用户不存在
            return request_failed(-1,"用户不存在")
        elif not check_password(pwd,user.password):
            # case 2 : 密码错误
            return request_failed(-1,"密码错误")
        elif user.locked:
            # case 3 : 用户被锁定
            return request_failed(-1,"此用户已被管理员封禁")
        else:
            req.session[name] = True
            Logs(entity=user.entity,content="用户"+user.name+"登录",type=1).save()
            return request_success({"name":name,"entity":user.entity,"department":user.department,"identity":user.identity,"funclist":user.lockedapp})
    else:
        return BAD_METHOD

#用户登出
@CheckRequire
def logout(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    user = User.objects.filter(name=name).first()
    if req.method == "POST":
        if not user:
            # case 1 : 用户不存在
            return request_failed(-1,"用户" + name + "不存在")
        else:
            req.session[name] = False
            return request_success({"name":name})
    else:
        return BAD_METHOD

#进入用户界面
@CheckRequire
def home(req:HttpRequest,username:any):
    userName = require({"username": username}, "username", "string", err_msg="Bad param [username]", err_code=-1)
    if req.method == "GET":
        user = User.objects.filter(name=userName).first()
        if user and userName in req.session and req.session.get(userName):
            return_data = {
                "funclist":user.lockedapp,
                "code":0,
                "identity":user.identity,
                "username":username,
                "entity":user.entity,
                "department":user.department
            }
            return request_success(return_data)
        else:
            return request_failed(1,"用户不存在或未登录")
    else:
        return BAD_METHOD
