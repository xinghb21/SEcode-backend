import datetime as dt
import time

# 单位为秒
def get_timestamp():
    return (dt.datetime.now()).timestamp()

def get_time():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

# cyh 冗余代码
# sessionID的过期日期，也就是创建日期加上两天
def get_expire_date():
    return dt.datetime.now() + dt.timedelta(hours=24 * 2)
# cyh