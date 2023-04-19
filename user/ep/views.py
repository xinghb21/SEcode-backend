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
from utils import utils_time
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer

class EpViewSet(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    
    allowed_identity = [EP]
    #获取所有未处理的审批项目
    @Check
    @action(detail=False, methods=['get'], url_path="getallapply")
    def getallapply(self,req:Request):
        dep = req.user.department
        ent = req.user.entity
        pendings = Pending.objects.filter(entity=ent,department=dep,result=0).all()
        returnList = []
        for item in pendings:
            user = User.objects.filter(id=item.initiator).first()
            username = user.name if user else ""
            returnList.append({"id":item.id,"name":username,"reason":item.description,"oper":item.type})
        return Response({"code":0,"info":returnList})
    
    #资产管理员审批请求
    @Check
    @action(detail=False, methods=['post'], url_path="reapply")
    def reapply(self,req:Request):
        ent = req.user.entity
        dep = req.user.department
        id = require(req.data, "id", "int" , err_msg="Error type of [id]")
        status = require(req.data, "status", "int" , err_msg="Error type of [status]")
        reply = require(req.data, "reason", "string" , err_msg="Error type of [reason]")
        pen = Pending.objects.filter(entity=ent,department=dep,id=id).first()
        if not pen:
            raise Failure("待办项不存在")
        ptype = pen.type
        staff = User.objects.filter(entity=ent,department=dep,id=pen.initiator).first()
        assets = json.loads(pen.asset)
        if pen.result:
            raise Failure("此待办已审批完成")
        #更新待办信息
        #检查所有资产是否都存在
        for assetdict in assets:
            assetname = list(assetdict.keys())[0]
            asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).first()
            if not asset and status == 0:
                raise Failure("请求中包含已失效资产，请拒绝")
        assetlist = assets
        pen.result = 2 if status else 1
        pen.review_time = utils_time.get_timestamp()
        pen.reply = reply
        pen.save()
        #更新资产信息
        #领用
        if ptype == 1:
            #该待办中的所有资产项目
            for assetdict in assetlist:
                assetname = list(assetdict.keys())[0]
                #待办单条资产
                asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).first()
                if not asset:continue
                #数量型
                if asset.type:
                    #本资产的所有预备条目
                    pro = json.loads(asset.process)
                    #资产待审批数量减少
                    for i in pro:
                        if list(i.keys())[0] == staff.name:
                            if assetdict[assetname] < i[staff.name]:
                                i[staff.name] -= assetdict[assetname]
                            else:
                                pro.remove(i)
                            break
                    asset.process = json.dumps(pro)
                    #同意，更新usage
                    if status == 0:
                        use = json.loads(asset.usage)
                        if not use:
                            asset.usage = json.dumps([{staff.name:assetdict[assetname]}])
                        else:
                            needupdate = True
                            for term in use:
                                if staff.name in term:
                                    term.update({staff.name:term[staff.name] + assetdict[assetname]})
                                    needupdate = False
                                    break
                            if needupdate:
                                use.append({staff.name:assetdict[assetname]})
                            asset.usage = json.dumps(use)
                    #不同意，更新闲置
                    else:
                        asset.number_idle += assetdict[assetname]
                #条目型
                else:
                    #同意，状态置为1，设置使用者
                    if status == 0:
                        asset.status = 1
                        asset.user = staff
                    else:
                        asset.status = 0
                asset.save()
        #TODO if ptype == 2:
        #TODO if ptype == 3:
        #TODO if ptype == 4:
        return Response({"code":0,"detail":"ok"})
    
    @Check
    @action(detail=False, methods=['get'], url_path="assetsinapply")
    def assetsinapply(self,req:Request):
        id = req.query_params['id']
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
        assets = json.loads(pending.asset)
        returnlist = []
        for item in assets:
            assetname = list(item.keys())[0]
            asset = Asset.objects.filter(department=dep,entity=ent,name=assetname).first()
            returnlist.append({"id":asset.id,"assetname":assetname,"assetclass":asset.category.name,"assetcount":item[assetname]})
        return Response({"code":0,"info":returnlist})
    
    @Check
    @action(detail=False, methods=['get'], url_path="istbd")
    def istbd(self,req:Request):
        ent = req.user.entity
        dep = req.user.department
        pendings = Pending.objects.filter(entity=ent,department=dep,result=0).first()
        if pendings:
            return Response({"code":0,"info":True})
        else:
            return Response({"code":0,"info":False})
