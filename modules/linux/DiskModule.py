import time
import copy

from mon_module import *

metric_list = [
    'rps',
    'wps',
    'rrqmps',
    'wrqmps',
    'rsecps',
    'wsecps',
    'rkbps',
    'wkbps',
    'util',
    'await',
    'avgrq_sz',
    'avgqu_sz'
]

class DiskModule(MonModule):

    data_source = '/sys/block/%s/stat'

    rels = ('reads', 'rd_mrg', 'rd_sectors', 'ms_reading', 'writes', 'wr_mrg', 
         'wr_sectors', 'ms_writing', 'cur_ios', 'ms_doing_io', 'ms_weighted')

    sec_sz = 0.5

    def metric_init(self):
        f = open('/proc/partitions')
        f.readline()
        f.readline()
        self.data_source = self.data_source % (f.readline().strip().split()[-1])
        f.close()
        self.set_val('diskstats', dict.fromkeys(self.rels, 0), True)
        #self.set_val('last_diskstats', {}, True)
        super(DiskModule, self).metric_init()

    def update(self):
        #my_deep_copy(self.info['diskstats'], self.info['last_diskstats'])
        self.info['last_diskstats'] = copy.deepcopy(self.info['diskstats'])

        f = open(self.data_source)
        now = time.time()
        stats = f.read().strip().split()
        #print stats
        f.close()
        self.set_timestamp('diskstats', now)

        i = 0
        for k in self.rels:
            self.info['diskstats']['val'][k] = int(stats[i])
            i += 1
            
    def _get_metric_diff(self, key):
        return self.get_val(('diskstats', key)) - \
            self.get_val(('last_diskstats', key))

    def _get_time_diff(self):
        try:
            return self.get_timestamp('diskstats') - \
                self.get_timestamp('last_diskstats')
        except KeyError, e:
            #print e
            f = open('/proc/uptime')
            tdiff = float(f.read().split()[0])
            f.close()
            return tdiff

    def metric_handler(self, metric):
        try:
            return super(DiskModule, self).metric_handler(metric)
        except ZeroDivisionError, e:
            #print e, metric
            return 0

    def get_rps(self):
        return self._get_metric_diff('reads') / self._get_time_diff()

    def get_wps(self):
        return self._get_metric_diff('writes') / self._get_time_diff()

    def get_rrqmps(self):
        return self._get_metric_diff('rd_mrg') / self._get_time_diff()

    def get_wrqmps(self):
        return self._get_metric_diff('wr_mrg') / self._get_time_diff()

    def get_rsecps(self):
        return self._get_metric_diff('rd_sectors') / self._get_time_diff()

    def get_wsecps(self):
        return self._get_metric_diff('wr_sectors') / self._get_time_diff()
        
    def get_rkbps(self):
        return self.get_rsecps() * self.sec_sz

    def get_wkbps(self):
        return self.get_wsecps() * self.sec_sz

    def get_util(self):
        #return (self._get_metric_diff('ms_reading') + 
                #self._get_metric_diff('ms_writing')) / \
                #self._get_time_diff() / 10
        u = self._get_metric_diff('ms_doing_io') / self._get_time_diff() / 10
        #if u > 100:
            #import pdb; pdb.set_trace()
        return u

    def get_await(self):
        return float(self._get_metric_diff('ms_reading') + 
                self._get_metric_diff('ms_writing')) / \
                (self._get_metric_diff('reads') + 
                 self._get_metric_diff('writes'))

    def get_avgrq_sz(self):
        return float(self._get_metric_diff('rd_sectors') + 
                self._get_metric_diff('wr_sectors')) /\
                (self._get_metric_diff('reads') +
                 self._get_metric_diff('writes'))

    def get_avgqu_sz(self):
        return self._get_metric_diff('ms_weighted') / self._get_time_diff() / 1000

if __name__ == '__main__':
    ins = DiskModule()
    rels = ('Device:', 'rrqm/s', 'wrqm/s', 'r/s', 'w/s', 'rkB/s', 'wkB/s', 'avgrq-sz', 'avgqu-sz', 'await', '%util')
    m = ('rrqmps', 'wrqmps', 'rps', 'wps', 'rkbps', 'wkbps', 'avgrq_sz', 'avgqu_sz', 'await', 'util')
    caption = ('%-9s' +'%9s' * 10) % rels

    while True:
        print
        print caption
        print ('%-9s' + '%9.2f' * 10) % tuple([ins.data_source.split('/')[-2]] + [ins.metric_handler(i) for i in m])
        #print ins.info
        #print '%.2f' % ins.metric_handler('util')
        time.sleep(5)
        ins.update()
