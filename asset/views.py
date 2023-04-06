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
    
    @Check
    @action(detail=False, methods=["get"], url_path="get")
    def get_by_condition(self, req:Request):
        et = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        asset = Asset.objects.filter(entity=et, department=dep)
        # if "entity" in req.query_params:
        #     entity_name = require(req.query_params, "entity", "string", "Error type of [entity]")
        #     entity = Entity.objects.filter(name=entity_name).first()
        #     if not entity:
        #         raise Failure("所提供的业务实体不存在")
        #     object = object.filter(entity=entity)
        if "parent" in req.query_params:
            parent = require(req.query_params, "parent", "string", "Error type of [parent]")
            parent = Asset.objects.filter(entity=et, department=dep, name=parent).first()
            if not parent:
                raise Failure("所提供的上级资产不存在")
            asset = asset.filter(parent=parent)
        # else:
        #     if "parent" in req.query_params:
        #         raise Failure("提供了上级资产，却没有指定业务实体")
        if "category" in req.query_params:
            cate = require(req.query_params, "category", err_msg="Error type of [category]")
            cate = AssetClass.objects.filter(entity=et, department=dep, name=cate).first()
            if not cate:
                raise Failure("所提供的资产类型不存在")
            asset = asset.filter(category=cate)
        # if "department" in req.query_params:
        #     dep = require(req.query_params, "department", err_msg="Error type of [department]")
        #     dep = Department.objects.filter(name=dep).first()
        #     if not dep:
        #         raise Failure("所提供的部门不存在")
        #     object = object.filter(department=dep)
        if "name" in req.query_params:
            name = require(req.query_params, "name", err_msg="Error type of [name]")
            asset = asset.filter(name=name)
        # 按挂账人进行查询还需要讨论一下，比如一个部门下的资产的挂账人除了资产管理员还可以是谁
        # if "belonging" in req.query_params:
        #     user = require(req.query_params, "belonging", err_msg="Error type of [belonging]")
        #     user = User.objects.filter(name=user).first()
        #     if not user:
        #         raise Failure("所提供的挂账人不存在")
        #     object = object.filter(user=user)
        if "from" in req.query_params:
            from_ = require(req.query_params, "from", "float", err_msg="Error type of [from]")
            asset = asset.filter(from__gte=from_)
        if "to" in req.query_params:
            to_ = require(req.query_params, "to", "float", err_msg="Error type of [to]")
            asset = asset.filter(to__lte=to_)
        # 资产使用者只能是本部门下的吗？
        if "user" in req.query_params:
            user = require(req.query_params, "user", err_msg="Error type of [user]")
            user = User.objects.filter(name=user).first()
            if not user:
                raise Failure("所提供的使用者不存在")
            asset = asset.filter(user=user)
        if "status" in req.query_params:
            status = require(req.query_params, "status", "int", err_msg="Error type of [status]")
            asset = asset.filter(status=status)
        return Response([return_field(["name", "description", "number_idle", "category"], ast.serialize()) if ast.type else return_field(["name", "description", "status", "category"], ast.serialize()) for ast in asset])
    
    @Check
    @action(detail=False, methods=["get"], url_path="getdetail")
    def get_detail(self, req:Request):
        name = require(req.query_params, "name", err_msg="Missing or error type of [name]")
        et = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        asset = Asset.objects.filter(entity=et, department=dep, name=name).first()
        return Response(asset.serialize())    
               
    @Check   
    def post(self, req:Request):
        entity = Entity.objects.filter(id=req.user.entity).first()
        dep = Department.objects.filter(id=req.user.department).first()
        if 'parent' in req.data.keys():
            parent = require(req.data, 'parent', 'string', "Error type of [parent]")
            parent = Asset.objects.filter(entity=entity, department=dep, name=parent).first()
            if not parent:
                raise Failure("上级资产不存在")
        else:
            parent = None
        category = require(req.data, "category", "string", "Missing or error type of [category]")
        category = AssetClass.objects.filter(entity=entity, department=dep, name=category).first()
        if not category:
            raise Failure("该资产类型不存在")
        tp = category.type
        name = require(req.data, "name", "string", "Missing or error type of [name]")
        if len(name) > 128:
            raise Failure("名称过长")
        if Asset.objects.filter(entity=entity, department=dep, name=name).first():
            raise Failure("名称重复")
        tp = category.type
        if "belonging" in req.data.keys():
            belonging = require(req.data, "belonging", "string", "Missing or error type of [belonging]")
            belonging = User.objects.filter(entity=entity.id, department=dep.id, name=belonging).first()
            if not belonging:
                raise Failure("挂账人不存在或不在部门中")
        else:
            belonging = req.user
        price = require(req.data, "price", "float", "Missing or error type of [price]")
        if "life" in req.data.keys():
            life = require(req.data, "life", "int", "error type of [life]")
            if life < 0:
                raise Failure("使用年限不能为负数")
        else:
            life = 0
        if 'description' in req.data.keys():
            description = require(req.data, 'description', 'string', "Error type of [description]")
        else:
            description = ""
        if "additional" in req.data.keys():
            addi = req.data["additional"]
            additional = json.loads(addi)
            if type(additional) is not dict:
                raise Failure("Error type of [additional]")
            additional = json.dumps(additional)
        else:
            additional = "{}"
            
        if tp == True:
            number = require(req.data, "number", "int", "Missing or error type of [number]")
            if number < 0:
                raise Failure("数量不能为负数")
            number_idle = number
            usage = "[]"
            maintain = "[]"
            number_expire = 0
            expire = False
            Asset.objects.create(parent=parent, 
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
                                 expire=expire)
        else:
            user = None
            status = 0
            Asset.objects.create(parent=parent, 
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
                                 status=status)
          
        return Response({"code": 0, "detail": "success"})
  
  
class assetclass(APIView):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    allowed_identity = [EP]
    
    @Check
    def post(self, req:Request):
        if "parent" in req.data:
            parent = require(req.data, "parent", err_msg="Error type of [parent]")
            parent = AssetClass.objects.filter(name=parent).first()
            if not parent:
                raise Failure("父类别不存在")
        else:
            parent = None
        dep = Department.objects.filter(id=req.user.department).first()
        name = require(req.data, "name", err_msg="Error type of [name]")
        if len(name) > 128:
            raise Failure("名称过长")
        if AssetClass.objects.filter(department=dep, name=name).first():
            raise Failure("存在重名类别")
        tp = require(req.data, "type", "bool", err_msg="Error type of [type]")
        AssetClass.objects.create(parent=parent, department=dep, name=name, type=tp)
        return Response({"code": 0, "detail": "success"})
    
    # 返回该部门下的类别层级树
    # @Check
    # def get(self, req:Request):
        
        


# cyh