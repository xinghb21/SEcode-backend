#hyx

import json
import re

from django.contrib.auth.hashers import make_password

from user.models import User
from department.models import Department,Entity
from asset.models import Asset
from logs.models import Logs
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils import utils_time
from utils.identity import *
from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import action, throttle_classes, permission_classes, authentication_classes, api_view
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer

class AsViewSet(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    
    allowed_identity = [EP]
    
    def preprocess(self,user):
        ent = Entity.objects.filter(id=user.entity).first()
        dep = Department.objects.filter(id=user.department).first()
        assets = Asset.objects.filter(entity=ent,department=dep).all()
        return assets
    
    #资产总数量
    @Check
    @action(detail=False,methods=['get'],url_path="atotal")
    def atotal(self,req:Request):
        assets = self.preprocess(req.user)
        quant_assets = assets.filter(type=True).all()
        entry_assets = assets.filter(type=False).all()
        total = 0
        for item in list(quant_assets):
            total += item.number
        return Response({"code":0,"info":{"entryNumber":len(entry_assets),"quantTypeNumber":len(quant_assets),"quantTotalNumber":total}})
    
    #资产类别分布
    @Check
    @action(detail=False,methods=['get'],url_path="astatotal")
    def astatotal(self,req:Request):
        assets = self.preprocess(req.user)
        entry_assets = assets.filter(type=False).all()
        quant_assets = assets.filter(type=True).all()
        #全部闲置
        free = 0
        #全部占用
        occupy = 0
        #部分占用
        part_occupy = 0
        #全部维保
        maintain = 0
        #部分维保
        part_maintain = 0
        #需要清退
        expire = 0
        for item in entry_assets:
            if item.expire == True or utils_time.get_timestamp() - item.create_time > item.life * 31536000:
                expire += 1
                break
            if item.status == 0:
                free += 1
            if item.status == 1:
                occupy += 1
            if item.status == 2:
                maintain += 1
        for item in quant_assets:
            if item.expire == True or utils_time.get_timestamp() - item.create_time > item.life * 31536000:
                expire += 1
                break
            use = json.loads(item.usage)
            maint = json.loads(item.maintain)
            process = json.loads(item.process)
            if item.number == item.number_idle:
                free += 1
            if item.number_idle == 0 and not maint and not process:
                occupy += 1
            if use:
                part_occupy += 1
            if item.number_idle == 0 and not use and not process:
                maintain += 1
            if maint:
                part_maintain += 1
        info = {
            "freeNumber":free,
            "totccupyNumber":occupy,
            "partccupyNumber":part_occupy,
            "totfixNumber":maintain,
            "partfixNumber":part_maintain,
            "tbfixNumber":expire
        }
        return Response({"code":0,"info":info})
