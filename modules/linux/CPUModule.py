import sys
import os
from mon_module import MonModule

metric_list = [
    'cpu_user', 
    'cpu_nice', 
    'cpu_system', 
    'cpu_idle', 
    'cpu_usage',
    'cpu_iowait',
    'cpu_irq', 
    'cpu_softirq'
]

class CPUModule(MonModule):

    data_sources = [{  
                        'name'  :   'stat',
                        'path'  :   '/proc/stat',
                        'type'  :   'list',
                    }]

    def update(self):
        if self.info.has_key('stat'):
            self.info['last_stat'] = self.info['stat']
            self.info['stat'] = {}

        super(CPUModule, self).update()
        
        self.info['stat']['cpu'] = self.get_val('stat')[0].split()[1:]
        totalTime = 0
        alist = self.info['stat']['cpu']
        for elem in alist:
            totalTime += int(elem)
        self.info['stat']['cpu_total_jiffies'] = totalTime
        
        if not self.info.has_key('last_stat'):  # first run
            self.info['last_stat'] = self.info['stat']

        self.total_jiffies_diff = self.info['stat']['cpu_total_jiffies'] - \
                self.info['last_stat']['cpu_total_jiffies']

    def get_cpu_total_jiffies(self):
        return self.info['stat']['cpu_total_jiffies']

    def get_cpu_use_jiffies(self):
        alist = self.info['stat']['cpu']
        useTime = self.info['stat']['cpu_total_jiffies'] - int(alist[3])
        return useTime

    def get_cpu_user_jiffies(self):
        return self.info['stat']['cpu'][0]

    def get_cpu_nice_jiffies(self):
        return self.info['stat']['cpu'][1]

    def get_cpu_system_jiffies(self):
        return self.info['stat']['cpu'][2]

    def get_cpu_idle_jiffies(self):
        return self.info['stat']['cpu'][3]

    def get_cpu_iowait_jiffies(self):
        return self.info['stat']['cpu'][4]

    def get_cpu_irq_jiffies(self):
        return self.info['stat']['cpu'][5]

    def get_cpu_softirq_jiffies(self):
        return self.info['stat']['cpu'][6]

    def get_cpu_user(self):
        diff = float(self.info['stat']['cpu'][0]) - \
                     float(self.info['last_stat']['cpu'][0])
        if self.total_jiffies_diff > 0:
            return round((diff / self.total_jiffies_diff) * 100, 1)
        else:
            return 0.0

    def get_cpu_nice(self):
        diff = float(self.info['stat']['cpu'][1]) - \
                     float(self.info['last_stat']['cpu'][1])
        if self.total_jiffies_diff > 0:
            return round((diff / self.total_jiffies_diff) * 100, 1)
        else:
            return 0.0

    def get_cpu_system(self):
        diff = float(self.info['stat']['cpu'][2]) - \
                     float(self.info['last_stat']['cpu'][2])
        if self.total_jiffies_diff > 0:
            return round((diff / self.total_jiffies_diff) * 100, 1)
        else:
            return 0.0
        
    def get_cpu_idle(self):
        diff = float(self.info['stat']['cpu'][3]) - \
                     float(self.info['last_stat']['cpu'][3])
        if self.total_jiffies_diff > 0:
            return round((diff / self.total_jiffies_diff) * 100, 1)
        else:
            return 0.0

    def get_cpu_usage(self):
        if self.total_jiffies_diff > 0:
            return 100 - self.get_cpu_idle()
        else:
            return 0.0
 
    def get_cpu_iowait(self):
        diff = float(self.info['stat']['cpu'][4]) - \
                     float(self.info['last_stat']['cpu'][4])
        if self.total_jiffies_diff > 0:
            return round((diff / self.total_jiffies_diff) * 100, 1)
        else:
            return 0.0

    def get_cpu_irq(self):
        diff = float(self.info['stat']['cpu'][5]) - \
                     float(self.info['last_stat']['cpu'][5])
        if self.total_jiffies_diff > 0:
            return round((diff / self.total_jiffies_diff) * 100, 1)
        else:
            return 0.0
        
    def get_cpu_softirq(self):
        diff = float(self.info['stat']['cpu'][6]) - \
                     float(self.info['last_stat']['cpu'][6])
        if self.total_jiffies_diff > 0:
            return round((diff / self.total_jiffies_diff) * 100, 1)
        else:
            return 0.0


if __name__=="__main__":
    cmm = CPUModule()
    #print cmm.info
    #print '================================================================'
    #print 'cpu total jiffies : %d' % cmm.metric_handler('cpu_total_jiffies')
    #print 'cpu use jiffies : %d' % cmm.metric_handler('cpu_use_jiffies')
    #print cmm.get_cpu_idle()
    #print cmm.get_cpu_usage()
    import time
    #time.sleep(1)
    #cmm.update()
    #print cmm.get_cpu_idle()
    #print cmm.get_cpu_usage()
    while True:
        cmm.update()
        print cmm.metric_handler('cpu_usage')
        time.sleep(1)
