# cyh
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.exceptions import PermissionDenied

class GeneralPermission(BasePermission):
    def has_permission(self, req: Request, view):
        # 如果没有定义允许的身份，则默认为不限制身份
        try:
            allowed:list = view.allowed_identity
        except AttributeError:
            return True
        if len(allowed) == 0:
            return True
        if not req.user:
            return False
        if req.user.identity in allowed:
            return True
        else:
            return False
# cyh
