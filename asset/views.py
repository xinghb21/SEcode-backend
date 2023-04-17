# cyh
import json
import re
import time

from user.models import User
from department.models import Department, Entity
from logs.models import Logs
from asset.models import Asset, AssetClass

from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.identity import *
from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import action, throttle_classes, permission_classes
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
            asset = Asset.objects.filter(entity=et, department=dep, name=name).first()
            if not asset:
                return Response({
                    "code": 0,
                    "data": []
                })
            return Response({
                "code": 0,
                "data": [return_field(asset.serialize(), ["name", "description", "category", "type"])]
            })
        asset = Asset.objects.filter(entity=et, department=dep)
        if "parent" in req.query_params.keys():
            parent = require(req.query_params, "parent", "string", "Error type of [parent]")
            parent = Asset.objects.filter(entity=et, department=dep, name=parent).first()
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
            "data": [{"key": ast.id, "name": ast.name, "category": ast.category.name, "description": ast.description, "type": ast.type} for ast in asset] 
        }
        return Response(ret)
    
    @Check
    @action(detail=False, methods=["get"], url_path="getdetail")
    def get_detail(self, req:Request):
        name = require(req.query_params, "name", err_msg="Missing or error type of [name]")
        et = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        asset = Asset.objects.filter(entity=et, department=dep, name=name).first()
        if not asset:
            raise Failure("该资产不存在")
        ret = {
            "code": 0,
            **asset.serialize(),
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
                parent = Asset.objects.filter(entity=entity, department=dep, name=parent_name).first()
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
            if Asset.objects.filter(entity=entity, department=dep, name=name).first():
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
            if "additional" in asset.keys() and asset["additional"] != "" and asset["additional"] != None:
                addi = asset["additional"]
                additional = json.loads(addi)
                if type(additional) is not dict:
                    raise Failure("Error type of [additional]")
                additional = json.dumps(additional)
            else:
                additional = "{}"
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
                                    expire=expire))
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
                                    status=status))
                
        for a in toadd:
            a.save()
            
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
        assets = Asset.objects.filter(entity=et, department=dep, name__in=names)
        for asset in assets:
            asset.delete()
        return Response({"code": 0, "detail": "success"})
  
class assetclass(APIView):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    allowed_identity = [EP]
    
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