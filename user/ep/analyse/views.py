#hyx

import json
import re

from django.contrib.auth.hashers import make_password

from user.models import User
from department.models import Department,Entity
from asset.models import Asset
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

class AsViewSet(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    
    allowed_identity = [EP]
    
    def get_departs(self,dep,deplist):
        childdeps = Department.objects.filter(parent=dep.id).all()
        if childdeps:
            for childdep in list(childdeps):
                deplist.append(childdep)
                self.get_departs(childdep,deplist)
        return deplist
    
    def preprocess(self,user):
        ent = Entity.objects.filter(id=user.entity).first()
        dep = Department.objects.filter(id=user.department).first()
        deplist = [dep]
        self.get_departs(dep,deplist)
        assets = Asset.objects.filter(entity=ent,department__in=deplist).exclude(status=4).all()
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
            elif item.status == 0:
                free += 1
            elif item.status == 1:
                occupy += 1
            elif item.status == 2:
                maintain += 1
        for item in quant_assets:
            if item.expire == True or utils_time.get_timestamp() - item.create_time > item.life * 31536000:
                expire += 1
                break
            use = json.loads(item.usage)
            maint = json.loads(item.maintain)
            process = json.loads(item.process)
            if item.number - item.number_expire == item.number_idle:
                free += 1
            if item.number_idle == 0 and not maint and not process and item.number != 0:
                occupy += 1
            elif use:
                part_occupy += 1
            if item.number_idle == 0 and not use and not process and item.number != 0:
                maintain += 1
            elif maint:
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

    #价值折旧计算
    def price_count(self,asset,timestamp):
        if asset.expire == True or timestamp - asset.create_time > asset.life * 31536000:
            return 0.00
        elif float(asset.price) * ( 1 - (timestamp - asset.create_time) / (asset.life * 31536000)) > float(asset.price):
                return round(float(asset.price),2)
        else:
            return round(float(asset.price) * ( 1 - (timestamp - asset.create_time) / (asset.life * 31536000)),2)
    
    #资产净总价值
    @Check
    @action(detail=False,methods=['get'],url_path="totalnvalue")
    def totalnvalue(self,req:Request):
        totalnetvalue = 0.00
        assets = self.preprocess(req.user)
        for item in assets:
            if item.type:
                totalnetvalue += 1.00 * item.number * self.price_count(item,utils_time.get_timestamp() - int(utils_time.get_timestamp()) % 86400)
            else:
                totalnetvalue += self.price_count(item,utils_time.get_timestamp() - int(utils_time.get_timestamp()) % 86400)
        return Response({"code":0,"info":{"totalnetvalue":round(totalnetvalue,2)}})
    
    #根据日志计算价值
    def price_log(self,day,item):
        create_time = item.expire_time
        if day < create_time:
            return float(item.price)
        if create_time - day < item.life * 31536000:
            if float(item.price) * (1 - (create_time - day) / (item.life * 31536000)) < float(item.price):
                return float(item.price) * (1 - (create_time - day) / (item.life * 31536000))
            else:
                return float(item.price)
        else:
            return 0.0
    
    #近30天内资产净值
    @Check
    @action(detail=False,methods=['get'],url_path="nvcurve")
    def nvcureve(self,req:Request):
        valuelist = []
        deletelogs = []
        addlogs = []
        today = int(utils_time.get_timestamp()) - int(utils_time.get_timestamp()) % 86400
        dep = Department.objects.filter(id=req.user.department).first()
        deps = self.get_departs(dep,[dep])
        deps = [i.id for i in deps]
        assets = self.preprocess(req.user)
        for i in range(30):
            day = today - i * 86400
            basicvalue = 0.0
            for item in assets:
                if item.type:
                    basicvalue += 1.00 * item.number * self.price_count(item,day)
                else:
                    basicvalue += self.price_count(item,day)
            deletevalue = 0.0
            addvalue = 0.0
            #添加资产，对应应当减少价值
            addlog = list(AssetLog.objects.filter(entity=req.user.entity,department__in=deps,type=1,time__gte=day+86400,time__lte=day+2 * 86400).all())
            for item in addlog:
                if item.src != None:
                    if item.src.department in deps:
                        continue
                addlogs.append(item)
            #移出，改变数量和删除，对应应当增加价值
            deletelog = list(AssetLog.objects.filter(entity=req.user.entity,department__in=deps,type__in=[7,8,9,10],time__gte=day+86400,time__lte=day+2 * 86400).all())
            for item in deletelog:
                if item.type == 7:
                    destuser = User.objects.filter(id=item.dest.id).first()
                    if destuser.department in deps:
                        continue
                deletelogs.append(item)
            for item in addlogs:
                deletevalue += self.price_log(day,item)
            for item in deletelogs:
                addvalue += self.price_log(day,item)
            value = basicvalue + addvalue - deletevalue
            valuelist.append({"date":int(day),"netvalue":round(value,2)})
        return Response({"code":0,"info":reversed(valuelist)})
    
    #获得各部门资产分布
    @Check
    @action(detail=False,methods=['get'],url_path="departasset")
    def departasset(self,req:Request):
        dep = Department.objects.filter(id=req.user.department).first()
        deps = self.get_departs(dep,[dep])
        reslist = []
        for i in deps:
            assets = Asset.objects.filter(department=i).all()
            reslist.append({"name":i.name,"number":len(assets)})
        return Response({"code":0,"info":reslist})