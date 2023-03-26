import json
from django.http import HttpRequest, HttpResponse
from user.models import User
from logs.models import Logs
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
# Create your views here.

def valid_user(body):
    #获取无默认值的用户名和密码，缺失则报错
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    pwd = require(body, "password", "string", err_msg="Missing or error type of [password]")
    #用户名不得长于128个字符
    assert 0 < len(name) <= 128, "Bad length of [name]. The length should be no longer than 128."
    #密码有效性检查在前端进行，只获取加密后的md5

    #所有有默认值的属性
    entity = 0 if "entity" not in body else body["entity"]
    department = 0 if "department" not in body else body["department"]
    identity = 4 if "identity" not in body else body["identity"]
    return name,pwd,entity,department,identity

'''
@CheckRequire
def startup(req: HttpRequest):
    return HttpResponse("Start up created by Hanyx.This is backend test.")
'''

#创建用户
@CheckRequire
def create_user(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "POST":
        name,pwd,entity,department,identity = valid_user(body)
        sameuser = User.objects.filter(name=name).first()
        if sameuser:
            return request_failed(-1,"The user already exists.")
        user = User(name=name,password=pwd,entity=entity,department=department,identity=identity)
        user.save()
        return request_success({"username":name})

    else:
        return BAD_METHOD

#删除用户
@CheckRequire
def delete_user(req:HttpRequest):
    body = json.loads(req.body.decode("utf-8"))
    if req.method == "DELETE":
        id = require(body, "id", "int", err_msg="Missing or error type of [id]")
        thisuser = User.objects.filter(id=id).first()
        if thisuser:
            name = thisuser.name
            thisuser.delete()
            return request_success({"username":name})
        else:
            return request_failed(-1,"The user doesn't exist.")

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
        elif pwd != user.password:
            # case 2 : 密码错误
            return request_failed(-1,"密码错误")
        elif req.session.get(name) == True:
            # case 3 : 用户已登录
            return request_failed(-1,"此用户已在其它设备登录")
        elif user.locked:
            # case 4 : 用户被锁定
            return request_failed(-1,"此用户已被管理员封禁")
        else:
            req.session[name] = True
            req.session.set_expiry(0)
            Logs(entity=user.entity,content="用户"+user.name+"登录").save()
            return request_success({"name":name,"entity":user.entity,"department":user.department,"identity":user.identity,"lockedapp":user.lockedapp})
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
        elif req.session.get(name) == False:
            # case 2 : 用户未登录
            return request_failed(-1,"此用户尚未登录")
        else:
            req.session[name] = False
            return request_success({"session":name})
    else:
        return BAD_METHOD
