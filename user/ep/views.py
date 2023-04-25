#hyx

import json
import re

from django.contrib.auth.hashers import make_password

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
    
    #对于转移、维保、退库的拒绝
    def reject(self,assetlist,username):
        user = User.objects.filter(name=username).first()
        for assetdict in assetlist:
            assetname = list(assetdict.keys())[0]
            #待办单条资产
            asset = Asset.objects.filter(entity=user.entity,department=user.department,name=assetname).first()
            #数量型
            if asset.type:
                use = json.loads(asset.usage)
                if not use:
                    asset.usage = json.dumps([{username:assetdict[assetname]}])
                else:
                    needupdate = True
                    for term in use:
                        if username in term:
                            term.update({username:term[username] + assetdict[assetname]})
                            needupdate = False
                            break
                    if needupdate:
                        use.append({username:assetdict[assetname]})
                    asset.usage = json.dumps(use)
            #条目型
            else:
                asset.status = 1
            asset.save()
    
    #产生消息
    def create_message(self,result,pending_id,type,reply):
        operate = ""
        if type == 1:
            operate = "资产领用"
        elif type == 2:
            operate = "资产转移"
        elif type == 3:
            operate = "资产维保"
        else:
            operate = "资产退库"
        if result == False:
            return "您编号为%d的%s请求已通过审批" % (pending_id,operate)
        else:
            return "您编号为%d的%s请求未通过审批,拒绝理由:%s" % (pending_id,operate,reply)
    
    #资产管理员审批请求
    @Check
    @action(detail=False, methods=['post'], url_path="reapply")
    def reapply(self,req:Request):
        ent = req.user.entity
        entity = Entity.objects.filter(id=ent).first()
        dep = req.user.department
        depart = Department.objects.filter(id=dep).first()
        id = require(req.data, "id", "int" , err_msg="Error type of [id]")
        status = require(req.data, "status", "int" , err_msg="Error type of [status]")
        reply = require(req.data, "reason", "string" , err_msg="Error type of [reason]")
        pen = Pending.objects.filter(entity=ent,department=dep,id=id).first()
        #检查待办项合法
        if not pen:
            raise Failure("待办项不存在")
        ptype = pen.type
        staff = User.objects.filter(entity=ent,department=dep,id=pen.initiator).first()
        assets = json.loads(pen.asset)
        if pen.result:
            raise Failure("此待办已审批完成")
        #检查所有资产是否都存在
        for assetdict in assets:
            assetname = list(assetdict.keys())[0]
            asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).first()
            if not asset and status == 0:
                raise Failure("请求中包含已失效资产，请拒绝")
        assetlist = assets
        #更新待办信息
        pen.result = 2 if status else 1
        pen.review_time = utils_time.get_timestamp()
        pen.reply = reply
        pen.save()
        #给员工发送消息
        msg = self.create_message(status,id,ptype,reply)
        Message.objects.create(user=pen.initiator,content=msg,type=ptype,pending=id)
        #更新资产信息
        #资产领用，与其他三类差异较大
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
                        asset.belonging = staff
                    else:
                        asset.status = 0
                asset.save()
        #资产转移
        if ptype == 2:
            #拒绝
            if status == 1:
                self.reject(assetlist,staff.name)
                return Response({"code":0,"detail":"ok"})
            destuser = User.objects.filter(id=pen.destination).first()
            destdep = Department.objects.filter(id=destuser.department).first()
            for assetdict in assetlist:
                assetname = list(assetdict.keys())[0]
                #待办单条资产
                asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).first()
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
                    #跨部门
                    if destdep != depart:
                        asset.number -= assetdict[assetname]
                        destlist = [{destuser.name:assetdict[assetname]}]
                        Asset.objects.create(entity=entity,department=destdep,name=assetname,type=1,belonging=destuser,price=asset.price,life=asset.life,description=asset.description,additional=asset.additional,number=assetdict[assetname],number_idle=0,usage=json.dumps(destlist))
                    #同部门
                    else:
                        use = json.loads(asset.usage)
                        if not use:
                            asset.usage = json.dumps([{destuser.name:assetdict[assetname]}])
                        else:
                            needupdate = True
                            for term in use:
                                if destuser.name in term:
                                    term.update({destuser.name:term[destuser.name] + assetdict[assetname]})
                                    needupdate = False
                                    break
                            if needupdate:
                                use.append({destuser.name:assetdict[assetname]})
                            asset.usage = json.dumps(use)
                    asset.save()
                #条目型
                else:
                    #跨部门
                    if destdep != depart:
                        Asset.objects.create(entity=entity,department=destdep,type=0,name=assetname,price=asset.price,life=asset.life,description=asset.description,additional=asset.additional,belonging=destuser,user=destuser,status=1)
                        asset.delete()
                    #同部门
                    else:
                        asset.belonging = destuser
                        asset.user = destuser
                        asset.status = 1
                        asset.save()
            #跨部门还需要向接受方发起类型确认的消息
            if destdep != depart:
                pd = Pending(entity=ent,department=destdep.id,initiator=pen.initiator,destination=pen.destination,asset=pen.asset,type=5)
                pd.save()
                Message.objects.create(user=pen.destination,type=5,pending=pd.id,content="请为转移资产选择类别")
        #资产维保
        if ptype == 3:
            #拒绝
            if status == 1:
                self.reject(assetlist,staff.name)
                return Response({"code":0,"detail":"ok"})
            for assetdict in assetlist:
                assetname = list(assetdict.keys())[0]
                #待办单条资产
                asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).first()
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
                    maintain = json.loads(asset.maintain)
                    if not maintain:
                        asset.maintain = json.dumps([{staff.name:assetdict[assetname]}])
                    else:
                        needupdate = True
                        for term in maintain:
                            if staff.name in term:
                                term.update({staff.name:term[staff.name] + assetdict[assetname]})
                                needupdate = False
                                break
                        if needupdate:
                            maintain.append({staff.name:assetdict[assetname]})
                        asset.maintain = json.dumps(maintain)
                else:
                    asset.status = 2
                asset.save()
        #资产退库
        if ptype == 4:
            #拒绝
            admin = User.objects.filter(id=depart.admin).first()
            if status == 1:
                self.reject(assetlist,staff.name)
                return Response({"code":0,"detail":"ok"})
            for assetdict in assetlist:
                assetname = list(assetdict.keys())[0]
                #待办单条资产
                asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).first()
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
                    asset.number_idle += assetdict[assetname]
                else:
                    asset.status = 0
                    asset.user = None
                    asset.belonging = admin
                asset.save()
        return Response({"code":0,"detail":"ok"})
    
    #查看待办项中所有资产信息
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
    
    #是否有未审批的代办项目
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
        
    #资产清退名单
    @Check
    @action(detail=False, methods=['get'], url_path="assetstbc")
    def assetstbc(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        broken_assets = Asset.objects.filter(entity=ent,department=dep,expire=True).all()
        find_old_assets = Asset.objects.filter(entity=ent,department=dep,expire=False).all()
        old_assets = []
        for item in find_old_assets:
            if utils_time.get_timestamp() - item.create_time > item.life * 31536000:
                old_assets.append(item)
        return_list = []
        for i in broken_assets:
            return_list.append({"id":i.id,"assetname":i.name,"assetclass":i.category.name,"department":dep.name,"number":i.number if i.type else 1})
        for i in old_assets:
            return_list.append({"id":i.id,"assetname":i.name,"assetclass":i.category.name,"department":dep.name,"number":i.number if i.type else 1})
        return Response({"code":0,"info":return_list})
    
    #清退资产
    @Check
    @action(detail=False, methods=['post'], url_path="assetclear")
    def assetclear(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        assetnames = require(req.data, "name", "list" , err_msg="Error type of [name]")
        assets = [Asset.objects.filter(id=id,entity=ent,department=dep,name=assetname).first() for assetname in assetnames]
        for asset in assets:
            if not asset:
                raise Failure("资产不存在")
            if not (utils_time.get_timestamp() - asset.create_time > asset.life * 31536000 or asset.expire):
                raise Failure("资产尚未报废或达到年限")
        for asset in assets:
            asset.delete()
        return Response({"code":0,"info":"success"})
    
    def getparse(self,body, key, tp):
        if key not in body.keys():
            return ""
        val = body[key]
        err_msg = f"Invalid parameters. Expected `{key}` to be `{tp}` type."
        if tp == "int":
            try:
                val = int(val)
                return val
            except:
                raise Failure(err_msg)
        elif tp == "float":
            try:
                val = float(val)
                return val
            except:
                raise Failure(err_msg)
        elif tp == "string":
            try:
                val = str(val)
                return val
            except:
                raise Failure(err_msg)
    
    #条件查询资产
    @Check
    @action(detail=False, methods=['get','post'], url_path="queryasset")
    def queryasset(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        parent = self.getparse(req.data,"parent","string")
        assetclass = self.getparse(req.data,"assetclass","string")
        name = self.getparse(req.data,"name","string")
        belonging = self.getparse(req.data,"belonging","string")
        time_from = self.getparse(req.data,"from","float")
        time_to = self.getparse(req.data,"to","float")
        user = self.getparse(req.data,"user","string")
        status = self.getparse(req.data,"status","int")
        price_from = self.getparse(req.data,"pricefrom","float")
        price_to = self.getparse(req.data,"priceto","float")
        id = self.getparse(req.data,"id","int")
        custom = self.getparse(req.data,"custom","string")
        content = self.getparse(req.data,"content","string")
        if content and not custom:
            raise Failure("请先选择属性")
        assets = Asset.objects.filter(entity=ent,department=dep).all()
        if parent:
            parentasset = Asset.objects.filter(entity=ent,department=dep,name=parent).first()
            assets = assets.filter(parent=parentasset).all()
        if assetclass:
            cat = AssetClass.objects.filter(entity=ent,department=dep,name=assetclass).first()
            assets = assets.filter(category=cat).all()
        if name:
            assets = assets.filter(name=name).all()
        if belonging:
            belong_user = User.objects.filter(name=belonging).first()
            assets = assets.filter(belonging=belong_user).all()
        if id:
            assets = assets.filter(id=id).all()
        if time_from:
            assets = assets.filter(create_time__gte=time_from).all()
        if time_to:
            assets = assets.filter(create_time__lte=time_to).all()
        if price_from:
            assets = assets.filter(price__gte=price_from).all()
        if price_to:
            assets = assets.filter(price__lte=price_to).all()
        return_list = list(assets)
        assets = list(assets)
        if user:
            for item in assets:
                if item.type:
                    have = False
                    usage = json.loads(item.usage)
                    for assetdict in usage:
                        if list(assetdict.keys())[0] == user:
                            have = True
                            break
                    if not have:
                        return_list.remove(item)
                else:
                    if not item.user or item.user.name != user:
                        return_list.remove(item)
            assets = list(return_list)
        if status >= 0:
            for item in assets:
                flag = False
                if item.type:
                    if status == 0 and item.number_idle == item.number: 
                        flag = True
                    if status == 1 and item.number_idle == 0:
                        maintain = json.loads(item.maintain)
                        process = json.loads(item.process)
                        if not (maintain or process): 
                            flag = True
                    if status == 2 and item.number_idle == 0:
                        using = json.loads(item.usage)
                        process = json.loads(item.process)
                        if not (using or process): 
                            flag = True
                    if status == 3 and (item.expire or utils_time.get_timestamp() - item.create_time > item.life * 31536000):
                        flag = True
                    if status == 4:
                        using = json.loads(item.usage)
                        if using:
                            flag = True
                    if status == 5:
                        maintain = json.loads(item.maintain)
                        if maintain:
                            flag = True
                else:
                    if item.status == status and status != 5:
                        flag = True
                if not flag:
                    return_list.remove(item)
            assets = list(return_list)
        if custom:
            for item in assets:
                add = json.loads(item.additional)
                flag = False
                if custom in add:
                    if not content:
                        flag = True
                    else:
                        if add[custom] == content:
                            flag = True
                if not flag:
                    return_list.remove(item)
        return Response({"code":0,"data":[{"name":item.name,"key":item.id,"description":item.description,"assetclass":item.category.name,"type":item.type}for item in return_list]})
        
