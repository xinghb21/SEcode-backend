#hyx

import json
import re

from django.contrib.auth.hashers import make_password
from django import db

from user.models import User
from department.models import Department,Entity
from asset.models import Asset,AssetClass,Alert
from logs.models import AssetLog
from pending.models import Pending,Message,EPMessage
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

from feishu.event.info import applyOutcome

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
        pendings = Pending.objects.filter(entity=ent,department=dep,result=0).all().order_by("-request_time")
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
            asset = Asset.objects.filter(entity=user.entity,department=user.department,name=assetname).exclude(status=4).first()
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

    #同意时将资产从暂存区移除
    def leave_buffer(self,asset,staff,assetdict,assetname):
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
        
    #产生消息
    def create_message(self,result,pending_id,type,reply):
        operate = ""
        if type == 1:
            operate = "资产领用"
        elif type == 2:
            operate = "资产转移"
        elif type == 3:
            operate = "资产维保"
        elif type == 4:
            operate = "资产退库"
        elif type == 6:
            operate = "资产调拨"
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
            asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).exclude(status=4).first()
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
        if ptype != 6:
            Message.objects.create(user=pen.initiator,content=msg,type=ptype,pending=id)
        else:
            EPMessage.objects.create(user=pen.initiator,content=msg,type=status + 3)
        #更新资产信息
        #资产领用，与其他三类差异较大
        if ptype == 1:
            #该待办中的所有资产项目
            for assetdict in assetlist:
                assetname = list(assetdict.keys())[0]
                #待办单条资产
                asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).exclude(status=4).first()
                if not asset:continue
                #数量型
                if asset.type:
                    self.leave_buffer(asset,staff,assetdict,assetname)
                    #同意，更新usage
                    if status == 0:
                        use = json.loads(asset.usage)
                        if not use:
                            asset.usage = json.dumps([{staff.name:assetdict[assetname]}])
                            staff.hasasset = staff.hasasset + 1
                            staff.save()
                        else:
                            needupdate = True
                            for term in use:
                                if staff.name in term:
                                    term.update({staff.name:term[staff.name] + assetdict[assetname]})
                                    needupdate = False
                                    break
                            if needupdate:
                                staff.hasasset = staff.hasasset + 1
                                staff.save()
                                use.append({staff.name:assetdict[assetname]})
                            asset.usage = json.dumps(use)
                        AssetLog(asset=asset,entity=staff.entity,department=staff.department,type=2,expire_time=asset.create_time,number=assetdict[assetname],dest=staff).save()
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
                        AssetLog(asset=asset,entity=staff.entity,department=staff.department,type=2,number=1,expire_time=asset.create_time,dest=staff).save()
                        staff.hasasset = staff.hasasset + 1
                        staff.save()
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
                asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).exclude(status=4).first()
                #数量型
                if asset.type:
                    pro = json.loads(asset.process)
                    for i in pro:
                        if list(i.keys())[0] == staff.name and i[staff.name] == assetdict[assetname]:
                            staff.hasasset = staff.hasasset - 1
                            staff.save()
                            break
                    self.leave_buffer(asset,staff,assetdict,assetname)
                    #跨部门
                    if destdep != depart:
                        destuser.hasasset = destuser.hasasset + 1
                        destuser.save()
                        asset.number -= assetdict[assetname]
                        if asset.number == 0:
                            asset.status = 4
                        destlist = [{destuser.name:assetdict[assetname]}]
                        newasset = Asset(entity=entity,department=destdep,name=assetname,type=1,belonging=destuser,price=asset.price,life=asset.life,description=asset.description,additionalinfo=asset.additionalinfo,additional=asset.additional,number=assetdict[assetname],number_idle=0,usage=json.dumps(destlist),create_time=asset.create_time)
                        newasset.save()
                        #转移者
                        AssetLog(asset=asset,type=7,entity=staff.entity,department=staff.department,expire_time=asset.create_time,number=assetdict[assetname],price=asset.price * assetdict[assetname],src=staff,dest=destuser,life=asset.life).save()
                        #接收者
                        AssetLog(asset=newasset,type=1,entity=destuser.entity,department=destuser.department,expire_time=newasset.create_time,number=assetdict[assetname],price=newasset.price * assetdict[assetname],dest=destuser,life=newasset.life).save()
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
                                destuser.hasasset = destuser.hasasset + 1
                                destuser.save()
                                use.append({destuser.name:assetdict[assetname]})
                            asset.usage = json.dumps(use)
                        AssetLog(asset=asset,type=3,entity=destuser.entity,department=destuser.department,number=assetdict[assetname],src=staff,dest=destuser).save()
                    asset.save()
                #条目型
                else:
                    #跨部门
                    staff.hasasset = staff.hasasset - 1
                    staff.save()
                    destuser.hasasset = destuser.hasasset + 1
                    destuser.save()
                    if destdep != depart:
                        newasset = Asset(entity=entity,department=destdep,type=0,name=assetname,price=asset.price,life=asset.life,description=asset.description,additionalinfo=asset.additionalinfo,additional=asset.additional,belonging=destuser,user=destuser,status=1,create_time=asset.create_time)
                        newasset.save()
                        asset.status = 4
                        asset.save()
                        #转移者
                        AssetLog(asset=asset,type=7,entity=staff.entity,department=staff.department,number=1,expire_time=asset.create_time,life=newasset.life,price=newasset.price,src=staff,dest=destuser).save()
                        #接受者
                        AssetLog(asset=newasset,type=1,entity=destuser.entity,department=destuser.department,expire_time=newasset.create_time,number=1,price=newasset.price,dest=destuser,life=newasset.life).save()
                    #同部门
                    else:
                        asset.belonging = destuser
                        asset.user = destuser
                        asset.status = 1
                        asset.save()
                        AssetLog(asset=asset,type=3,entity=destuser.entity,department=destuser.department,number=1,src=staff,dest=destuser).save()
            #跨部门还需要向接受方发起类型确认的消息
            if destdep != depart:
                pd = Pending(entity=ent,department=destdep.id,initiator=pen.initiator,destination=pen.destination,asset=pen.asset,type=5,result=1)
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
                asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).exclude(status=4).first()
                if asset.type:
                    self.leave_buffer(asset,staff,assetdict,assetname)
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
                    AssetLog(asset=asset,type=4,entity=staff.entity,department=staff.department,number=assetdict[assetname],src=staff).save()
                else:
                    asset.status = 2
                    AssetLog(asset=asset,type=4,entity=staff.entity,department=staff.department,number=1,src=staff).save()
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
                asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).exclude(status=4).first()
                if asset.type:
                    pro = json.loads(asset.process)
                    for i in pro:
                        if list(i.keys())[0] == staff.name and i[staff.name] == assetdict[assetname]:
                            staff.hasasset = staff.hasasset - 1
                            staff.save()
                            break
                    self.leave_buffer(asset,staff,assetdict,assetname)
                    asset.number_idle += assetdict[assetname]
                    AssetLog(asset=asset,type=6,entity=staff.entity,department=staff.department,number=assetdict[assetname],src=staff).save()
                else:
                    staff.hasasset = staff.hasasset - 1
                    staff.save()
                    asset.status = 0
                    asset.user = None
                    asset.belonging = admin
                    AssetLog(asset=asset,type=6,entity=staff.entity,department=staff.department,number=1,src=staff).save()
                asset.save()
        #仅拒绝调拨
        if ptype == 6:
            admin = User.objects.filter(id=pen.initiator).first()
            fromdep = Department.objects.filter(id=admin.department).first()
            print(assetlist)
            for assetdict in assetlist:
                #待办单条资产
                assetname = list(assetdict.keys())[0]
                asset = Asset.objects.filter(entity=ent,department=fromdep,name=assetname).exclude(status=4).first()
                number = assetdict[assetname]
                #数量型
                if asset.type:
                    self.leave_buffer(asset,admin,{asset.name:number},asset.name)
                    asset.number_idle += number
                #条目型
                else:
                    asset.status = 0
                asset.save()
        # cyh
        # 通知员工审批结果,审批人的回复
        db.close_old_connections()
        newprocess = applyOutcome(req.data)
        db.close_old_connections()
        newprocess.start()
        # cyh
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
            if pending.type == 6 or pending.type == 2:
                fromuser = User.objects.filter(id=pending.initiator).first()
                fromdep = Department.objects.filter(id=fromuser.department).first()
                asset = Asset.objects.filter(department=fromdep,entity=ent,name=assetname).exclude(status=4).first()
            else:
                asset = Asset.objects.filter(department=dep,entity=ent,name=assetname).exclude(status=4).first()
            returnlist.append({"id":asset.id,"assetname":assetname,"assetclass":asset.category.name if asset.category != None else "暂未确定类别","assetcount":item[assetname]})
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
        broken_assets = Asset.objects.filter(entity=ent,department=dep,expire=True).exclude(status=4).all()
        find_old_assets = Asset.objects.filter(entity=ent,department=dep,expire=False).exclude(status=4).all()
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
        assets = [Asset.objects.filter(entity=ent,department=dep,name=assetname).exclude(status=4).first() for assetname in assetnames]
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
        page = self.getparse(req.data,"page","int")
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
        assets = Asset.objects.filter(entity=ent,department=dep).exclude(status=4).all()
        if parent:
            parentasset = Asset.objects.filter(entity=ent,department=dep,name=parent).exclude(status=4).first()
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
        count = len(return_list)
        return_list = return_list[10 * page - 10:10 * page:]
        return Response({"code":0,"data":[{"name":item.name,"key":item.id,"description":item.description,"assetclass":item.category.name if item.category != None else "尚未确定具体类别","type":item.type}for item in return_list],"count":count})
        
    #防止父结构出现自环
    def validparent(self,asset,name):
        if asset.name == name:
            return False
        while(asset.parent != None):
            asset = asset.parent
            if asset.name == name:
                return False
        return True
    
    #资产信息变更
    @Check
    @action(detail=False, methods=['post'], url_path="modifyasset")
    def modifyasset(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        name = require(req.data, "name", "string" , err_msg="Error type of [name]")
        parent = self.getparse(req.data,"parent","string")
        number = self.getparse(req.data,"number","int")
        description = self.getparse(req.data,"description","string")
        add = req.data["addition"] if "addition" in req.data.keys() else {}
        asset = Asset.objects.filter(entity=ent,department=dep,name=name).exclude(status=4).first()
        if not asset:
            raise Failure("资产不存在")
        if parent:
            parentasset = Asset.objects.filter(name=parent).exclude(status=4).first()
            if not parentasset:
                raise Failure("父级资产不存在")
            if self.validparent(parentasset,name) == False:
                raise Failure("资产类别关系存在自环")
            asset.parent = parentasset
        if add:
            addition = json.loads(asset.additional)
            if type(add) == str:
                add = eval(add)
            addition.update(add)
            asset.additional = json.dumps(addition)
        if number != "":
            if asset.type:
                if asset.price != None and asset.number != None and asset.number_idle != None:
                    AssetLog(type=9,entity=req.user.entity,department=req.user.department,asset=asset,number=number,price=asset.price * (asset.number_idle - number),expire_time=asset.create_time,life=asset.life).save()
                asset.number += number - asset.number_idle
                asset.number_idle = number
        if description != "":
            asset.description = description
        asset.save()
        return Response({"code":0,"info":"success"})

    #调拨的有效检查
    def valid_asset(self,assets):
        assetlist = []
        #错误检查
        for assetdict in assets:
            id = assetdict["id"]
            name = assetdict["assetname"]
            number = assetdict["assetnumber"]
            asset = Asset.objects.filter(id=id).exclude(status=4).first()
            if not asset or asset.name != name:
                raise Failure("资产信息错误")
            if (asset.type and asset.number_idle < number) or (not asset.type and asset.status):
                raise Failure("闲置资产数量不足")
            assetlist.append({name:number})
        return assetlist
    
    #调拨的资产状态改变
    def asset_in_process(self,assets,username):
        for assetdict in assets:
            id = assetdict["id"]
            number = assetdict["assetnumber"]
            asset = Asset.objects.filter(id=id).exclude(status=4).first()
            #数量型
            if asset.type:
                asset.number_idle -= number
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
    
    #申请资产调拨
    @Check
    @action(detail=False, methods=['post'], url_path="transfer")
    def transfer(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        assets = require(req.data, "transfer", "list" , err_msg="Error type of [transfer]")
        reason = require(req.data, "reason", "string" , err_msg="Error type of [reason]")
        department = require(req.data, "department", "string" , err_msg="Error type of [department]")
        todep = Department.objects.filter(name=department).first()
        if not todep:
            raise Failure("目标部门不存在")
        dest = User.objects.filter(id=todep.admin).first()
        if not dest:
            raise Failure("目标部门无资产管理员")
        assetlist = self.valid_asset(assets)
        for asset in assetlist:
            assetname = list(asset.keys())[0]
            sameasset = Asset.objects.filter(entity=ent,department=todep,name=assetname).exclude(status=4).first()
            if sameasset:
                raise Failure("资产%s在目标用户所在部门存在同名资产" % assetname)
        self.asset_in_process(assets,req.user.name)
        pending = Pending(entity=ent.id,department=todep.id,initiator=req.user.id,destination=dest.id,asset=json.dumps(assetlist),type=6,description=reason)
        pending.save()
        return Response({"code":0,"info":"success"})
    
    #审批调拨并为调拨的资产选定类别
    @Check
    @action(detail=False, methods=['post'], url_path="setcat")
    def setcat(self,req:Request):
        dep = Department.objects.filter(id=req.user.department).first()
        ent = Entity.objects.filter(id=req.user.entity).first()
        id = require(req.data, "id", "int" , err_msg="Error type of [id]")
        status = require(req.data, "status", "int" , err_msg="Error type of [status]")
        reply = require(req.data, "reason", "string" , err_msg="Error type of [reason]")
        pen = Pending.objects.filter(entity=ent.id,department=dep.id,id=id,type=6).first()
        #检查待办项合法
        if not pen:
            raise Failure("待办项不存在")
        if pen.result:
            raise Failure("此待办已审批完成")
        thisadmin = req.user
        fromadmin = User.objects.filter(id=pen.initiator).first()
        fromdep = Department.objects.filter(id=fromadmin.department).first()
        assetlist = require(req.data,"asset","list",err_msg="Error type of [asset]")
        for item in assetlist:
            asset = Asset.objects.filter(entity=ent,department=fromdep,id=item["id"]).exclude(status=4).first()
            assetclass = AssetClass.objects.filter(entity=ent,department=dep,name=item["label"]).first()
            if not asset:
                raise Failure("资产不存在")
            if status == 0:
                if not assetclass:
                    raise Failure("资产类别不存在")
                if asset.type != assetclass.type:
                    raise Failure("资产与资产类别类型不符")
        #更新待办信息
        pen.result = 2 if status else 1
        pen.review_time = utils_time.get_timestamp()
        pen.reply = reply
        pen.save()
        if status == 0:
            for assetdict in assetlist:
                #待办单条资产
                asset = Asset.objects.filter(entity=ent,department=fromdep,id=assetdict["id"]).exclude(status=4).first()
                assetclass = AssetClass.objects.filter(entity=ent,department=dep,name=assetdict["label"]).first()
                number = assetdict["number"]
                #数量型
                if asset.type:
                    self.leave_buffer(asset,fromadmin,{asset.name:number},asset.name)
                    asset.number -= number
                    if asset.number == 0:
                        asset.status = 4
                    newasset = Asset(entity=ent,department=dep,name=asset.name,type=1,belonging=thisadmin,price=asset.price,life=asset.life,description=asset.description,additionalinfo=asset.additionalinfo,additional=asset.additional,number=number,number_idle=number,create_time=asset.create_time,category=assetclass)
                    newasset.save()
                    #转移者
                    AssetLog(asset=asset,type=7,entity=fromadmin.entity,department=fromadmin.department,number=number,src=fromadmin,dest=thisadmin,expire_time=asset.create_time,life=newasset.life,price=newasset.price*number).save()
                    #接收者
                    AssetLog(asset=newasset,type=1,entity=thisadmin.entity,department=thisadmin.department,expire_time=newasset.create_time,number=number,dest=thisadmin,life=newasset.life,price=newasset.price*number).save()
                else:
                    newasset = Asset(entity=ent,department=dep,type=0,name=asset.name,price=asset.price,life=asset.life,description=asset.description,additionalinfo=asset.additionalinfo,additional=asset.additional,belonging=thisadmin,status=0,create_time=asset.create_time,category=assetclass)
                    newasset.save()
                    asset.status = 4
                    #转移者
                    AssetLog(asset=asset,type=7,entity=fromadmin.entity,department=fromadmin.department,expire_time=asset.create_time,number=1,src=fromadmin,dest=thisadmin,life=newasset.life,price=newasset.price).save()
                    #接受者
                    AssetLog(asset=newasset,type=1,entity=thisadmin.entity,department=thisadmin.department,expire_time=newasset.create_time,number=1,dest=thisadmin,life=newasset.life,price=newasset.price).save()
                asset.save()
        return Response({"code":0,"info":"success"})
    
    #获取所有维保申请
    @Check
    @action(detail=False,methods=['get'],url_path="getallmatain")
    def getallmatain(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        pendings = Pending.objects.filter(entity=ent.id,department=dep.id,type=3,result=1).all()
        return_list = []
        for item in pendings:
            assets = json.loads(item.asset)
            assetlist = []
            for assetdict in assets:
                assetname = list(assetdict.keys())[0]
                asset = Asset.objects.filter(entity=ent,department=dep,name=assetname).first()
                if asset:
                    assetlist.append({"id":asset.id,"name":assetname})
            return_list.append({"id":item.id,"assets":assetlist})
        return Response({"code":0,"info":return_list})
    
    #维保完成
    @Check
    @action(detail=False,methods=['post'],url_path="matianover")
    def matianover(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        assets = require(req.data, "assets", "list" , err_msg="Error type of [assets]")
        pid = require(req.data, "id", "int" , err_msg="Error type of [id]")
        pending = Pending.objects.filter(id=pid).first()
        staff = User.objects.filter(id=pending.initiator).first()
        numlist = json.loads(pending.asset)
        numdict = {}
        for item in numlist:
            numdict.update({list(item.keys())[0]:item[list(item.keys())[0]]})
        for item in assets:
            asset = Asset.objects.filter(id=int(item["id"])).first()
            if not asset or asset.name != item["name"]:
                raise Failure("资产信息有误")
        useasset = []
        brokenasset = []
        for item in assets:
            asset = Asset.objects.filter(id=int(item["id"])).first()
            #数量型
            if asset.type:
                #移出维保区
                number = numdict[asset.name]
                maintain = json.loads(asset.maintain)
                for term in maintain:
                    if staff.name in term:
                        if number == term[staff.name]:
                            maintain.remove(term)
                        else:
                            term.update({staff.name:term[staff.name] - number})
                        break
                asset.maintain = json.dumps(maintain)
                #正常使用
                if int(item["state"]) == 1:
                    AssetLog(entity=ent.id,department=dep.id,asset=asset,type=5,dest=staff,number=number).save()
                    use = json.loads(asset.usage)
                    if not use:
                        asset.usage = json.dumps([{staff.name:number}])
                    else:
                        needupdate = True
                        for term in use:
                            if staff.name in term:
                                term.update({staff.name:term[staff.name] + number})
                                needupdate = False
                                break
                        if needupdate:
                            use.append({staff.name:number})
                        asset.usage = json.dumps(use)
                #报废
                else:
                    use = json.loads(asset.usage)
                    donothave = True
                    for i in use:
                        if list(i.keys())[0] == staff.name:
                            donothave = False
                            break
                    if donothave:
                        staff.hasasset = staff.hasasset - 1
                        staff.save()
                    AssetLog(type=10,entity=req.user.entity,asset=asset,department=req.user.department,number=number,price=asset.price * number,expire_time=asset.create_time,life=asset.life,src=staff).save()
                    if asset.number_expire != None:
                        asset.number_expire += number
                    else:
                        asset.number_expire = number
                    if asset.number_expire == asset.number:
                        asset.expire = True
            else:
                if int(item["state"]) == 1:
                    AssetLog(entity=ent.id,department=dep.id,asset=asset,type=5,dest=staff,number=1).save()
                    asset.status = 1
                else:
                    staff.hasasset = staff.hasasset - 1
                    staff.save()
                    AssetLog(type=10,entity=req.user.entity,asset=asset,department=req.user.department,number=1,price=asset.price,expire_time=asset.create_time,life=asset.life,src=staff).save()
                    asset.expire = True
            asset.save()
            if int(item["state"]) == 1:
                useasset.append(item["name"])
            else:
                brokenasset.append(item["name"])
        content = "维保已完成。"
        if useasset:
            content += "返还资产:" + str(useasset).replace('[','').replace(']','') + " "
        if brokenasset:
            content += "报废资产:" + str(brokenasset).replace('[','').replace(']','') + " "
        Message(user=staff.id,pending=pending.id,type=7,content=content).save()
        pending.result = 3
        pending.save()
        return Response({"code":0,"info":"ok"})
    
    #更新告警信息列表
    def update_alert(self,ent,dep,userid):
        awares = Alert.objects.filter(entity=ent,department=dep).all()
        for item in awares:
            asset = item.asset
            if not asset:
                continue
            old_msg = EPMessage.objects.filter(user=userid,asset=asset,type=item.type).first()
            #年限不足
            if item.type == 0:
                #确认
                if utils_time.get_timestamp() - asset.create_time > item.number * 31536000:
                    if not old_msg:
                        EPMessage(user=userid,asset=asset,type=0,content="%s使用已超过%d年" % (asset.name,item.number),aware=item.id).save()
                    else:
                        old_msg.content = "%s使用已超过%d年" % (old_msg.asset.name,item.number)
                        old_msg.save()
                else:
                    if old_msg:
                        old_msg.delete()
            #数量不足
            else:
                #确认
                if asset.number < item.number:
                    if not old_msg:
                        EPMessage(user=userid,asset=asset,type=1,content="%s数量不足%d" % (asset.name,item.number),aware=item.id).save()
                    else:
                        old_msg.content = "%s数量不足%d" % (old_msg.asset.name,item.number)
                        old_msg.save()
                else:
                    if old_msg:
                        old_msg.delete()
    
    #获得所有消息通知
    @Check
    @action(detail=False,methods=['get'],url_path="allmessage")
    def allmessage(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        self.update_alert(ent,dep,req.user.id)
        msgs = EPMessage.objects.filter(user=req.user.id).all().order_by("-time")
        return_list = [{"key":item.id,"type":0 if item.type == 0 or item.type == 1 else item.type - 1,"message":item.content}for item in msgs]
        return Response({"code":0,"info":return_list})
    
    #是否有消息通知
    @Check
    @action(detail=False,methods=['get'],url_path="beinformed")
    def beiinformed(self,req:Request):
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        self.update_alert(ent,dep,req.user.id)
        msgs = EPMessage.objects.filter(user=req.user.id).all()
        if msgs:
            return Response({"code":0,"info":True})
        else:
            return Response({"code":0,"info":False})
        
    #删除资产折旧信息
    @Check
    @action(detail=False,methods=['delete'],url_path="dclearmg")
    def dclearmg(self,req:Request):
        id = require(req.data, "key", "int" , err_msg="Error type of [key]")
        msg = EPMessage.objects.filter(id=id).first()
        if not msg:
            raise Failure("消息不存在")
        if msg.type == 0 or msg.type == 1:
            raise Failure("不可删除告警信息")
        msg.delete()
        return Response({"code":0,"info":"success"})