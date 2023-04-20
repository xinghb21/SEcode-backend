# cyh
import json
import re
import time
import requests
import hashlib

from django.contrib.auth.hashers import make_password, check_password

from user.models import User
from department.models import Department, Entity
from logs.models import Logs
from asset.models import Asset, AssetClass

from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.identity import *
from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import authentication_classes as auth
from rest_framework.decorators import action, throttle_classes, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
from rest_framework.views import APIView
from utils.decipher import AESCipher

from feishu.models import Feishu
from feishu.events import dispatch_event

ENCRYPT_KEY = "uJHwvC9MR6OL2m2gonsWadkVBdrqF1tN"
APP_ID = "cli_a4b17e84d0f8900e"
APP_SECRET = "bMrD4Rtx85VS0jiPhPgThdrohZTHR4Jo"
VERIFICATION_TOKEN = "AOKjmM7RLNEw9pPck9zyNcF7KvshqL4F"

class feishu(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = []
    allowed_identity = []
    
    decipher = AESCipher(ENCRYPT_KEY)
    
    @Check
    @action(detail=False, methods=['post'], url_path="answer")
    def answer_event(self, req:Request):
        if 'X-Lark-Request-Timestamp' in req._request.headers.keys() and 'X-Lark-Request-Nonce' in req._request.headers.keys() and 'X-Lark-Signature' in req._request.headers.keys():
            bytes_b1 = (req._request.headers['X-Lark-Request-Timestamp'] + req._request.headers['X-Lark-Request-Nonce'] + ENCRYPT_KEY).encode('utf-8')
            bytes_b = bytes_b1 + req._request.body
            h = hashlib.sha256(bytes_b)
            signature = h.hexdigest()
            if signature != req._request.headers['X-Lark-Signature']:
                raise Failure("签名校验有误, 事件被拒绝处理")
        if "challenge" in req.data.keys():
            return Response({"challenge": req.data["challenge"]})
        if "encrypt" in req.data.keys():
            body = self.decipher.decrypt_string(req.data['encrypt'])
            try:
                body: dict = json.loads(body)
            except:
                raise Failure("解密后信息非json格式")
            if "schema" in body:
                token = body["header"]["token"]
            else:
                token = body["token"]
            if token != VERIFICATION_TOKEN:
                raise Failure("token校验有误, 事件被拒绝处理")
            if "challenge" in body.keys():
                return Response({"challenge": body["challenge"]})
            dispatch_event(body)
            return Response({
                "code": 0,
                "detail": "successfully handled",
            })
    
    # 通过授权码获得该飞书用户的token和个人信息，在后端保存
    @Check
    @action(detail=False, methods=['get'], url_path="code")
    def process_code(self, req:Request):
        code = require(req.query_params, "code", err_msg="Missing or Error type of [code]")
        redirect = require(req.query_params, "redirect", err_msg="Missing or Error type of [redirect]")
        body = {
            "grant_type": "authorization_code",
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "code": code,
            "redirect_uri": redirect,
        }
        resp = requests.post("https://passport.feishu.cn/suite/passport/oauth/token", 
                             body, 
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
        if resp.status_code != 200:
            raise Failure("请求token失败，授权码可能失效")
        resp = resp.json()
        access_token = resp['access_token']
        userinfo = requests.get("https://passport.feishu.cn/suite/passport/oauth/userinfo",
                                headers={"Authorization": "Bearer " + access_token})
        if userinfo.status_code != 200:
            raise Failure("获取用户信息失败")
        userinfo = userinfo.json()
        union_id = userinfo['union_id']
        fs = Feishu.objects.filter(union_id=union_id).first()
        if not fs:
            # 创建一个没有绑定帐号的飞书用户
            feishu = Feishu.objects.create(user=None, access_token=access_token, 
                                  access_expires_in=resp['expires_in'],
                                  refresh_token=resp['refresh_token'],
                                  refresh_expires_in=resp['refresh_expires_in'],
                                  name=userinfo['name'],
                                  open_id=userinfo['open_id'],
                                  union_id=union_id)
            # 在当前会话中保存该飞书用户
            req._request.session['feishu_id'] = feishu.id
            return Response({
                "code": 0,
                "detail": "success",
            })
        # 在当前会话中保存该飞书用户
        req._request.session['feishu_id'] = fs.id
        # 该飞书用户已经存在于数据库中，则更新token
        fs.token_create_time = get_timestamp()
        fs.access_token = access_token
        fs.access_expires_in=resp['expires_in']
        fs.refresh_token=resp['refresh_token']
        fs.refresh_expires_in=resp['refresh_expires_in']
        fs.save()
        return Response({
            "code": 0,
            "detail": "success",
        })

    # 通过授权码判断该飞书用户是否已经绑定了帐号
    @Check
    @action(detail=False, methods=['get'], url_path="isbound")
    def check_is_bound(self, req:Request):
        try:
            feishu_id = req._request.session["feishu_id"]
        except Exception:
            raise Failure("无飞书用户登录")
        fs = Feishu.objects.filter(id=feishu_id).first()
        if not fs:
            raise Failure("登录的飞书用户不存在于数据库中")
        if not fs.user:
            return Response({
                "code": 0,
                "isbound": False,
            })
        return Response({
            "code": 0,
            "isbound": True,
            "name": fs.user.name,
        })
        
    # 通过飞书绑定的帐号登录
    @Check
    @action(detail=False, methods=['post'], url_path="login")
    def login(self, req:Request):
        try:
            feishu_id = req._request.session["feishu_id"]
        except Exception:
            raise Failure("该飞书用户未登录")
        name = require(req.data, "name", err_msg="Missing or Error type of [name]")
        fs = Feishu.objects.filter(id=feishu_id).first()
        if not fs.user:
            raise Failure("该飞书用户未绑定帐号")
        if name != fs.user.name:
            raise Failure("登录的帐号不是该飞书用户绑定的帐号")
        if fs.user.locked:
            raise Failure("该帐号已被系统管理员封禁")
        req._request.session["id"] = fs.user.id
        req._request.session[fs.user.name] = True
        return Response({
            "code": 0,
            "detail": "success",
        })
        
    # 绑定系统中的帐号
    @Check
    @action(detail=False, methods=['post'], url_path="binduser")
    def binduser(self, req: Request):
        try:
            feishu_id = req._request.session["feishu_id"]
        except Exception:
            raise Failure("该飞书用户未登录")
        fs = Feishu.objects.filter(id=feishu_id).first()
        if not fs:
            raise Failure("飞书用户不存在")
        if fs.user:
            raise Failure("该飞书用户已经绑定了用户")
        name = require(req.data, "name", err_msg="Missing or Error type of [name]")
        pw = require(req.data, "password", err_msg="Missing or Error type of [password]")
        user = User.objects.filter(name=name).first()
        if not user:
            raise Failure("所绑定的用户不存在")
        if not check_password(pw, user.password):
            raise Failure("密码错误")
        if user.locked:
            raise Failure("此用户已被管理员封禁")
        fs.user = user
        fs.save()
        return Response({
            "code": 0,
            "detail": "success",
        })
        
    # 绑定飞书帐号
    @Check
    @action(detail=False, methods=['post'], url_path="bind")
    def bind(self, req: Request):
        pass
        
    
    # 解除绑定
    @Check
    @action(detail=False, methods=['delete'], url_path="unbind")
    def unbind(self, req: Request):
        pass
        
        
        
            
