from functools import wraps
from feishu.models import EventException

def CatchException(check_fn):
    @wraps(check_fn)
    def decorated(*args, **kwargs):
        try:
            return check_fn(*args, **kwargs)
        except Exception as e:
            EventException.objects.create(event=e.args[0], msg=e.args[1])
            return None
    return decorated