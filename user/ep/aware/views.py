#hyx
import json
import re

from django.contrib.auth.hashers import make_password

from user.models import User
from department.models import Department,Entity
from asset.models import Asset,Alert
from logs.models import AssetLog
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils import utils_time
from utils.identity import *
from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check
import math
from rest_framework.decorators import action, throttle_classes, permission_classes, authentication_classes, api_view
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer

class AwViewSet(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    
    allowed_identity = [EP]
    
    #增加告警策略
    @Check
    @action(detail=False,methods=['post'],url_path="newaw")
    def newaw(self,req:Request):
        assetname = require(req.data, "assetname", "string" , err_msg="Error type of [assetname]")
        warning = require(req.data, "warning", "int" , err_msg="Error type of [warning]")
        condition = require(req.data, "condition", "float" , err_msg="Error type of [condition]")
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).first()
        if not asset:
            raise Failure("资产不存在")
        already_alert = Alert.objects.filter(entity=ent,department=dep,asset=asset,type=warning).first()
        if already_alert:
            raise Failure("已经存在同类告警策略")
        Alert(entity=ent,department=dep,asset=asset,type=warning,number=condition).save()
        return Response({"code":0,"info":"success"})
    
    #删除告警策略
    @Check
    @action(detail=False,methods=['delete'],url_path="deleteaw")
    def deleteaw(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        id = require(req.data, "key", "int" , err_msg="Error type of [key]")
        aware = Alert.objects.filter(id=id,entity=ent,department=dep).first()
        if not aware:
            raise Failure("告警策略不存在")
        aware.delete()
        return Response({"code":0,"info":"success"})
    
    #获取告警策略
    @Check
    @action(detail=False,methods=['get'],url_path="getw")
    def getw(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        awares = Alert.objects.filter(entity=ent,department=dep).all()
        return_list = [{"key":item.id,"assetname":item.asset.name,"warning":item.type,"condition":item.number} for item in awares]
        return Response({"code":0,"info":return_list})
    
    #更改告警策略条件
    @Check
    @action(detail=False,methods=['post'],url_path="cgcondition")
    def cgcondition(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        id = require(req.data, "key", "int" , err_msg="Error type of [key]")
        newcondition = require(req.data, "newcondition", "float" , err_msg="Error type of [newcondition]")
        aware = Alert.objects.filter(entity=ent,department=dep,id=id).first()
        if not aware:
            raise Failure("告警策略不存在")
        aware.number = newcondition
        aware.save()
        return Response({"code":0,"info":"success"})