# cyh
import json
import re
import time

from user.models import User
from department.models import Department, Entity
from logs.models import Logs
from asset.models import Asset, AssetClass

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
from utils.decipher import AESCipher

ENCRYPT_KEY = "fmX6uAwQeQj775zyo5Xt0e603RhBmEOb"

class feishu(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = []
    allowed_identity = []
    
    decipher = AESCipher(ENCRYPT_KEY)
    
    @Check
    @action(detail=False, methods=['post'], url_path="answer")
    def answer_challenge(self, req:Request):
        # challenge = self.decipher.decrypt_string(req.data['encrypt'])
        # print(challenge)
        # challenge = json.loads(challenge)
        # print(challenge)
        return Response({"challenge": req.data["challenge"]})
