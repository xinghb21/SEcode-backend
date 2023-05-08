# cyh
import json
import re
import time
import requests
import hashlib

from django.contrib.auth.hashers import make_password, check_password

from user.models import User
from department.models import Department, Entity
from logs.models import Logs
from asset.models import Asset, AssetClass

from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp
from utils.identity import *
from utils.permission import GeneralPermission
from utils.session import LoginAuthentication
from utils.exceptions import Failure, ParamErr, Check

from rest_framework.decorators import authentication_classes as auth
from rest_framework.decorators import action, throttle_classes, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import viewsets
from rest_framework.views import APIView
from utils.decipher import AESCipher

from asynctask.models import Async_import_export_task

class asynctask(viewsets.ViewSet):
    authentication_classes = [LoginAuthentication]
    permission_classes = []
    allowed_identity = []
    
    @Check
    @action(detail=False, methods=['post'], url_path="newouttask")
    def newtask(self, req:Request):
        if req.user.identity != 3:
            raise Failure("您没有权限进行此操作")
        
    