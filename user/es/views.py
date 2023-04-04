# cyh
import json
import re

from django.contrib.auth.hashers import make_password

from user.models import User
from department.models import Department,Entity
from logs.models import Logs
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.identity import *
from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr

from rest_framework.decorators import action, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
# 企业系统管理员

class EsViewSet(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = [GeneralPermission]
    
    allowed_identity = [ES]
    
    # 获得被操作的用户
    def get_target_user(self, req:Request):
        if req._request.method == "GET":
            name = require(req.query_params, "name", err_msg="Missing or error type of [name]")
        else:
            name = require(req.data, "name", err_msg="Missing or error type of [name]")
        user = User.objects.filter(name=name).first()
        if not user:
            raise Failure("被查询的用户不存在")
        if user.identity == 1:
            raise Failure("系统管理员无权操作超级管理员")
        if user.identity == 2:
            raise Failure("系统管理员无权操作系统管理员")
        if user.entity != req.user.entity:
            raise Failure("系统管理员无权操作其它业务实体的用户")
        return user

    # 企业系统管理员查看企业用户
    @action(detail=False, methods=['get'])
    def check(self, req:Request):
        
        user = self.get_target_user(req)
        if user.entity == 0:
            et_name = ""
        else:
            et = Entity.objects.filter(id=user.entity).first()
            if not et:
                raise Failure("被操作的用户的业务实体不存在")
            et_name = et.name
        
        if user.department == 0:
            dep_name = ""
        else:
            dep = Department.objects.filter(id=user.department).first()
            if not dep:
                raise Failure("被操作的用户的部门不存在")
            dep_name = dep.name
        if user.identity == 3:
            id_name = "资产管理员"
        else:
            id_name = "员工"
        
        ret = {
            "code": 0,
            "name": user.name,
            "entity": et_name,
            "department": dep_name,
            "locked": user.locked,
            "identity": id_name,
            "lockedapp": user.lockedapp,
        }
        
        return Response(ret)
    
    # 更改员工的部门
    @action(detail=False, methods=['post'])
    def alter(self, req:Request):
        user = self.get_target_user(req)
        # department
        old_dep = user.department
        if old_dep == 0:
            old_name = ""
        else:
            old_name = Department.objects.filter(id = old_dep).first().name
        new_name = require(req.data, "department", "string", "Missing or error type of [department]")
        if len(new_name) == 0:
            user.department = 0
            user.save()
        else:
            dep = Department.objects.filter(name=new_name).first()
            if not dep:
                raise Failure("新部门不存在")
            user.department = dep.id
            user.save()
        ret = {
            "code": 0,
            "name": user.name,
            "old_department": old_name,
            "new_department": new_name,
        }
        return Response(ret)
        
    @action(detail=False, methods=['post'])
    def lock(self, req:Request):
        user = self.get_target_user(req)
        
        if user.locked:
            return Response({"code": 0, "detail": "用户已经处于锁定状态"})
        else:
            user.locked = True
            return Response({"code": 0, "detail": "成功锁定用户"})
        
    @action(detail=False, methods=['post'])
    def unlock(self, req:Request):
        user = self.get_target_user(req)
        if not user.locked:
            return Response({"code": 0, "detail": "用户未处于锁定状态"})
        else:
            user.locked = False
            return Response({"code": 0, "detail": "成功解锁用户"})
    
    # 用于匹配app列表的正则表达式
    re_app = r"^[01]{9}$"
    
    @action(detail=False, methods=['post'])
    def apps(self, req:Request):
        user = self.get_target_user(req)
        new_app = require(req.data, "newapp", err_msg="Missing or error type of [newapp]")
        if not re.match(self.re_app, new_app):
            raise ParamErr("Error format of new app list")
        old_app = user.lockedapp
        user.lockedapp = new_app
        user.save()
        ret = {
            "code": 0,
            "new_app": new_app,
            "old_app": old_app,
        }
        return Response(ret)

    @action(detail=False, methods=['post'])
    def reset(self, req:Request):
        user = self.get_target_user(req)
        new_pw = require(req.data, "newpassword", err_msg="Missing or error type of [newpassword]")
        user.password = make_password(new_pw)
        user.save()
        return Response({"code": 0})
    
    
    #hyx
    #创建部门
    @action(detail=False,methods=['post'])
    def createdepart(self,req:Request):
        entname = require(req.data,"entity","string",err_msg="Missing or error type of [entity]")
        depname = require(req.data,"depname","string",err_msg="Missing or error type of [depname]")
        parentname = require(req.data,"parent","string",err_msg="Missing or error type of [parent]")
        ent = Entity.objects.filter(name=entname).first()
        if not ent:
            raise Failure("业务实体不存在")
        if not parentname:
            newdepart = Department(name=depname,entity=ent.id)
            newdepart.save()
        else:
            parent = Department.objects.filter(name=parentname,entity=ent.id).first()
            if not parent:
                raise Failure("上属部门不存在")
            newdepart2 = Department(name=depname,entity=ent.id,parent=parent.id)
            newdepart2.save()
        ret = {
            "code" : 0,
            "name" : depname
        }
        return Response(ret)
    
    #递归构造部门树存储
    def tree(self,ent,parent):
        roots = Department.objects.filter(entity=ent,parent=parent).all()
        #递归基
        if not roots:
            return "$"
        else:
            res = {}
            for root in roots:
                res.update({root.name:self.tree(ent,root.id)})
            return res
    
    #查看部门树
    @action(detail=False,methods=['get'])
    def departs(self,req:Request):
        if req.user.identity != 2:
            raise Failure("此用户无权查看部门结构")
        ent = Entity.objects.filter(admin=self.user.id).first()
        if not ent:
            raise Failure("业务实体不存在")
        ret = {
            "code" : 0,
            "info" : self.tree(ent.id,0)
        }
        return Response(ret)