import os

from monagent.modules.linux.MemModule import MemModule
from monagent.utils.XenBroker import get_mem_total, get_mem_free, get_total_domU_memory

metric_list = [
    #'mem_total',
    'mem_usage',
    #'cached',
    #'mem_free',
    'mem_used',
    #'buffers',
    #'swap_total',
    #'swap_cached',
    #'swap_free',
    #'mem_available'
]

xm_path = os.environ['xm_path']
xentop_path = os.environ['xentop_path']

class XenMemModule(MemModule):

    def __init__(self):
        super(XenMemModule, self).__init__()
        self.mem_total = get_mem_total(xm_path, xentop_path)

    def get_mem_used(self):
        return super(XenMemModule, self).get_mem_used() + \
                get_total_domU_memory(xm_path, xentop_path)

    def get_mem_available(self):
        return get_mem_free(xm_path, xentop_path)

    def get_mem_usage(self):
        return self.get_mem_used() * 100.0 / self.mem_total


if __name__ == '__main__':
    ins = XenMemModule()
    import time
    while True:
        ins.update() 
        print ins.get_mem_used(), ins.get_mem_usage(), ins.get_mem_available()
        time.sleep(1)
