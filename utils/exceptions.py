from rest_framework.views import exception_handler
from rest_framework import exceptions, status
from Aplus.settings import DEBUG
from functools import wraps

def handler(e, ctx):
    # print("type is ------", type(e))
    resp = exception_handler(e, ctx)

    if resp is not None:
        if type(e) is exceptions.PermissionDenied:
            # status code is 403
            resp.data["code"] = -5
        elif type(e) is exceptions.AuthenticationFailed:
            # status code is 403
            resp.data["code"] = -4
        elif type(e) is exceptions.MethodNotAllowed:
            # status code is 405
            resp.data["code"] = -3
        elif type(e) is ParamErr:
            # status code is 400
            resp.data["code"] = -2
        elif type(e) is Failure:
            # status code is 400
            resp.data["code"] = -1
        else:
            resp.data["code"] = -100

    return resp

def Check(check_fn):
    @wraps(check_fn)
    def decorated(*args, **kwargs):
        try:
            return check_fn(*args, **kwargs)
        except Exception as e:
            raise Failure(e.args[0])
    return decorated


# 其它错误
class Failure(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "请求失败."
    
    # 在debug=false时也显示错误信息
    def __init__(self, info=""):
        if len(info) != 0:
            self.detail = info

# 参数错误
class ParamErr(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Invalid parameters."
    
    # 在debug=false时也显示错误信息
    def __init__(self, info=""):
        if len(info):
            self.detail += " " + info
