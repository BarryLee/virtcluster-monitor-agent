from mon_module import MonModule
import XenbakedModule

metric_list = [
    'cpu_usage',
    'cpu_idle'
]

class XenCPUModule(MonModule):

    def __init__(self):
        self.xenbakedModuleIns = XenbakedModule.instance()

    def update(self):
        self.xenbakedModuleIns.update()

    def get_cpu_idle(self):
        return self.xenbakedModuleIns.get_overall_cpu_idle()

    def get_cpu_usage(self):
        return 100 - self.get_cpu_idle()
