# cyh
import json
import datetime
import time

from department.models import Entity

from django import db

from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check
from utils.utils_time import get_timestamp

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets

from asynctask.models import Async_import_export_task
from asynctask.task.export import AssetExport, TaskExport
from asynctask.task.oss import get_bucket


class asynctask(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = []
    allowed_identity = []
    
    @Check
    @action(detail=False, methods=['post'], url_path="newouttask")
    def newtask(self, req:Request):
        test = False
        if req.query_params.get("test"):
            test = True
        if req.user.identity != 3:
            raise Failure("您没有权限进行此操作")
        # 获取该资产管理员已有的任务，只保留最新的两条任务
        oldtasks = Async_import_export_task.objects.filter(user=req.user).order_by("-create_time")
        if len(oldtasks) >= 2:
            for i in range(2, len(oldtasks)):
                oldtasks[i].delete()
        et = Entity.objects.filter(id=req.user.entity).first()
        if not et:
            raise Failure("登录用户所在的业务实体不存在")
        now = datetime.datetime.now()
        filepath = now.strftime("%Y/%m/%d/%H:%M:%S/") + "资产导出.xlsx"
        task = Async_import_export_task(name="导出资产列表", entity=et, user=req.user, type=0, file_path=filepath)
        task.save()
        db.close_old_connections()
        p = AssetExport(task.id, test)
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
                "process": task.process,
            }
        )
    @Check
    @action(detail=False, methods=['post'], url_path="restarttask") 
    def restart(self, req:Request):
        test = False
        if req.query_params.get("test"):
            test = True
        id = req.data.get("taskid")
        if not id:
            raise ParamErr("id不能为空")
        task = Async_import_export_task.objects.filter(id=id).first()
        if not task:
            raise Failure("任务不存在")
        task.status = 3
        task.process = 0
        task.save()
        tp = task.type
        db.close_old_connections()
        if tp == 0:
            p = AssetExport(task.id, test)
        elif tp == 1:
            p = TaskExport(task.id, test)
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
    
    def gettask(self, req:Request, ids):
        # print(json.dumps(list(ids)))
        test = False
        if req.query_params.get("test"):
            test = True
        et = Entity.objects.filter(id=req.user.entity).first()
        if not et:
            raise Failure("登录用户所在的业务实体不存在")
        now = datetime.datetime.now()
        filepath = now.strftime("%Y/%m/%d/%H:%M:%S/") + "异步任务导出.xlsx"
        task = Async_import_export_task(name="导出异步任务", entity=et, user=req.user, type=1, file_path=filepath, ids=json.dumps(list(ids)))
        task.save()
        db.close_old_connections()
        p = TaskExport(task.id, test)
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
        et = Entity.objects.filter(id=req.user.entity).first()
        if not et:
            raise Failure("登录用户所在的业务实体不存在")
        return self.gettask(req, Async_import_export_task.objects.filter(entity=et, status=1).values_list("id", flat=True))
            
    @Check
    @action(detail=False, methods=['post'], url_path="getfailed")
    def getfailed(self, req:Request):
        if req.user.identity != 2:
            raise Failure("您没有权限进行此操作")
        et = Entity.objects.filter(id=req.user.entity).first()
        if not et:
            raise Failure("登录用户所在的业务实体不存在")
        return self.gettask(req, Async_import_export_task.objects.filter(entity=et, status=0).values_list("id", flat=True))
    
    def processtask(self,body):
        if "page" in body.keys():
            page = int(body["page"])
        else:
            page = 1
        if "from" in body.keys():
            fromtime = body["from"]
            fromtime = time.strptime(fromtime, "%Y-%m-%d")
            fromtime = time.mktime(fromtime)
        else:
            fromtime = 0
        if "to" in body.keys():
            totime = body["to"]
            totime = time.strptime(totime, "%Y-%m-%d")
            totime = time.mktime(totime)
        else:
            totime = get_timestamp()
        return page,fromtime,totime
    
    @Check
    @action(detail=False, methods=['get'], url_path="esgetalltask")
    def esgetalltask(self, req:Request):
        if req.user.identity != 2:
            raise Failure("您没有权限进行此操作")
        et = Entity.objects.filter(id=req.user.entity).first()
        if not et:
            raise Failure("登录用户所在的业务实体不存在")
        oldtasks = Async_import_export_task.objects.filter(entity=et, finish_time__lt=get_timestamp()-3*24*60*60)
        bucket = get_bucket()
        for task in oldtasks:
            bucket.delete_object(task.file_path)
            task.delete()
        page,fromtime,totime = self.processtask(req.query_params)
        if "person" in req.query_params.keys():
            person = req.query_params["person"]
        else:
            person = ""
        tasks = list(Async_import_export_task.objects.filter(entity=et,create_time__lte=totime,create_time__gte=fromtime,user__name__contains=person).order_by("-create_time"))
        return_list = tasks[10 * page - 10:10 * page:]
        return Response({
            "code": 0,
            "info": [task.respond() for task in return_list],
            "count":len(tasks),
        })
        
    @Check
    @action(detail=False, methods=['get'], url_path="getalivetasks")
    def getalivetasks(self, req:Request):
        if req.user.identity != 2 and req.user.identity != 3:
            raise Failure("您没有权限进行此操作")
        page,fromtime,totime = self.processtask(req.query_params)
        tasks = Async_import_export_task.objects.filter(user=req.user, status__in=[0,1,2,3],create_time__lte=totime,create_time__gte=fromtime).order_by("-create_time")
        return_list = tasks[10 * page - 10:10 * page:]
        return Response({
            "code": 0,
            "info": [task.respond() for task in return_list],
            "count":len(tasks),
        })
    
        
        
        
        
        
    