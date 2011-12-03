import time
import threading

import Xenbakedfront
from mon_module import MonModule

_lockForInstanceCreation = threading.RLock()

def instance():
    """Singleton constructor. Use this instead of the class constructor.
    """
    _lockForInstanceCreation.acquire()
    global inst
    try:
        inst
    except:
        inst = XenbakedModule()
    _lockForInstanceCreation.release()
    return inst

class XenbakedModule(MonModule):

    __lock = threading.RLock()

    __update_interval = 1

    def __init__(self):
        self.last_update = 0
        super(XenbakedModule, self).__init__()
        
    def metric_init(self):
        self.start_xenbaked()
        self.update()
        
    def __del__(self):
        self.stop_xenbaked()

    def start_xenbaked(self):
        Xenbakedfront.start_xenbaked()
    
    def stop_xenbaked(self):
        Xenbakedfront.stop_xenbaked()

    def update(self):
        XenbakedModule.__lock.acquire()
        if time.time() - self.last_update < self.__update_interval:
            #return self.get_val('xenbaked')
            pass
        else:
            self.set_val('xenbaked', Xenbakedfront.update(), True)
            self.set_timestamp('xenbaked', time.time())
            self.last_update = self.get_timestamp('xenbaked')
        XenbakedModule.__lock.release()

    def get_overall_cpu_idle(self):    # average idle pct on multi-processors
        ret = 0.0
        allinfo = self.get_val('xenbaked')
        ncpu = len(allinfo)
        for i in range(ncpu):
            for dom in range(0, Xenbakedfront.NDOMAINS):
                if Xenbakedfront.domain_id[dom] != -1:
                    continue

                [h, l, f] = allinfo[i]
                ret += h[dom][0][1]

        return ret / ncpu

