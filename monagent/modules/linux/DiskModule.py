import time
import copy
import os
import sys

from mon_module import *

sys.path.append(current_dir(parent_dir(__file__)))
from utils.block import *

metric_list = [
    'rps',
    'wps',
    'rrqmps',
    'wrqmps',
    'rsecps',
    'wsecps',
    'rkBps',
    'wkBps',
    'util',
    'await',
    'avgrq_sz',
    'avgqu_sz'
]

class DiskModule(MonModule):

    block_dir = '/sys/block'
    statsfile = block_dir + '/%s/stat'

    rels = ('reads', 'rd_mrg', 'rd_sectors', 'ms_reading', 'writes', 'wr_mrg', 
         'wr_sectors', 'ms_writing', 'cur_ios', 'ms_doing_io', 'ms_weighted')

    sec_sz = 0.5

    def __init__(self, device):
        if os.path.exists(self.statsfile % device):
            self.statsfile = self.statsfile % device
        else:
            self.statsfile = self.statsfile % \
                    (get_partition_disk()[device] + '/' + device)
        self._device = device
        self._report = {}
        self._t_diff = 0
        self._update_t = 0
        self.metric_init()


    def metric_init(self):
        #self.set_val('diskstats', dict.fromkeys(self.rels, 0), True)
        self._report['diskstats'] = list([0] * 11)
        #self.set_val('last_diskstats', {}, True)
        super(DiskModule, self).metric_init()


    def update(self):
        #my_deep_copy(self.info['diskstats'], self.info['last_diskstats'])
        self._report['last_diskstats'] = copy.deepcopy(self._report['diskstats'])

        f = open(self.statsfile)
        now = time.time()
        self._report['diskstats'] = map(lambda x: int(x), f.read().split())
        #stats = f.read().strip().split()
        #print stats
        f.close()
        if self._update_t == 0:
            self._t_diff = float(open('/proc/uptime').read().split()[0])
        else:
            self._t_diff = now - self._update_t
        self._update_t = now

        #i = 0
        #for k in self.rels:
            #self.info['diskstats']['val'][k] = int(stats[i])
            #i += 1


    def _get_stats_diff(self, index):
        return self._report['diskstats'][index] - \
                self._report['last_diskstats'][index]


    def metric_handler(self, metric):
        try:
            return super(DiskModule, self).metric_handler(metric)
        except ZeroDivisionError, e:
            #print e, metric
            return 0


    def get_rps(self):
        return self._get_stats_diff(0) / self._t_diff


    def get_rrqmps(self):
        return self._get_stats_diff(1) / self._t_diff


    def get_wps(self):
        return self._get_stats_diff(4) / self._t_diff


    def get_wrqmps(self):
        return self._get_stats_diff(5) / self._t_diff


    def get_rsecps(self):
        return self._get_stats_diff(2) / self._t_diff

    def get_wsecps(self):
        return self._get_stats_diff(6) / self._t_diff
        
    def get_rkBps(self):
        return self.get_rsecps() * self.sec_sz

    def get_wkBps(self):
        return self.get_wsecps() * self.sec_sz

    def get_util(self):
        #return (self._get_stats_diff(3) + 
                #self._get_stats_diff(7)) / \
                #self._t_diff / 10
        u = self._get_stats_diff(9) / self._t_diff / 10
        #if u > 100:
            #import pdb; pdb.set_trace()
        return u

    def get_await(self):
        return float(self._get_stats_diff(3) + 
                self._get_stats_diff(7)) / \
                (self._get_stats_diff(0) + 
                 self._get_stats_diff(4))

    def get_avgrq_sz(self):
        return float(self._get_stats_diff(2) + 
                self._get_stats_diff(6)) /\
                (self._get_stats_diff(0) +
                 self._get_stats_diff(4))

    def get_avgqu_sz(self):
        return self._get_stats_diff(10) / self._t_diff / 1000

if __name__ == '__main__':
    ins_a = DiskModule('sda')
    ins_b = DiskModule('sdb')
    rels = ('Device:', 'rrqm/s', 'wrqm/s', 'r/s', 'w/s', 'rkB/s', 'wkB/s', 'avgrq-sz', 'avgqu-sz', 'await', '%util')
    m = ('rrqmps', 'wrqmps', 'rps', 'wps', 'rkBps', 'wkBps', 'avgrq_sz', 'avgqu_sz', 'await', 'util')
    caption = ('%-9s' +'%9s' * 10) % rels

    while True:
        print
        print caption
        print ('%-9s' + '%9.2f' * 10) % tuple([ins_a._device] + [ins_a.metric_handler(i) for i in m])
        print ('%-9s' + '%9.2f' * 10) % tuple([ins_b._device] + [ins_b.metric_handler(i) for i in m])
        #print ins.info
        #print '%.2f' % ins.metric_handler('util')
        time.sleep(5)
        ins_a.update()
        ins_b.update()
