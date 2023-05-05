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
    
    @Check
    @action(detail=False, methods=["post"], url_path="createattributes")
    def createattributes(self,req:Request):
        name = require(req.data,"name","string",err_msg="Missing or error type of [name]")
        if not name or " " in name:
            raise Failure("属性名不可为空或有空格")
        dep = Department.objects.filter(id=req.user.department).first()
        attributes = dep.attributes
        if not attributes:
            attributes = name
        else:
            attri = dep.attributes.split(',')
            if name in attri:
                raise Failure("该属性已存在")
            attributes += "," + name
        dep.attributes = attributes
        dep.save()
        return Response({"code":0,"detail":"创建成功"})
    
    #更改部门额外可选标签项
    @Check
    @action(detail=False, methods=["post"], url_path="setlabel")
    def setlabel(self,req:Request):
        label = require(req.data,"label","string",err_msg="Missing or error type of [label]")
        dep = Department.objects.filter(id=req.user.department).first()
        labels = label[1:len(label) - 1:1].replace('"','').replace('\'','').replace(' ','')
        dep.label = labels
        dep.save()
        return Response({"code":0,"detail":"ok"})
    
    #获取当前部门所有已选择标签项
    @Check
    @action(detail=False,methods=["get"],url_path="usedlabel")
    def usedlabel(self,req:Request):
        dep = Department.objects.filter(id=req.user.department).first()
        if not dep.label:
            return Response({"code":0,"info":[]})
        else:
            info = dep.label.split(',')
            return Response({"code":0,"info":info})
    
    #获取当前部门所有额外属性
    @Check
    @action(detail=False,methods=["get"],url_path="attributes")
    def attributes(self,req:Request):
        dep = Department.objects.filter(id=req.user.department).first()
        if not dep.attributes:
            return Response({"code":0,"info":[]})
        else:
            info = dep.attributes.split(',')
            return Response({"code":0,"info":info})
    
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
    
    @Check
    @action(detail=False, methods=["get"], url_path="get")
    def get_by_condition(self, req:Request):
        et = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        # 按名字查直接返回单个
        if "name" in req.query_params.keys():
            name = require(req.query_params, "name", err_msg="Error type of [name]")
            asset = Asset.objects.filter(entity=et, department=dep, name=name).exclude(status=4).first()
            if not asset:
                return Response({
                    "code": 0,
                    "data": []
                })
            return Response({
                "code": 0,
                "data": [return_field(asset.serialize(), ["name", "description", "category", "type"])]
            })
        asset = Asset.objects.filter(entity=et, department=dep).exclude(status=4)
        if "parent" in req.query_params.keys():
            parent = require(req.query_params, "parent", "string", "Error type of [parent]")
            parent = Asset.objects.filter(entity=et, department=dep, name=parent).exclude(status=4).first()
            if not parent:
                raise Failure("所提供的上级资产不存在")
            asset = asset.filter(parent=parent)
        if "category" in req.query_params.keys():
            cate = require(req.query_params, "category", err_msg="Error type of [category]")
            cate = AssetClass.objects.filter(entity=et, department=dep, name=cate).first()
            if not cate:
                raise Failure("所提供的资产类型不存在")
            asset = asset.filter(category=cate)
            # print(asset)
        # 按挂账人进行查询还需要讨论一下，比如一个部门下的资产的挂账人除了资产管理员还可以是谁
        if "belonging" in req.query_params.keys():
            user = require(req.query_params, "belonging", err_msg="Error type of [belonging]")
            user = User.objects.filter(entity=et.id, department=dep.id, name=user).first()
            if not user:
                raise Failure("所提供的挂账人不存在")
            asset = asset.filter(belonging=user)
        if "from" in req.query_params.keys():
            from_ = require(req.query_params, "from", "float", err_msg="Error type of [from]")
            asset = asset.filter(create_time__gte=from_)
        if "to" in req.query_params:
            to_ = require(req.query_params, "to", "float", err_msg="Error type of [to]")
            asset = asset.filter(create_time__lte=to_)
        # 资产使用者只能是本部门下的吗？
        if "user" in req.query_params.keys():
            user = require(req.query_params, "user", err_msg="Error type of [user]")
            user = User.objects.filter(name=user).first()
            if not user:
                raise Failure("所提供的使用者不存在")
            asset = asset.filter(user=user)
        if "status" in req.query_params.keys():
            status = require(req.query_params, "status", "int", err_msg="Error type of [status]")
            asset = asset.filter(status=status)
        if "pricefrom" in req.query_params.keys():
            pfrom = require(req.query_params, "pricefrom", "float", err_msg="Error type of [pricefrom]")
            asset = asset.filter(price__gte=pfrom)
        if "priceto" in req.query_params.keys():
            pto = require(req.query_params, "priceto", "float", err_msg="Error type of [priceto]")
            asset = asset.filter(price__lte=pto)
        ret = {
            "code": 0,
            "data": [{"key": ast.id, "name": ast.name, "category": ast.category.name if ast.category != None else "请手动设定资产类别", "description": ast.description, "type": ast.type} for ast in asset] 
        }
        return Response(ret)
               
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
                                    belonging=belonging, 
                                    price=price, 
                                    life=life, 
                                    description=description, 
                                    additional=additional,
                                    user=user,
                                    status=status,
                                    haspic=hasimage))
                
        for a in toadd:
            a.save()
            AssetLog(asset=a,type=1,entity=req.user.entity,department=req.user.department,number=a.number if a.type else 1).save()
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
            AssetLog(type=8,entity=req.user.entity,department=req.user.department,number=asset.number if asset.type else 1,price=asset.price * asset.number,expire_time=asset.create_time).save()
            asset.delete()
        return Response({"code": 0, "detail": "success"})
  
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
@CheckRequire
def fulldetail(req:HttpRequest,id:any):
    asset = Asset.objects.filter(id=int(id)).exclude(status=4).first()
    if not asset:
        return HttpResponse("资产不存在")
    content = "<h4>基本信息<h4/>"
    content += "资产名称:" + asset.name + '<br/>'
    content += "资产编号:" + str(asset.id) + '<br/>'
    content += "业务实体:" + asset.entity.name + '<br/>'
    content += "所属部门:" + asset.department.name + '<br/>'
    content += "创建时间:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(asset.create_time)) + '<br/>'
    if asset.category:
        content += "资产类别:" + asset.category.name + "(" + ("数量型" if asset.type else "条目型") + ")" + '<br/>'
    else:
        content += "资产类别:" + ("数量型" if asset.type else "条目型") + ",尚未确定具体类别"+ '<br/>'
    if asset.parent:
        content += "上级资产:" + asset.parent.name + '<br/>'
    if asset.belonging:
        content += "挂账人:" + asset.belonging.name + '<br/>'
    
    content += "原市值:" + str(float(asset.price)) + '<br/>'
    content += "描述信息:" + (asset.description if asset.description else "暂无描述") + '<br/>'
    addition = json.loads(asset.additional)
    if addition:
        for key in addition:
            content += "%s:%s" % (key,addition[key])  + '<br/>'
    content += "<h4>使用情况<h4/>"
    if asset.expire:
        content += "已报废<br/>"
    elif asset.type:
        content += "总数量:" + str(asset.number) + '<br/>'
        content += "闲置数量:" + str(asset.number_idle) + '<br/>'
        content += "清退数量:" + str(asset.number_expire) + '<br/>'
        usage = json.loads(asset.usage)
        maintain = json.loads(asset.maintain)
        process = json.loads(asset.process)
        if usage:
            content += "<h5>使用<h5/>"
            for user in usage:
                content += "%s:%d" % (list(user.keys())[0],user[list(user.keys())[0]]) + '<br/>'
        if maintain:
            content += "<h5>维保<h5/>"
            for user in maintain:
                content += "%s:%d" % (list(user.keys())[0],user[list(user.keys())[0]]) + '<br/>'
        if process:
            content += "<h5>入库审批<h5/>"
            for user in process:
                content += "%s:%d" % (list(user.keys())[0],user[list(user.keys())[0]]) + '<br/>'
    else:
        content += "使用者:" + (asset.user.name if asset.user else "无") + '<br/>'
        content += "状态:" + ("闲置" if asset.status == 0 else ("使用" if asset.status == 1 else("维保" if asset.status == 2 else ("清退") if asset.status == 3 else ("废弃") if asset.status == 4 else "入库审批"))) + '<br/>'
    logs = list(AssetLog.objects.filter(asset=asset).all().order_by("-time"))[0:30:]
    content += "<h4>调动历史<h4/>"
    for log in logs:
        if log.type == 1:
            if log.src:
                content += "用户%s从外部门获取,数量:%d" % (log.src.name,log.number) + ",时间:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(asset.create_time)) + '<br/>'
            else:
                content += "资产管理员导入,数量:%d" % log.number + ",时间:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(asset.create_time)) + '<br/>'
        if log.type == 2:
            content += "用户%s领用,数量:%d" % (log.src.name,log.number) + ",时间:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(asset.create_time)) + '<br/>'
        if log.type == 3:
            content += "用户%s向用户%s转移,数量:%d" % (log.src.name,log.dest.name,log.number) + ",时间:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(asset.create_time)) + '<br/>'
        if log.type == 4:
            content += "用户%s维保,数量:%d" % (log.src.name,log.number) + ",时间:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(asset.create_time)) + '<br/>'
        if log.type == 5:
            content += "用户%s维保完成,数量:%d" % (log.src.name,log.number) + ",时间:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(asset.create_time)) + '<br/>'
        if log.type == 6:
            content += "用户%s退库,数量:%d" % (log.src.name,log.number) + ",时间:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(asset.create_time)) + '<br/>'
        if log.type == 7:
            content += "用户%s向外部门用户%s转移,数量:%d" % (log.src.name,log.dest.name,log.number) + ",时间:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(asset.create_time)) + '<br/>'
    return HttpResponse(content)