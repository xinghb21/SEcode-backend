# cyh
import json
import datetime

from department.models import Entity

from django import db

from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets

from asynctask.models import Async_import_export_task
from asynctask.task.export import AssetExport, TaskExport


class asynctask(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = []
    allowed_identity = []
    
    @Check
    @action(detail=False, methods=['post'], url_path="newouttask")
    def newtask(self, req:Request):
        if req.user.identity != 3:
            raise Failure("您没有权限进行此操作")
        et = Entity.objects.filter(id=req.user.entity).first()
        if not et:
            raise Failure("登录用户所在的业务实体不存在")
        now = datetime.datetime.now()
        filepath = now.strftime("%Y/%m/%d/%H:%M:%S/") + "资产导出.xlsx"
        db.close_old_connections()
        p = AssetExport()
        task = Async_import_export_task(name="导出资产列表", entity=et, user=req.user, type=0, file_path=filepath, pid=p.pid)
        task.save()
        db.close_old_connections()
        p.start()
        return Response(
            {
                "code": 0,
                "info": {
                    "id": task.id,
                    "person": task.user.name if task.user else "",
                    "type": task.type,
                    "time": task.create_time,
                    "state": task.status,
                    "fileurl": filepath,
                }
            }
        )
    
    @Check
    @action(detail=False, methods=['post'], url_path="getprocess")
    def getprocess(self, req:Request):
        id = req.data.get("taskid")
        if not id:
            raise ParamErr("id不能为空")
        task = Async_import_export_task.objects.filter(id=id).first()
        if not task:
            raise Failure("任务不存在")
        return Response(
            {
                "code": 0,
                "process": task.process
            }
        )
    @Check
    @action(detail=False, methods=['post'], url_path="restarttask") 
    def restart(self, req:Request):
        id = req.data.get("taskid")
        if not id:
            raise ParamErr("id不能为空")
        task = Async_import_export_task.objects.filter(id=id).first()
        if not task:
            raise Failure("任务不存在")
        tp = task.type
        db.close_old_connections()
        if tp == 0:
            p = AssetExport()
        elif tp == 1:
            p = TaskExport()
        task.pid = p.pid
        task.status = 3
        task.process = 0
        task.save()
        db.close_old_connections()
        p.start()
        return Response(
            {
                "code": 0,
                "info": {
                    "id": task.id,
                    "person": task.user.name if task.user else "",
                    "type": task.type,
                    "time": task.create_time,
                    "state": task.status,
                    "fileurl": task.file_path,
                }
            }
        )
    
    def gettask(self, req, ids):
        et = Entity.objects.filter(id=req.user.entity).first()
        if not et:
            raise Failure("登录用户所在的业务实体不存在")
        now = datetime.datetime.now()
        filepath = now.strftime("%Y/%m/%d/%H:%M:%S/") + "异步任务导出.xlsx"
        db.close_old_connections()
        p = TaskExport()
        task = Async_import_export_task(name="导出异步任务", entity=et, user=req.user, type=1, file_path=filepath, pid=p.pid, ids=json.dumps(ids))
        task.save()
        db.close_old_connections()
        p.start()
        return Response(
            {
                "code": 0,
                "info": {
                    "id": task.id,
                    "person": task.user.name if task.user else "",
                    "type": task.type,
                    "time": task.create_time,
                    "state": task.status,
                    "fileurl": filepath,
                }
            }
        )
        
    @Check
    @action(detail=False, methods=['post'], url_path="getsuccess")
    def getsuccess(self, req:Request):
        if req.user.identity != 2:
            raise Failure("您没有权限进行此操作")
        return self.gettask(req, Async_import_export_task.objects.filter(status=1).values_list("id", flat=True))
            
    @Check
    @action(detail=False, methods=['post'], url_path="getfailed")
    def getfailed(self, req:Request):
        if req.user.identity != 2:
            raise Failure("您没有权限进行此操作")
        return self.gettask(req, Async_import_export_task.objects.filter(status=0).values_list("id", flat=True))
    
    @Check
    @action(detail=False, methods=['post'], url_path="esgetalltask")
    def esgetalltask(self, req:Request):
        if req.user.identity != 2:
            raise Failure("您没有权限进行此操作")
        et = Entity.objects.filter(id=req.user.entity).first()
        if not et:
            raise Failure("登录用户所在的业务实体不存在")
        tasks = Async_import_export_task.objects.filter(entity=et).order_by("-create_time")
        return Response({
            "code": 0,
            "info": [task.respond() for task in tasks]
        })
        
    @Check
    @action(detail=False, methods=['post'], url_path="getalivetasks")
    def getalivetasks(self, req:Request):
        if req.user.identity != 2 or req.user.identity != 3:
            raise Failure("您没有权限进行此操作")
        tasks = Async_import_export_task.objects.filter(user=req.user, status=2).order_by("-create_time")
        return Response({
            "code": 0,
            "info": [task.respond() for task in tasks]
        })
    
        
        
        
        
        
    