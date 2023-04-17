# cyh
import json
import re
import time
import requests

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

from rest_framework.decorators import action, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
from rest_framework.views import APIView
from utils.decipher import AESCipher
from feishu.models import Feishu

ENCRYPT_KEY = "uJHwvC9MR6OL2m2gonsWadkVBdrqF1tN"
APP_ID = "cli_a4b17e84d0f8900e"
APP_SECRET = "bMrD4Rtx85VS0jiPhPgThdrohZTHR4Jo"

class feishu(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = []
    allowed_identity = []
    
    decipher = AESCipher(ENCRYPT_KEY)
    
    @Check
    @action(detail=False, methods=['post'], url_path="answer")
    def answer_challenge(self, req:Request):
        challenge = self.decipher.decrypt_string(req.data['encrypt'])
        print(challenge)
        challenge = json.loads(challenge)
        print(challenge)
        return Response({"challenge": challenge["challenge"]})
    
    # 通过授权码判断该飞书用户是否已经绑定了帐号
    @Check
    @action(detail=False, methods=['get'], url_name="isbound")
    def check_is_bound(self, req:Request):
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
                                  access_expires_in=resp['access_expires_in'],
                                  refresh_token=resp['refresh_token'],
                                  refresh_expires_in=resp['refresh_expires_in'],
                                  name=userinfo['name'],
                                  open_id=userinfo['open_id'],
                                  union_id=union_id)
            # 在当前会话中保存该飞书用户
            req._request.session['feishu_id'] = feishu.id
            return Response({
                "code": 0,
                "isbound": False,
            })
        req._request.session['feishu_id'] = fs.id
        if not fs.user:
            return Response({
                "code": 0,
                "isbound": False,
            })
        # 绑定了帐号，则更新token
        fs.token_create_time = get_timestamp()
        fs.access_token = access_token
        fs.access_expires_in=resp['access_expires_in']
        fs.refresh_token=resp['refresh_token']
        fs.refresh_expires_in=resp['refresh_expires_in']
        fs.save()
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
        return Response({
            "code": 0,
            "detail": "success",
        })
        
    # 绑定帐号
    @Check
    def post(self, req: Request):
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
        # 将绑定的帐号设置为登录状态
        req._request.session['id'] = fs.user.id
        return Response({
            "code": 0,
            "detail": "success",
        })
    
    # 
    # @Check
    # def delete(self, req: Request):
        
        
            
