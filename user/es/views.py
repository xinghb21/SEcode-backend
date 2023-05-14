# cyh
import json
import re

from django.contrib.auth.hashers import make_password

from user.models import User
from department.models import Department,Entity
from asset.models import Asset
from logs.models import Logs
from pending.models import Pending
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.identity import *
from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import action, throttle_classes, permission_classes, authentication_classes, api_view
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
    # 查看业务实体下的所有用户
    @Check
    @action(detail=False, methods=['get'], url_path="checkall")
    def check_all(self, req:Request):
        et = req.user.entity
        users = User.objects.filter(entity=et).exclude(identity=2)
        ret = []
        for user in users:
            tmp = return_field(user.serialize(), ["id", "name", "entity","identity", "lockedapp", "locked"])
            entity = user.entity
            entity = Entity.objects.filter(id=entity).first().name
            dep = user.department
            if dep != 0:
                dep = Department.objects.filter(id=dep).first().name
            else:
                dep = ""
            tmp["entity"] = entity
            tmp["department"] = dep
            if(user.identity != 2):
                ret.append(tmp)
        ret_with_code = {
            "code": 0,
            "data": ret
        }
        return Response(ret_with_code)
    
    @Check
    @action(detail=False, methods=['delete'])
    def batchdelete(self, req:Request):
        if "names" not in req.data:
            raise Failure("Missing [names]")
        names = req.data["names"]
        if type(names) is not list:
            raise Failure("Error type of [names]")
        users = User.objects.filter(entity=req.user.entity, name__in=names)
        for user in users:
            if user.identity == 3:
                dep = Department.objects.filter(id=user.department).first()
                if not dep:
                    raise Failure("资产管理员"+user.name+"所属的部门不存在")
                dep.admin = 0
                dep.save()
            user.delete()
            
        return Response({"code": 0, "detail": "success"})
    

    # 企业系统管理员查看企业用户
    @Check
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
        
        ret = {
            "code": 0,
            "name": user.name,
            "entity": et_name,
            "department": dep_name,
            "locked": user.locked,
            "identity": user.identity,
            "lockedapp": user.lockedapp,
        }
        
        return Response(ret)
    
    #能否转移或改变职务
    def havetask(self,user):
        ent = Entity.objects.filter(id=user.entity).first()
        dep = Department.objects.filter(id=user.department).first()
        if user.identity == 3:
            pendings = Pending.objects.filter(entity=ent.id,department=dep.id,result=0).all()
            maintain = Pending.objects.filter(entity=ent.id,department=dep.id,type=3).exclude(result=3).all()
            if pendings or maintain:
                return False
        if user.identity == 4:
            if user.hasasset > 0:
                return False
        return True
    
    # 更改员工的部门
    @Check
    @action(detail=False, methods=['post'])
    def alter(self, req:Request):
        user = self.get_target_user(req)
        if not self.havetask(user):
            if user.identity == 3:
                raise Failure("此管理员存在未完成待办项")
            else:
                raise Failure("此员工名下仍有资产")
        new_name = require(req.data, "department", "string", "Missing or error type of [department]")
        if not new_name:
            raise Failure("新部门名称不能为空")
        olddep = Department.objects.filter(id = user.department).first()
        dep = Department.objects.filter(name=new_name).first()
        if not dep:
            raise Failure("新部门不存在")
        if dep.admin != 0 and user.identity == 3:
            raise Failure("该部门已存在资产管理员")
        if user.identity == 3:
            olddep.admin = 0
            dep.admin = user.id
            olddep.save()
            dep.save()
        user.department = dep.id
        user.save()
        Logs(entity=user.entity,content="用户"+user.name+"部门从"+olddep.name+"变更为"+dep.name,type=3).save()
        ret = {
            "code": 0,
            "name": user.name,
            "old_department": olddep.name,
            "new_department": new_name,
        }
        return Response(ret)
    
    @Check
    @action(detail=False, methods=['post'])
    def lock(self, req:Request):
        user = self.get_target_user(req)
        
        if user.locked:
            return Response({"code": 0, "detail": "用户已经处于锁定状态"})
        else:
            user.locked = True
            user.save()
            Logs(entity=user.entity,content="锁定用户"+user.name,type=3).save()
            return Response({"code": 0, "detail": "成功锁定用户"})
    
    @Check   
    @action(detail=False, methods=['post'])
    def unlock(self, req:Request):
        user = self.get_target_user(req)
        if not user.locked:
            return Response({"code": 0, "detail": "用户未处于锁定状态"})
        else:
            user.locked = False
            user.save()
            Logs(entity=user.entity,content="解锁用户"+user.name,type=3).save()
            return Response({"code": 0, "detail": "成功解锁用户"})
    
    # 用于匹配app列表的正则表达式
    re_app = r"^[01]{9}$"
    
    @Check
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
            "detail": "成功更改用户应用"
        }
        return Response(ret)
    @Check
    @action(detail=False, methods=['post'])
    def reset(self, req:Request):
        user = self.get_target_user(req)
        new_pw = require(req.data, "newpassword", err_msg="Missing or error type of [newpassword]")
        user.password = make_password(new_pw)
        user.save()
        return Response({"code": 0, "detail": "success"})
    
    
    #hyx
    
    #创建部门
    @Check
    @action(detail=False,methods=['post'])
    def createdepart(self,req:Request):
        entname = require(req.data,"entity","string",err_msg="Missing or error type of [entity]")
        depname = require(req.data,"depname","string",err_msg="Missing or error type of [depname]")
        parentname = require(req.data,"parent","string",err_msg="Missing or error type of [parent]")
        ent = Entity.objects.filter(name=entname).first()
        if not ent:
            raise Failure("业务实体不存在")
        havedp = Department.objects.filter(entity=ent.id,name=depname).first()
        if havedp:
            raise Failure("部门已存在")
        if depname == entname:
            raise Failure("部门名称不可与业务实体名称相同")
        if req.user.id != ent.admin:
            raise Failure("无权创建部门")
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
        Logs(entity=ent.id,content="创建部门"+depname,type=2).save()
        return Response(ret)
    
    #递归删除部门
    def layerdelete(self,dep):
        children = Department.objects.filter(parent=dep.id).all()
        if children:
            for child in children:
                self.layerdelete(child)
        assets = Asset.objects.filter(department=dep.id).all()
        for asset in assets:
            asset.delete()
        staffs = User.objects.filter(department=dep.id).all()
        for staff in staffs:
            staff.delete()
        dep.delete()
    
    #删除部门，下属所有内容均删除
    @Check
    @action(detail=False,methods=['delete'])
    def deletedepart(self,req:Request):
        depname = require(req.data,"name","string",err_msg="Missing or error type of [depname]")
        ent = Entity.objects.filter(admin=req.user.id).first()
        dep = Department.objects.filter(entity=ent.id,name=depname).first()
        if not dep:
            raise Failure("该部门不存在")
        Logs(entity=ent.id,content="删除部门"+depname+"及其下属部门",type=2).save()
        self.layerdelete(dep)
        ret = {
            "code" : 0,
            "name" : depname
        }
        return Response(ret)
    
    #递归构造部门树存储
    @Check
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
    @Check
    @action(detail=False,methods=['get'])
    def departs(self,req:Request):
        if req.user.identity != 2:
            raise Failure("此用户无权查看部门结构")
        ent = Entity.objects.filter(admin=req.user.id).first()
        if not ent:
            raise Failure("业务实体不存在")
        ret = {
            "code" : 0,
            "info" : {ent.name:self.tree(ent.id,0)}
        }
        return Response(ret)
    
    #修改部门名称
    @Check
    @action(detail=False,methods=['POST'])
    def renamedepart(self,req:Request):
        oldname = require(req.data,"oldname","string",err_msg="Missing or error type of [oldname]")
        newname = require(req.data,"newname","string",err_msg="Missing or error type of [newname]")
        ent = Entity.objects.filter(admin=req.user.id).first()
        dep = Department.objects.filter(entity=ent.id,name=oldname).first()
        dep2 = Department.objects.filter(entity=ent.id,name=newname).first()
        if newname == ent.name:
            raise Failure("新名称不可与业务实体名相同")
        if not dep:
            raise Failure("待修改部门不存在")
        if dep2:
            raise Failure("新名称部门已存在")
        dep.name=newname
        dep.save()
        Logs(entity=ent.id,content="将部门"+oldname+"名称修改为"+newname,type=2).save()
        ret = {
            "code" : 0,
            "oldname" : oldname,
            "newname" : newname
        }
        return Response(ret)
    
    #获取所有部门员工
    @Check
    @action(detail=False,methods=['GET'])
    def staffs(self,req:Request):
        if req.user.identity != 2:
            raise Failure("此用户无权查看部门员工")
        ent = Entity.objects.filter(admin=req.user.id).first()
        if not ent:
            raise Failure("业务实体不存在")
        deps = Department.objects.filter(entity=ent.id).all()
        info = {}
        for dep in deps:
            staffs = User.objects.filter(entity=ent.id,department=dep.id,identity=4).all()
            info.update({dep.name:[staff.name for staff in staffs]})
        ret = {
            "code" : 0,
            "info" : info
        }
        return Response(ret)

    @Check
    @action(detail=False, methods=["delete"], url_path="deletealldeparts")
    def batch_delete(self, req:Request):
        if type(req.data) is not list:
            raise Failure("请求参数格式错误")
        names = req.data
        Department.objects.filter(entity=req.user.entity, name__in=names).delete()
        return Response({
            "code": 0,
            "detail": "success",
        })
        
    @Check
    @action(detail=False, methods=['post'])
    def searchuser(self, req:Request):
        users = User.objects.filter(entity=req.user.entity)
        if "username" in req.data.keys() and req.data["username"] != "":
            name = require(req.data, "username", err_msg="Error type of [username]")
            users = users.filter(name=name)
        if "department" in req.data.keys() and req.data["department"] != "":
            name = require(req.data, "department", err_msg="Error type of [department]")
            dep = Department.objects.filter(entity=req.user.entity, name=name).first()
            users = users.filter(department=dep.id)
        if "identity" in req.data.keys():
            id = require(req.data, "identity", "int", "Error type of [identity]")
            if id == 3 or id == 4:
                users = users.filter(identity=id)
        ret =[]
        for user in users:
            tmp = return_field(user.serialize(), ["id", "name","department", "entity","identity", "lockedapp", "locked", "apps"])
            entity = user.entity
            entity = Entity.objects.filter(id=entity).first().name
            dep = user.department
            if dep != 0:
                dep = Department.objects.filter(id=dep).first().name
            else:
                dep = ""
            tmp["entity"] = entity
            tmp["department"] = dep
            if(user.identity != 2):
                ret.append(tmp)
        return Response({
                "code": 0,
                "data": ret
            })
        
    @Check
    @action(detail=False, methods=['post'])
    def changeidentity(self, req:Request):
        name = require(req.data, "name", err_msg="Missing or Error type of [name]")
        new_id = require(req.data, "new", "int", err_msg="Missing or Error type of [new]")
        depart = require(req.data, "department", err_msg="Missing or Error type of [department]")
        entityname = require(req.data, "entity", err_msg="Missing or Error type of [entity]") 
        entity=Entity.objects.filter(name=entityname).first()
        dep = Department.objects.filter(name=depart).first()
        if new_id != 3 and new_id != 4:
            raise Failure("传入的新身份不合法")
        user = User.objects.filter(department= dep.id, entity=entity.id, name=name).first()
        if not user:
            raise Failure("该用户不存在")
        if not self.havetask(user):
            if user.identity == 3:
                raise Failure("此管理员存在未完成待办项")
            else:
                raise Failure("此员工名下仍有资产")
        if new_id == 3:
            if dep.admin != 0:
                raise Failure("该部门下已经有资产管理员")
            user.identity = 3
            user.lockedapp = "000001110"
            user.save()
            dep.admin = user.id
            dep.save()
            Logs(entity=entity.id,content="员工"+user.name+"升职为部门"+dep.name+"的资产管理员",type=3).save()
        else:
            if user.identity == 3:
                dep.admin = 0
                dep.save()
                user.identity = 4
                user.lockedapp = "000000001"
                user.save()
                Logs(entity=entity.id,content="部门"+dep.name+"的资产管理员"+user.name+"降职为员工",type=3).save()
        return Response({
            "code": 0,
            "detail": "success"
        })
    
    #hyx 2023.4.15
    #增加用户应用
    @Check
    @action(detail=False,methods=["post"])
    def addapp(self,req:Request):
        username = require(req.data, "username", err_msg="Missing or Error type of [username]")
        # print(req.data['appadded'])
        appadded = require(req.data, "appadded", "list", err_msg="Missing or Error type of [appadded]")
        ent = req.user.entity
        user = User.objects.filter(name=username).first()
        if not user or user.entity != ent:
            raise Failure("此用户不存在")
        if user.identity != 3 and user.identity != 4:
            raise Failure("此用户不是资产管理员或员工")
        if not user.apps:
            user.apps = json.dumps({"data":[]})
        oldapps = json.loads(user.apps)
        oldlist = oldapps["data"]
        for item in appadded:
            needupdate = True
            for i in oldlist:
                if item["name"] == i["name"]:
                    i["urlvalue"] = item["urlvalue"]
                    needupdate = False
                    break
            if needupdate:
                oldlist.append(item)
        user.apps = json.dumps({"data":oldlist})
        user.save()
        return Response({
            "code": 0,
            "info": "success"
        })
        
    #删除用户应用
    @Check
    @action(detail=False,methods=["delete"])
    def deleteapps(self,req:Request):
        username = require(req.data, "username", err_msg="Missing or Error type of [username]")
        appdeleted = require(req.data, "appdeleted", "list",err_msg="Missing or Error type of [appdeleted]")
        ent = req.user.entity
        user = User.objects.filter(name=username).first()
        if not user or user.entity != ent:
            raise Failure("此用户不存在")
        if user.identity != 3 and user.identity != 4:
            raise Failure("此用户不是资产管理员或员工")
        if not user.apps:
            user.apps = json.dumps({"data":[]})
        oldapps = json.loads(user.apps)
        oldlist = oldapps["data"]
        # print(oldlist)
        # print(appdeleted)
        for item in appdeleted:
            for i in oldlist:
                if item == i["name"]:
                    oldlist.remove(i)
                    break
        user.apps = json.dumps({"data":oldlist})
        user.save()
        return Response({
            "code": 0,
            "info": "success"
        })

#获取某个资产管理员或员工应用
    @Check
    @action(detail=False,methods=["get"])
    def getonesapp(self,req:Request):
        username = req.query_params["name"]
        admin = req.user
        user = User.objects.filter(name=username).first()
        if not user or admin.entity != user.entity:
            raise Failure("该用户不在业务实体内")
        apps = json.loads(user.apps)
        return Response({"code": 0,"info": apps["data"]})

#获取操作日志
    @Check
    @action(detail=False,methods=['get'])
    def getlogs(self,req:Request):
        page = int(req.query_params["page"])
        logs = list(Logs.objects.filter(entity=req.user.entity).all().order_by("-time"))
        if len(logs) > 1000:
            delete_logs = logs[1000:len(logs):]
            for i in delete_logs:
                i.delete()
        return_list = logs[10 * page - 10:10 * page:]
        return Response({"code": 0,"info": [{"id":item.id,"type":item.type,"content":item.content,"time":item.time} for item in return_list],"count":len(logs)})
