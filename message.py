import requests
import datetime as dt
import json

ENCRYPT_KEY = "uJHwvC9MR6OL2m2gonsWadkVBdrqF1tN"
APP_ID = "cli_a4b17e84d0f8900e"
APP_SECRET = "bMrD4Rtx85VS0jiPhPgThdrohZTHR4Jo"
VERIFICATION_TOKEN = "AOKjmM7RLNEw9pPck9zyNcF7KvshqL4F"

content = "{\"text\": \"账号: username\\n密码: password\"}"

def get_timestamp():
    return (dt.datetime.now()).timestamp()
# 租户访问凭证
TENANT_ACCESS_TOKEN = ""
# tenant_access_token 的过期时间，单位为秒
TENANT_EXPIRE = -1
# 上一个凭证的获取时间
access_time = get_timestamp()

def get_tenant_token_test():
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
        raise Exception(res["msg"])
    TENANT_ACCESS_TOKEN = res["tenant_access_token"]
    TENANT_EXPIRE = res["expire"]
    access_time = now
    return TENANT_ACCESS_TOKEN
    

# r = requests.post("https://open.feishu.cn/open-apis/im/v1/messages",
#                             data={
#                                 "receive_id": "ou_929358b9d66157f63c7429377a137d66",
#                                 "msg_type": "text",
#                                 "content": "{\"text\": \"账号: abab\\n密码: cdcd\"}",
#                                 "uuid": "a0d69e20-1dd1-458b-k525-dfeca4015224"
#                             },
#                             headers={
#                                 "Authorization": "Bearer "+get_tenant_token_test(),
#                                 "content-type": "application/json; charset=utf-8",
#                             },
#                             params={
#                                 "receive_id_type": "open_id"
#                             }
#                             )

# print(r.json())
def send():
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    params = {"receive_id_type":"union_id"}
    msg = "text content"
    msgContent = {
        "text": msg,
    }
    req = {
        "receive_id": "on_f6f75bf8348ec96444840ab3f9542791", # chat id
        "msg_type": "text",
        "content": json.dumps(msgContent)
    }
    payload = json.dumps(req)
    headers = {
        'Authorization': 'Bearer ' + get_tenant_token_test(), # your access token
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, params=params, headers=headers, data=payload)
    print(response.headers['X-Tt-Logid']) # for debug or oncall
    print(response.content) # Print Response
if __name__ == '__main__':
    send()