#hyx

import json
import re

from django.contrib.auth.hashers import make_password

from user.models import User
from department.models import Department,Entity
from asset.models import Asset
from logs.models import Logs
from pending.models import Pending
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.identity import *
from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer

class NsViewSet(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    
    allowed_identity = [EN]
    #发起代办申请
    @Check
    @action(detail=False, methods=['post'], url_path="userapply")
    def userapply(self,req:Request):
        user = req.user
        ent = Entity.objects.filter(id=user.entity).first()
        dep = Department.objects.filter(id=user.department).first()
        # print(req.data["assetapply"])
        assets = require(req.data, "assetsapply", "list" , err_msg="Error type of [assetsapply]")
        reason = require(req.data, "reason", "string" , err_msg="Error type of [reason]")
        assetdict = {}
        for item in assets:
            asset = Asset.objects.filter(entity=ent,department=dep,name=item["assetname"]).first()
            if not asset:
                raise Failure("资产%s不存在" % item["assetname"])
            if asset.id != item["id"]:
                raise Failure("资产id错误")
            if asset.category.name != item["assetclass"]:
                raise Failure("资产类别错误")
            #数量型
            if asset.type:
                targetnum = item["assetcount"]
                if targetnum > asset.number_idle:
                    raise Failure("资产%s闲置数量不足" % asset.name)
                assetdict.update({item["assetname"]:item["assetcount"]})
            #条目型
            else:
                if asset.status != 0:
                    raise Failure("资产%s未处于闲置状态" % asset.name)
                assetdict.update({item["assetname"]:1})
        #更新资产状态
        for key in assetdict:
            asset = Asset.objects.filter(entity=ent,department=dep,name=key).first()
            #数量型
            if asset.type:
                asset.number_idle -= assetdict[key]
                process = json.loads(asset.process)
                if not process:
                    asset.process = "[" + "{\"%s\":%d}" % (user.name,assetdict[key]) + "]"
                else:
                    needupdate = True
                    for term in process:
                        if user.name in term:
                            term.update({user.name:term[user.name]+item["assetcount"]})
                            needupdate = False
                            break
                    if needupdate:
                        process.append({user.name:item["assetcount"]})
                    asset.process = json.dumps(process)
            else:
                asset.status = 5
                asset.user = user
            asset.save()
        assetlist = [{key:assetdict[key]} for key in assetdict]
        pending = Pending(entity=ent.id,department=dep.id,initiator=user.id,asset=json.dumps(assetlist),type=1,description=reason)
        pending.save()
        return Response({"code":0,"info":"success"})
    
    #获取所有领用申请
    @Check
    @action(detail=False, methods=['get'], url_path="getallapply")
    def getallapply(self,req:Request):
        user = req.user
        ent = Entity.objects.filter(id=user.entity).first()
        dep = Department.objects.filter(id=user.department).first()
        if not ent :
            raise Failure("用户不属于任何业务实体")
        if not dep:
            raise Failure("用户不属于任何部门")
        pendings = Pending.objects.filter(entity=ent.id,department=dep.id,initiator=user.id,type=1).all()
        returnlist = [{"id":item.id,"reason":item.description,"status":item.result,"message":item.reply} for item in pendings]
        return Response({"code":0,"info":returnlist})

#获取所有领用涉及的资产
@Check
@api_view(['GET'])
@authentication_classes([LoginAuthentication])
@permission_classes([GeneralPermission])
def assetsinapply(req:Request,id:any):
    user = req.user
    ent = Entity.objects.filter(id=user.entity).first()
    dep = Department.objects.filter(id=user.department).first()
    if not ent :
        raise Failure("用户不属于任何业务实体")
    if not dep:
        raise Failure("用户不属于任何部门")
    pending = Pending.objects.filter(id=id).first()
    if not pending:
        raise Failure("待办项不存在")
    if pending.initiator != user.id:
        raise Failure("该申请与申请人不符")
    assets = json.loads(pending.asset)
    returnlist = []
    for item in assets:
        assetname = list(item.keys())[0]
        asset = Asset.objects.filter(department=dep,entity=ent,name=assetname).first()
        returnlist.append({"id":asset.id,"assetname":assetname,"assetcount":item[assetname]})
    return Response({"code":0,"info":returnlist})