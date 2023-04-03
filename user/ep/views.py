# cyh
import json
import re

from user.models import User
from department.models import Department
from logs.models import Logs

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
    def define(self, req:Request):
        pass
    
    
    
# cyh