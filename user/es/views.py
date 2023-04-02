# cyh
import json

from user.models import User
from department.models import Department
from logs.models import Logs

from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.identity import *
from utils.permission import GeneralPermission
from utils.session import SessionAuthentication
from utils.exceptions import Failure

from rest_framework.decorators import action, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
# 企业系统管理员

class EsViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [GeneralPermission]
    allowed_identity = [ES]

    # 企业系统管理员查看企业用户
    @action(detail=False, methods=['get'])
    def check(self, req:Request):
        # 被操作的用户
        name = require(req.query_params, "name", err_msg="Missing or error type of [name]")
        user = User.objects.filter(name=name).first()
        if not user:
            raise Failure("被查询的用户不存在")
        if user.identity == 1:
            raise Failure("系统管理员无权操作超级管理员")
        if user.identity == 2:
            raise Failure("系统管理员无权操作系统管理员")
        if user.entity != req.user.entity:
            raise Failure("系统管理员无权操作其它业务实体的用户")
        
        field_list = ["name", "entity", "department", "locked", "identity", "lockedapp"]
        
        return request_success(return_field(user.serialize(), field_list))
    
    # 将已有的员工添加入本企业
    @action(detail=False, methods=['post'])
    def alter(self, req:Request):
        # 被操作的用户
        name = require(req.data, "name", err_msg="Missing or error type of [name]")
        user = User.objects.filter(name=name).first()
        # department
        old_dep = user.department
        dep_index = require(req.data, "department", "int", "Missing or error type of [department]")
        dep = Department.objects.filter(id=dep_index).first()
        if dep_index != 0 and not dep:
            raise Failure("部门不存在")
        user.department = dep_index
        user.save()
        ret = {
            "code": 0,
            "name": user.name,
            "old department": old_dep,
            "new department": dep,
            "info": "转移成功"
        }
        return Response(ret)
        
    # @CheckRequire
    # def reset(req:HttpRequest):
        
        