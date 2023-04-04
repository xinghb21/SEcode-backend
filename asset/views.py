# cyh
import json
import re

from user.models import User
from department.models import Department
from logs.models import Logs
from asset.models import Asset

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
        ret["parent_id"] = object.parent
        if ret["parent_id"] != 0:
            ret["parent"] = Asset.objects.filter(id=ret["parent_id"]).first().name
        else:
            ret["parent"] = ""
        ret["department_id"] = object.department
        ret["department"] = Department.objects.filter(id=ret["department_id"]).first().name
        ret["name"] = object.name
        ret["type"] = object.type
        ret["number"] = object.number
        ret["belonging_id"] = object.belonging
        ret["belonging"] = User.objects.filter(id=ret["belonging_id"]).first()
        ret["price"] = object.price
        ret["description"] = object.description
        ret["additional"] = json.loads(object.additional)
        ret["status"] = object.status
        ret["create_time"] = object.create_time
        ret["life"] = object.life
        
        return ret
    
    @Check
    def get(self, req:Request, format=None):
        object = Asset.objects.all()
        if "id" in req.data:
            id = req.data["id"]
            object = object.filter(id=id)
        if "parent" in req.data:
            parent = req.data["parent"]
            parent = Asset.objects.fi
            object = object.filter(id=id)
        
            
        
    @Check   
    def post(self, req:Request):
        if 'parent' in req.data.keys():
            parent = require(req.data, 'parent', 'int', "Error type of [parent]")
        else:
            parent = 0
        dep = require(req.data, "department", "int", "Missing or error type of [department]")
        name = require(req.data, "name", "string", "Missing or error type of [name]")
        if len(name) > 100:
            raise Failure("名称过长")
        if 'type' in req.data.keys():
            tp = require(req.data, 'type', 'bool', "Error type of [type]")
        else:
            tp = False
        if 'number' in req.data.keys():
            number = require(req.data, 'number', 'int', "Error type of [number]")
            if not tp and number != 1:
                raise Failure("条目型资产的数量应当始终为1")
            if tp and number <= 0:
                raise Failure("数量型资产的数量应当至少为1")
        else:
            if tp:
                raise Failure("定义条目型资产应当提供数量")
            number = 1
        belonging = require(req.data, "belonging", "int", "Missing or error type of [belonging]")
        price = require(req.data, "price", "float", "Missing or error type of [price]")
        life = require(req.data, "life", "int", "Missing or error type of [life]")
        if 'description' in req.data.keys():
            description = require(req.data, 'description', 'string', "Error type of [description]")
        else:
            description = ""
        if "additional" in req.data.keys():
            addi = req.data["additional"]
            if type(addi) is not dict:
                raise Failure("Error type of [additional]")
            additional = json.dumps(addi)
        else:
            additional = json.dumps({})
        
        Asset.objects.create(parent=parent, department=dep, name=name, type=tp, number=number, belonging=belonging, price=price, life=life, description=description, additional=additional)   
        return Response({"code": 0, "detail": "success"})
    
# cyh