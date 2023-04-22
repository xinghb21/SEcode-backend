# cyh
import requests
import json

from feishu.views import APP_ID, APP_SECRET
from utils.exceptions import Failure
from utils.utils_time import get_timestamp

# 租户访问凭证
TENANT_ACCESS_TOKEN = ""
# tenant_access_token 的过期时间，单位为秒
TENANT_EXPIRE = -1
# 上一个凭证的获取时间
access_time = get_timestamp()

def get_tenant_token():
    now = get_timestamp()
    global TENANT_ACCESS_TOKEN, TENANT_EXPIRE, access_time
    if TENANT_EXPIRE != -1 and access_time + TENANT_EXPIRE - 10 > now and now > access_time:
        return TENANT_ACCESS_TOKEN
    resp = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                  params={
                      "app_id": APP_ID,
                      "app_secret": APP_SECRET,
                },
                  headers={
                      "Content-Type": "application/json; charset=utf-8",
                  })
    res = resp.json()
    if res["code"] != 0:
        raise Failure(res["msg"])
    TENANT_ACCESS_TOKEN = res["tenant_access_token"]
    TENANT_EXPIRE = res["expire"]
    access_time = now
    return TENANT_ACCESS_TOKEN
    
    

