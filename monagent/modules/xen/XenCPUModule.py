from time import sleep, time
import os

from monagent.modules.mon_module import MonModule
from monagent.utils.XenBroker import XenBrokerException, get_total_cpu_usage
import threading
from monagent.utils.utils import threadinglize

metric_list = [
    'cpu_usage',
    'cpu_idle'
]

xm_path = os.environ['xm_path']
xentop_path = os.environ['xentop_path']

class XenCPUModule(MonModule):

    __lock = threading.RLock()

    #def __init__(self):
    #    super(XenCPUModule, self).__init__()
    #    self.metric_init()

    #def metric_init(self):
    #    threadinglize(self._update)()

    #def _update(self):
    #    while True:
    #        try:
    #            XenCPUModule.__lock.acquire()
    #            self._set_report('cpu_usage', get_total_cpu_usage(xm_path, xentop_path), True)
    #            XenCPUModule.__lock.release()
    #        except XenBrokerException, e:
    #            print e
    #            XenCPUModule.__lock.release()
    #            continue
    #        # the function get_total_cpu_usage takes more than 2 
    #        # seconds to run, no need to sleep long
    #        sleep(0)

    def update(self):
        self._set_report('cpu_usage', get_total_cpu_usage(xm_path, xentop_path), True)
        self._update_t = time()

    def get_cpu_usage(self):
        try:
            cpuusage = self._get_report('cpu_usage')
        except KeyError, e:
            #print e
            cpuusage = 0.0
        #return self._get_report('cpu_usage')
        return cpuusage

    def get_cpu_idle(self):
        return 100 - self.get_cpu_usage()

if __name__ == '__main__':
    x = XenCPUModule()
    #x.metric_init()
    import time
    #time.sleep(2)
    while True:
        print x.get_cpu_usage()
        x.update()
        #print x.get_cpu_idle()
        time.sleep(1)
