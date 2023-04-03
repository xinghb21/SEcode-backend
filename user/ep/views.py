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
from utils.session import SessionAuthentication
from utils.exceptions import Failure, ParamErr

from rest_framework.decorators import action, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
# 资产管理员

class EpViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [GeneralPermission]
    allowed_identity = [EP]
    
    @action(detail=False, methods=['post'])
    def createAsset(self, req:Request):
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
        return Response({"detail": "success"})
    
    
# cyh