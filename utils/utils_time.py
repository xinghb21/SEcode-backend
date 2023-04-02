import datetime as dt
from user.models import EXPIRE_DAYS

def get_timestamp():
    return (dt.datetime.now()).timestamp()

# cyh
# sessionID的过期日期，也就是创建日期加上两天
def get_expire_date():
    return dt.datetime.now() + dt.timedelta(hours=24 * EXPIRE_DAYS)
# cyh