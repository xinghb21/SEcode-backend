import oss2

# oss
AccessKeyId = 'LTAI5tCj3A8UM1Lhoo5Frcmh'
AccessSecret = 'UWGiKrBHzUaXUKnSEQOSci18rwn2YG'
endpoint = 'https://oss-cn-beijing.aliyuncs.com'
def get_bucket():
    auth = oss2.Auth(AccessKeyId, AccessSecret)
    bucket = oss2.Bucket(auth, endpoint, 'asynctask')
    return bucket