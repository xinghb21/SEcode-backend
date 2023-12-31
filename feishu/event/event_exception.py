from functools import wraps
from feishu.models import EventException, Event

def CatchException(check_fn):
    @wraps(check_fn)
    def decorated(*args, **kwargs):
        try:
            return check_fn(*args, **kwargs)
        except Exception as e:
            if type(e.args[0]) == Event:
                print(e.args[1])
                EventException.objects.create(event=e.args[0], msg=e.args[1])
            else:
                print(e.args[0])
                EventException.objects.create(msg=e.args[0])
            return None
    return decorated