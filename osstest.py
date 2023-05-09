import os
import datetime
from multiprocessing import Process

class sleep(Process):
     def __init__(self):
          super().__init__()
          
     def run(self):
          print("sleep")
          print("inside pid is", self.pid)
          os.system("sleep 10")
          print("wake up")
     
p = sleep()
p.start()
print(p.pid)
def get_pid(pid):
     print(pid)
     
     return pid
p2 = Process(target=get_pid, args=(p.pid,))
p2.start()