# cyh
import json
import re
import time

from django.http import HttpRequest, HttpResponse
from user.models import User
from department.models import Department, Entity
from logs.models import AssetLog
from asset.models import Asset, AssetClass

from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.identity import *
from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import action, permission_classes,api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
from rest_framework.views import APIView

class asset(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    allowed_identity = [EP]
    
    def getpage(self,body):
        if "page" in body.keys():
            page = int(body["page"])
        else:
            page = 1
        return page
    
    #hyx
    #创建新属性
    
    # 资产管理员查看自己的部门和业务实体
    @Check
    @action(detail=False, methods=['get'], url_path="getbelonging")
    def get_belonging(self, req:Request):
        return Response({
            "code": 0,
            "entity": Entity.objects.filter(id=req.user.entity).first().name,
            "department": Department.objects.filter(id=req.user.department).first().name,
        })
    
    #添加属性
    @Check
    @action(detail=False, methods=["post"], url_path="createattributes")
    def createattributes(self,req:Request):
        name = require(req.data,"name","string",err_msg="Missing or error type of [name]")
        dep = Department.objects.filter(id=req.user.department).first()
        attributes = json.loads(dep.attributes)
        if name not in attributes:
                attributes.append(name)
        dep.attributes = json.dumps(attributes)
        dep.save()
        return Response({"code":0,"detail":"创建成功"})
    
    #更改部门额外可选标签项
    @Check
    @action(detail=False, methods=["post"], url_path="setlabel")
    def setlabel(self,req:Request):
        label = require(req.data,"label","list",err_msg="Missing or error type of [label]")
        dep = Department.objects.filter(id=req.user.department).first()
        dep.label = json.dumps(label)
        dep.save()
        return Response({"code":0,"detail":"ok"})
    
    #获取当前部门所有已选择标签项
    @Check
    @action(detail=False,methods=["get"],url_path="usedlabel")
    def usedlabel(self,req:Request):
        dep = Department.objects.filter(id=req.user.department).first()
        return Response({"code":0,"info":json.loads(dep.label)})
    
    #获取当前部门所有额外属性
    @Check
    @action(detail=False,methods=["get"],url_path="attributes")
    def attributes(self,req:Request):
        dep = Department.objects.filter(id=req.user.department).first()
        return Response({"code":0,"info":json.loads(dep.attributes)})
    
    #递归构造类别树存储
    def classtree(self,ent,dep,parent):
        #递归基
        roots = AssetClass.objects.filter(entity=ent,department=dep,parent=parent).all()
        # print(roots)
        if not roots:
            return "$"
        else:
            res = {}
            for root in roots:
                sym = "1" if root.type else "0"
                res.update({root.name + "," + sym : self.classtree(ent,dep,root)})
            return res

    #返回类别树结构
    @Check
    @action(detail=False, methods=["get"], url_path="assetclasstree") 
    def assetclasstree(self,req:Request):
        if req.user.identity != 3:
            raise Failure("此用户无权查看部门结构")
        dep = Department.objects.filter(id=req.user.department).first()
        ent = Entity.objects.filter(id=req.user.entity).first()
        ret = {
            "code" : 0,
            "info" : {dep.name:self.classtree(ent,dep,None)}
        }
        return Response(ret)
    #hyx end
    
    #获取所有资产
    @Check
    @action(detail=False, methods=["get"], url_path="get")
    def get_by_condition(self, req:Request):
        page = self.getpage(req.query_params)
        et = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        asset = list(Asset.objects.filter(entity=et, department=dep).exclude(status=4).all())
        count = len(asset)
        asset = asset[10 * page - 10:10 * page:]
        ret = {
            "code": 0,
            "data": [{"key": ast.id, "name": ast.name, "category": ast.category.name if ast.category != None else "尚未确定具体类别", "description": ast.description, "type": ast.type} for ast in asset],
            "count":count
        }
        return Response(ret)
               
    #增加资产
    @Check  
    @action(detail=False, methods=["post"], url_path="post") 
    def post(self, req:Request):
        if type(req.data) is not list:
            raise ParamErr("请求参数格式错误")
        entity = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        toadd = []
        for asset in req.data:
            if 'parent' in asset.keys() and asset["parent"] != "" and asset["parent"] != None:
                parent_name = require(asset, 'parent', 'string', "Error type of [parent]")
                parent = Asset.objects.filter(entity=entity, department=dep, name=parent_name).exclude(status=4).first()
                if not parent:
                    raise Failure("上级资产不存在")
            else:
                parent = None
            category_name = require(asset, "category", "string", "Missing or error type of [category]")
            category = AssetClass.objects.filter(entity=entity, department=dep, name=category_name).first()
            if not category:
                raise Failure("该资产类型不存在")
            tp = category.type
            
            name = require(asset, "name", "string", "Missing or error type of [name]")
            if len(name) > 128:
                raise Failure("名称过长")
            if Asset.objects.filter(entity=entity, department=dep, name=name).exclude(status=4).first():
                raise Failure("名称重复")
            if "belonging" in asset.keys() and asset["belonging"] != "" and asset["belonging"] != None:
                belonging = require(asset, "belonging", "string", "Missing or error type of [belonging]")
                belonging = User.objects.filter(entity=entity.id, department=dep.id, name=belonging).first()
                if not belonging:
                    raise Failure("挂账人不存在或不在部门中")
            else:
                belonging = req.user
            price = require(asset, "price", "float", "Missing or error type of [price]")

            life = require(asset, "life", "int", "error type of [life]")
            if life < 0:
                raise Failure("使用年限不能为负数")
            if 'description' in asset.keys() and asset["description"] != None:
                description = require(asset, 'description', 'string', "Error type of [description]")
            else:
                description = ""
            if "addtional" in asset.keys() and asset["addtional"] != "" and asset["addtional"] != None:
                addi = asset["addtional"]
                additional = {}
                for item in addi:
                    if "value" in item:
                        additional.update({item["key"]:item["value"]})
                additional = json.dumps(additional)
            else:
                additional = "{}"
            if "additionalinfo" in asset.keys() and asset["additionalinfo"] != "" and asset["additionalinfo"] != None:
                additionalinfo = require(asset,"additionalinfo","string","Error type of [additionalinfo]")
            else:
                additionalinfo = ""
            if 'hasimage' in asset.keys() :
                hasimage = require(asset, 'hasimage', 'boolean', "Error type of [hasimage]")
            else:
                hasimage = False
            if tp == True:
                number = require(asset, "number", "int", "Missing or error type of [number]")
                if number < 0:
                    raise Failure("数量不能为负数")
                number_idle = number
                usage = "[]"
                maintain = "[]"
                number_expire = 0
                expire = False
                toadd.append(Asset(parent=parent, 
                                    department=dep, 
                                    entity=entity, 
                                    category=category, 
                                    type=tp, 
                                    name=name, 
                                    belonging=belonging, 
                                    price=price, 
                                    life=life, 
                                    description=description, 
                                    additional=additional,
                                    additionalinfo=additionalinfo,
                                    number=number,
                                    number_idle=number_idle,
                                    usage=usage,
                                    maintain=maintain,
                                    number_expire=number_expire,
                                    expire=expire,
                                    haspic=hasimage))
            else:
                user = None
                status = 0
                toadd.append(Asset(parent=parent, 
                                    department=dep, 
                                    entity=entity, 
                                    category=category, 
                                    type=tp, 
                                    name=name, 
                                    number=1,
                                    belonging=belonging, 
                                    price=price, 
                                    life=life, 
                                    description=description,
                                    additionalinfo=additionalinfo, 
                                    additional=additional,
                                    user=user,
                                    status=status,
                                    haspic=hasimage))
                
        for a in toadd:
            a.save()
            AssetLog(asset=a,type=1,entity=req.user.entity,department=req.user.department,number=a.number,price=a.price*a.number,expire_time=a.create_time,life=a.life).save()
        return Response({"code": 0, "detail": "success"})
    # cyh
    # 批量删除资产
    @Check
    @action(detail=False, methods=['delete'], url_path="delete")
    def delete(self, req:Request):
        names = req.data
        if type(names) is not list:
            raise ParamErr("请求参数格式不正确")
        et = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        assets = Asset.objects.filter(entity=et, department=dep, name__in=names).exclude(status=4)
        for asset in assets:
            if asset.number and asset.price:
                AssetLog(type=8,entity=req.user.entity,department=req.user.department,number=asset.number if asset.type else 1,price=asset.price * asset.number,expire_time=asset.create_time,life=asset.life).save()
            asset.delete()
        return Response({"code": 0, "detail": "success"})
    
    #资产历史格式转换
    def process_history(self,pagelogs):
        returnlist = []
        for item in pagelogs:
            if item.type == 1:
                if item.dest:
                    returnlist.append({"type":1,"content":"用户%s从外部门获取,数量:%d" % (item.dest.name,item.number),"time":item.time,"id":item.id,"asset":item.asset.name if item.asset != None else "已删除资产"})
                else:
                    returnlist.append({"type":1,"content":"资产管理员导入,数量:%d" % item.number,"time":item.time,"id":item.id,"asset":item.asset.name if item.asset != None else "已删除资产"})
            elif item.type == 2:
                returnlist.append({"type":2,"content":"用户%s领用,数量:%d" % (item.dest.name,item.number),"time":item.time,"id":item.id,"asset":item.asset.name if item.asset != None else "已删除资产"})
            elif item.type == 3:
                returnlist.append({"type":3,"content": "用户%s向部门内用户%s转移,数量:%d" % (item.src.name,item.dest.name,item.number),"time":item.time,"id":item.id,"asset":item.asset.name if item.asset != None else "已删除资产"})
            elif item.type == 4:
                returnlist.append({"type":4,"content": "用户%s申请维保,数量:%d" % (item.src.name,item.number),"time":item.time,"id":item.id,"asset":item.asset.name if item.asset != None else "已删除资产"})
            elif item.type == 5:
                returnlist.append({"type":4,"content": "用户%s维保完成并返还,数量:%d" % (item.dest.name,item.number),"time":item.time,"id":item.id,"asset":item.asset.name if item.asset != None else "已删除资产"})
            elif item.type == 6:
                returnlist.append({"type":5,"content": "用户%s退库,数量:%d" % (item.src.name,item.number),"time":item.time,"id":item.id,"asset":item.asset.name if item.asset != None else "已删除资产"})
            elif item.type == 7:
                returnlist.append({"type":3,"content": "用户%s向外部门用户%s转移,数量:%d" % (item.src.name,item.dest.name,item.number),"time":item.time,"id":item.id,"asset":item.asset.name if item.asset != None else "已删除资产"})
            elif item.type == 9:
                returnlist.append({"type":6,"content": "资产闲置数量更改为%d" % (item.number),"time":item.time,"id":item.id,"asset":item.asset.name if item.asset != None else "已删除资产"})
            elif item.type == 10:
                returnlist.append({"type":4,"content": "用户%s申请维保的资产报废,数量:%d" % (item.src.name,item.number),"time":item.time,"id":item.id,"asset":item.asset.name if item.asset != None else "已删除资产"})
            else: continue
        return returnlist

    #hyx资产历史
    @Check
    @action(detail=False, methods=['get'], url_path="history")
    def history(self,req:Request):
        id = int(req.query_params["id"])
        page = self.getpage(req.query_params)
        asset = Asset.objects.filter(id=id).exclude(status=4).first()
        logs = list(AssetLog.objects.filter(asset=asset).all().order_by("-time"))
        count = len(logs)
        pagelogs = logs[5 * page - 5:5 * page:]
        returnlist = self.process_history(pagelogs)
        return Response({"code": 0, "info": returnlist,"count":count})
    
    #所有历史
    @Check
    @action(detail=False, methods=['get'], url_path="allhistory")
    def allhistory(self,req:Request):
        page = self.getpage(req.query_params)
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        logs = list(AssetLog.objects.filter(entity=ent.id,department=dep.id).all().order_by("-time"))
        count = len(logs)
        pagelogs = logs[10 * page - 10:10 * page:]
        returnlist = self.process_history(pagelogs)
        return Response({"code": 0, "info": returnlist,"count":count})
    
    #条件查询历史
    @Check
    @action(detail=False,methods=['get'],url_path="queryhis")
    def queryhis(self,req:Request):
        page = self.getpage(req.query_params)
        ent = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        asset = Asset.objects.filter(entity=ent,department=dep).exclude(status=4).all()
        logs = AssetLog.objects.filter(asset__in=list(asset)).all().order_by("-time")
        if "type" in req.query_params.keys() and req.query_params["type"] != "":
            type = int(req.query_params["type"])
            if type == 1:
                logs = logs.filter(type=1).all()
            elif type == 2:
                logs = logs.filter(type=2).all()
            elif type == 3:
                logs = logs.filter(type__in=[3,7]).all()
            elif type == 4:
                logs = logs.filter(type__in=[4,5,10]).all()
            elif type == 5:
                logs = logs.filter(type=6).all()
            else:
                logs = logs.filter(type=9).all()
        if "assetname" in req.query_params.keys() and req.query_params["assetname"] != "":
            assetname = req.query_params["assetname"]
            asset = asset.filter(name=assetname).first()
            logs = logs.filter(asset=asset).all()
        if "timefrom" in req.query_params.keys() and req.query_params["timefrom"] != "":
            timefrom = float(req.query_params["timefrom"])
            logs = logs.filter(time__gte=timefrom).all()
        if "timeto" in req.query_params.keys() and req.query_params["timeto"] != "":
            timeto = float(req.query_params["timeto"])
            logs = logs.filter(time__lte=timeto).all()
        count = len(logs)
        pagelogs = logs[10 * page - 10:10 * page:]
        returnlist = self.process_history(pagelogs)
        return Response({"code": 0, "info": returnlist,"count":count})
  
class assetclass(APIView):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    allowed_identity = [EP, EN]
    
    @Check
    def delete(self,req:Request):
        name = require(req.data, "name", err_msg="Error type of [name]")
        et = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        ac = AssetClass.objects.filter(entity=et, department=dep, name=name).first()
        if not ac:
            raise Failure("该资产类别不存在")
        ac.delete()
        return Response({"code": 0, "detail": "success"})
    
    @Check
    def put(self,req:Request):
        oldname = require(req.data, "oldname", err_msg="Error type of [oldname]")
        newname = require(req.data, "newname", err_msg="Error type of [newname]")
        if not newname or " " in newname:
            raise Failure("新的资产类别名不可为空或有空格")
        et = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        if newname == dep.name:
            raise Failure("新的资产类别名不可与部门名相同")
        ac = AssetClass.objects.filter(entity=et, department=dep, name=oldname).first()
        if not ac:
            raise Failure("该资产类别不存在")
        ac.name = newname
        ac.save()
        return Response({"code": 0, "detail": "success"})
    
    @Check
    def post(self, req:Request):
        et = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        if "parent" in req.data:
            parent = require(req.data, "parent", err_msg="Error type of [parent]")
            parent = AssetClass.objects.filter(entity=et, department=dep, name=parent).first()
            if not parent:
                raise Failure("父类别不存在")
        else:
            parent = None
        name = require(req.data, "name", err_msg="Error type of [name]")
        if not name or " " in name:
            raise Failure("资产类别名不可为空或有空格")
        if len(name) > 128:
            raise Failure("名称过长")
        if name == dep.name:
            raise Failure("资产类别名不可与部门同名")
        if AssetClass.objects.filter(entity=et, department=dep, name=name).first():
            raise Failure("存在重名类别")
        tp = require(req.data, "type", "int", err_msg="Error type of [type]")
        tp = bool(tp)
        AssetClass.objects.create(parent=parent, entity=et, department=dep, name=name, type=tp)
        return Response({"code": 0, "detail": "success"})
    
    # 返回该部门下的类别
    @Check
    def get(self, req:Request):
        et = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        classes = AssetClass.objects.filter(entity=et, department=dep)
        return Response({
            "code": 0,
            "data": [clas.name for clas in classes],
        })
# cyh

#hyx
#资产详细信息
@api_view(['GET'])
@authentication_classes([LoginAuthentication])
@permission_classes([GeneralPermission])
def getdetail(req:Request):
    id = require(req.query_params, "id", err_msg="Missing or error type of [id]")
    et = Entity.objects.filter(id=req.user.entity).first()
    dep = Department.objects.filter(id=req.user.department).first()
    asset = Asset.objects.filter(entity=et, department=dep, id=id).exclude(status=4).first()
    if not asset:
        raise Failure("该资产不存在")
    ret = {
        "code": 0,
        "data":asset.serialize(),
    }
    return Response(ret)

#资产全视图，标签二维码显示，不需要登录
@api_view(['GET'])
def fulldetail(req:Request,id:any):
    asset = Asset.objects.filter(id=int(id)).exclude(status=4).first()
    if not asset:
        raise Failure("该资产不存在")
    ret = {
        "code": 0,
        "data":asset.serialize(),
    }
    return Response(ret)