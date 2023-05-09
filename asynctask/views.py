# cyh
import json
import datetime

from user.models import User
from department.models import Department, Entity
from logs.models import Logs
from asset.models import Asset, AssetClass

from django import db

from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets

from asynctask.models import Async_import_export_task
from asynctask.task.export import AssetExport


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
        p = AssetExport(req.user)
        task = Async_import_export_task(name="导出资产列表", entity=et, user=req.user, type=1, file_path=filepath, pid=p.pid)
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
        
        
        
        
    