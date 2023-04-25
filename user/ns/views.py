#hyx

import json
import re

from django.contrib.auth.hashers import make_password
from django import db

from user.models import User
from department.models import Department,Entity
from asset.models import Asset,AssetClass
from logs.models import Logs
from pending.models import Pending,Message
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

from feishu.event.info import applySubmit

class NsViewSet(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    
    allowed_identity = [EN]
    
    #员工名下资产列表
    def staffassets(self,name):
        user = User.objects.filter(name=name).first()
        ent = Entity.objects.filter(id=user.entity).first()
        dep = Department.objects.filter(id=user.department).first()
        asset_item = Asset.objects.filter(entity=ent,department=dep,type=False,user=user).all()
        asset_num_all = Asset.objects.filter(entity=ent,department=dep,type=True).all()
        return_list = [{"id":i.id,"name":i.name,"type":0,"number":1} for i in asset_item]
        for i in asset_num_all:
            users = json.loads(i.usage)
            for dict in users:
                if user.name in list(dict.keys())[0]:
                    return_list.append({"id":i.id,"name":i.name,"type":1,"number":dict[user.name]})
        return return_list

    #转移,维保和退库的有效检查
    def valid_asset(self,assets,username):
        assetlist = []
        #错误检查
        for assetdict in assets:
            id = assetdict["id"]
            name = assetdict["assetname"]
            number = assetdict["assetnumber"]
            asset = Asset.objects.filter(id=id).first()
            if not asset or asset.name != name:
                raise Failure("资产信息错误")
            if asset.type:
                numbers = json.loads(asset.usage)
                possess = False
                for i in numbers:
                    if list(i.keys())[0] == username:
                        possess = True
                        if i[username] < number:
                            raise Failure("资产数量错误")
                if not possess:
                    raise Failure("资产不属于该用户")
            else:
                if asset.user.name != username:
                    raise Failure("资产不属于该用户")
            assetlist.append({name:number})
        return assetlist
    
    #转移，维保和退库的资产状态改变
    def asset_in_process(self,assets,username):
        for assetdict in assets:
            id = assetdict["id"]
            number = assetdict["assetnumber"]
            asset = Asset.objects.filter(id=id).first()
            #数量型
            if asset.type:
                using = json.loads(asset.usage)
                for term in using:
                    if list(term.keys())[0] == username:
                        if term[username] == number:
                            using.remove(term)
                        else:
                            term[username] -= number
                        break
                asset.usage = json.dumps(using)
                process = json.loads(asset.process)
                if not process:
                    asset.process = json.dumps([{username:number}])
                else:
                    needupdate = True
                    for term in process:
                        if username in term:
                            term.update({username:term[username]+number})
                            needupdate = False
                            break
                    if needupdate:
                        process.append({username:number})
                    asset.process = json.dumps(process)
            #条目型
            else:
                asset.status = 5
            asset.save()
    
    #获取所有申请
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
        pendings = Pending.objects.filter(entity=ent.id,department=dep.id,initiator=user.id).all()
        returnlist = [{"id":item.id,"reason":item.description,"status":item.result,"message":item.reply,"type":item.type} for item in pendings]
        return Response({"code":0,"info":returnlist})

    #申请资产领用
    @Check
    @action(detail=False, methods=['post'], url_path="userapply")
    def userapply(self,req:Request):
        user = req.user
        ent = Entity.objects.filter(id=user.entity).first()
        dep = Department.objects.filter(id=user.department).first()
        assets = require(req.data, "assetsapply", "list" , err_msg="Error type of [assetsapply]")
        reason = require(req.data, "reason", "string" , err_msg="Error type of [reason]")
        assetdict = {}
        for item in assets:
            asset = Asset.objects.filter(entity=ent,department=dep,name=item["assetname"]).first()
            if not asset:
                raise Failure("资产%s不存在" % item["assetname"])
            if asset.id != item["id"]:
                raise Failure("资产id错误")
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
                    asset.process = json.dumps([{user.name:assetdict[key]}])
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
            asset.save()
        assetlist = [{key:assetdict[key]} for key in assetdict]
        pending = Pending(entity=ent.id,department=dep.id,initiator=user.id,asset=json.dumps(assetlist),type=1,description=reason)
        pending.save()
        # cyh
        # 消息同步
        db.close_old_connections()
        newprocess = applySubmit(req.user, req.data)
        newprocess.start()
        # cyh
        return Response({"code":0,"info":"success"})

    #申请资产转移
    @Check
    @action(detail=False, methods=['post'], url_path="exchange")
    def exchange(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        fromdep = Department.objects.filter(id=req.user.department).first()
        assets = require(req.data, "exchange", "list" , err_msg="Error type of [exchange]")
        reason = require(req.data, "reason", "string" , err_msg="Error type of [reason]")
        username = require(req.data, "username", "string" , err_msg="Error type of [username]")
        dest = User.objects.filter(entity=req.user.entity,name=username).first()
        if not dest:
            raise Failure("目标用户不存在")
        if dest.identity != 4:
            raise Failure("目标用户不是员工")
        todep = Department.objects.filter(id=dest.department).first()
        if not todep:
            raise Failure("目标部门不存在")
        assetlist = self.valid_asset(assets,req.user.name)
        #如果跨部门，检查目标部门是否有重名资产
        if fromdep != todep:
            for asset in assetlist:
                assetname = list(asset.keys())[0]
                sameasset = Asset.objects.filter(entity=ent,department=todep,name=assetname).first()
                if sameasset:
                    raise Failure("资产%s在目标用户所在部门存在同名资产" % assetname)
        self.asset_in_process(assets,req.user.name)
        pending = Pending(entity=ent.id,department=fromdep.id,initiator=req.user.id,destination=dest.id,asset=json.dumps(assetlist),type=2,description=reason)
        pending.save()
        return Response({"code":0,"info":"success"})

    #申请资产维保
    @Check
    @action(detail=False, methods=['post'], url_path="applymainten")
    def applymainten(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        assets = require(req.data, "assets", "list" , err_msg="Error type of [assets]")
        reason = require(req.data, "reason", "string" , err_msg="Error type of [reason]")
        #错误检查
        assetlist = self.valid_asset(assets,req.user.name)
        self.asset_in_process(assets,req.user.name)
        pending = Pending(entity=ent.id,department=dep.id,initiator=req.user.id,asset=json.dumps(assetlist),type=3,description=reason)
        pending.save()
        return Response({"code":0,"info":"success"})
    
    #申请资产退库
    @Check
    @action(detail=False, methods=['post'], url_path="returnasset")
    def returnasset(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        assets = require(req.data, "assets", "list" , err_msg="Error type of [assets]")
        reason = require(req.data, "reason", "string" , err_msg="Error type of [reason]")
        #错误检查
        assetlist = self.valid_asset(assets,req.user.name)
        self.asset_in_process(assets,req.user.name)
        pending = Pending(entity=ent.id,department=dep.id,initiator=req.user.id,asset=json.dumps(assetlist),type=4,description=reason)
        pending.save()
        return Response({"code":0,"info":"success"})
    
    #查看员工自己名下的所有资产
    @Check
    @action(detail=False,methods=['get'],url_path="possess")
    def possess(self,req:Request):
        list = self.staffassets(req.user.name)
        return Response({"code":0,"assets":list})

    #获取申请中涉及的的资产
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
        dest = User.objects.filter(id=pending.destination).first()
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
        return Response({"code":0,"info":returnlist,"user":dest.name}) if dest else Response({"code":0,"info":returnlist,"user":""})
    
    #查看所有处于闲置状态的资产
    @Check
    @action(detail=False, methods=['get'], url_path="getassets")
    def getassets(self,req:Request):
        user = req.user
        ent = Entity.objects.filter(id=user.entity).first()
        dep = Department.objects.filter(id=user.department).first()
        if not ent :
            raise Failure("用户不属于任何业务实体")
        if not dep:
            raise Failure("用户不属于任何部门")
        assets_num = Asset.objects.filter(entity=ent,department=dep,type=True).exclude(number_idle=0).all()
        assets_item = Asset.objects.filter(entity=ent,department=dep,type=False,status=0).all()
        returnlist = []
        for asset in assets_num:
            returnlist.append({"id":asset.id,"name":asset.name,"type":1,"count":asset.number_idle})
        for asset in assets_item:
            returnlist.append({"id":asset.id,"name":asset.name,"type":0,"count":1})
        return Response({"code":0,"info":returnlist})
    
    #删除已经被处理的申请
    @Check
    @action(detail=False,methods=["delete"], url_path="deleteapplys")
    def deleteapplys(self,req:Request):
        user = req.user
        id = require(req.data, "id", "int" , err_msg="Error type of [id]")
        pending_to_del = Pending.objects.filter(id=id).first()
        if not pending_to_del or pending_to_del.initiator != user.id:
            raise Failure("申请不存在")
        if pending_to_del.result == 0:
            raise Failure("不能删除资产管理员未处理的申请")
        pending_to_del.delete()
        return Response({"code":0,"info":"ok"})
    
    #员工获取自己所有信息
    @Check
    @action(detail=False,methods=["get"], url_path="getmessage")
    def getmessage(self,req:Request):
        user = req.user
        msgs = Message.objects.filter(user=user.id).order_by('read','-time')
        msglist = []
        for msg in msgs:
            pending = Pending.objects.filter(id=msg.pending).first()
            assets = [list(item.keys())[0] for item in json.loads(pending.asset)]
            msglist.append({"id":msg.id,"type":msg.type,"assetname":assets,"status":pending.result,"message":msg.content})
        return Response({"code":0,"info":msglist})
    
    #员工是否存在未读信息
    @Check
    @action(detail=False,methods=["get"], url_path="hasmessage")
    def hasmessage(self,req:Request):
        user = req.user
        msg = Message.objects.filter(user=user.id,read=False).first()
        if msg:
            return Response({"code":0,"info":True})
        else:
            return Response({"code":0,"info":False})
    
    #员工信息已读,不设置报错信息
    @Check
    @action(detail=False,methods=["post"], url_path="read")
    def read(self,req:Request):
        id = require(req.data, "id", "int" , err_msg="Error type of [id]")
        msg = Message.objects.filter(user=req.user.id,id=id).first()
        if msg:
            msg.read = True
            msg.save()
        return Response({"code":0,"info":"ok"})
    
    #跨部门获得转移资产的员工指定类型
    @Check
    @action(detail=False,methods=["post"], url_path="exchange")
    def exchange(self,req:Request):
        assetname = require(req.data, "assetname", "string" , err_msg="Error type of [assetname]")
        label = require(req.data, "label", "string" , err_msg="Error type of [label]")
        dep = Department.objects.filter(id=req.user.department).first()
        ent = Entity.objects.filter(id=req.user.entity).first()
        asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).first()
        assetclass = AssetClass.objects.filter(entity=ent,department=dep,name=label).first()
        if not asset:
            raise Failure("资产不存在")
        if not assetclass:
            raise Failure("资产类别不存在")
        if asset.type != assetclass.type:
            raise Failure("资产与资产类别类型不符")
        asset.category = assetclass
        asset.save()
        return Response({"code":0,"info":"success"})
