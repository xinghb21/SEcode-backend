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

class asset(APIView):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    allowed_identity = [EP]
    
    def get_object(object:Asset):
        ret = {}
        ret["id"] = object.id
        ret["parent"] = object.parent.name if object.parent else ""
        ret["entity"] = object.entity.name
        ret["category"] = object.category.name
        ret["department"] = object.department.name
        ret["name"] = object.name
        ret["number"] = object.number
        ret["belonging"] = object.belonging.name
        ret["price"] = object.price
        ret["life"] = object.life
        ret["create_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(object.create_time))
        ret["description"] = object.description
        ret["additional"] = json.loads(object.additional)
        ret["status"] = object.status
        
        return ret
    
    @Check
    def get(self, req:Request, format=None):
        object = Asset.objects.all()
        if "id" in req.query_params:
            id = require(req.query_params, "id", "int", "Error type of [id]")
            object = object.filter(id=id)
            objects = [self.get_object(obj) for obj in object]
            return objects
        if "entity" in req.query_params:
            entity_name = require(req.query_params, "entity", "string", "Error type of [entity]")
            entity = Entity.objects.filter(name=entity_name).first()
            if not entity:
                raise Failure("所提供的业务实体不存在")
            object = object.filter(entity=entity)
            if "parent" in req.query_params:
                parent = require(req.query_params, "parent", "string", "Error type of [parent]")
                parent = Asset.objects.filter(name=parent).first()
                if not parent:
                    raise Failure("所提供的上级资产不存在")
                object = object.filter(parent=parent)
        else:
            if "parent" in req.query_params:
                raise Failure("提供了上级资产，却没有指定业务实体")
        if "category" in req.query_params:
            cate = require(req.query_params, "category", err_msg="Error type of [category]")
            cate = AssetClass.objects.filter(name=cate).first()
            if not cate:
                raise Failure("所提供的资产类型不存在")
            object = object.filter(category=cate)
        if "department" in req.query_params:
            dep = require(req.query_params, "department", err_msg="Error type of [department]")
            dep = Department.objects.filter(name=dep).first()
            if not dep:
                raise Failure("所提供的部门不存在")
            object = object.filter(department=dep)
        if "name" in req.query_params:
            name = require(req.query_params, "name", err_msg="Error type of [name]")
            object = object.filter(name=name)
        if "belonging" in req.query_params:
            user = require(req.query_params, "belonging", err_msg="Error type of [belonging]")
            user = User.objects.filter(name=user).first()
            if not user:
                raise Failure("所提供的挂账人不存在")
            object = object.filter(user=user)
        if "from" in req.query_params:
            from_ = require(req.query_params, "from", "float", err_msg="Error type of [from]")
            object = object.filter(from__gte=from_)
        if "to" in req.query_params:
            to_ = require(req.query_params, "to", "float", err_msg="Error type of [to]")
            object = object.filter(to__lte=to_)
        if "status" in req.query_params:
            status = require(req.query_params, "status", "int", err_msg="Error type of [status]")
            object = object.filter(status=status)
        return Response(object)
        
               
    @Check   
    def post(self, req:Request):
        if 'parent' in req.data.keys():
            parent = require(req.data, 'parent', 'string', "Error type of [parent]")
            parent = Asset.objects.filter(name=parent).first()
            if not parent:
                raise Failure("上级资产不存在")
        else:
            parent = None
        entity = require(req.data, "entity", "string", "Missing or error type of [entity]")
        entity = Entity.objects.filter(name=entity).first()
        if not entity:
            raise Failure("所属业务实体不存在")
        category = require(req.data, "category", "string", "Missing or error type of [category]")
        category = AssetClass.objects.filter(name=category).first()
        if not category:
            raise Failure("该资产类型不存在")
        dep = require(req.data, "department", "string", "Missing or error type of [department]")
        dep = Department.objects.filter(entity=entity.id, name=dep).first()
        if not dep:
            raise Failure("所属部门不存在")
        name = require(req.data, "name", "string", "Missing or error type of [name]")
        if len(name) > 128:
            raise Failure("名称过长")
        if Asset.objects.filter(name=name).first():
            raise Failure("名称重复")
        tp = category.type
        if tp == True:
            number = require(req.data, "number", "int", "Missing or error type of [number]")
            if number < 0:
                raise Failure("数量不能为负数")
        else:
            number = 1
        if "belonging" in req.data.keys():
            belonging = require(req.data, "belonging", "string", "Missing or error type of [belonging]")
            user = User.objects.filter(name=belonging).first()
            if not user:
                raise Failure("挂账人不存在")
        else:
            user = req.user
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
            additional = json.dumps(addi)
            if type(additional) is not dict:
                raise Failure("Error type of [additional]")
        else:
            additional = json.dumps({})
        
        Asset.objects.create(parent=parent, department=dep, name=name, type=tp, number=number, belonging=belonging, price=price, life=life, description=description, additional=additional)   
        return Response({"code": 0, "detail": "success"})
    
# cyh