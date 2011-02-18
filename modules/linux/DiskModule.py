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

    partitionfile = '/proc/partitions'
    statsfile = '/proc/diskstats'

    rels = ('reads', 'rd_mrg', 'rd_sectors', 'ms_reading', 'writes', 'wr_mrg', 
         'wr_sectors', 'ms_writing', 'cur_ios', 'ms_doing_io', 'ms_weighted')

    sector_size = 0.5

    def __init__(self, enabled_devices=None):
        self.enabled_devices = enabled_devices
        super(DiskModule, self).__init__()


    def filter_func(self, dev):
        return self.enabled_devices is None or dev[2] in self.enabled_devices


    def update(self):
        if self._report.has_key('diskstats'):
            self._report['last_diskstats'] = copy.deepcopy(self._report['diskstats'])

        with open(self.statsfile) as f:
            self.rawdata = filter(self.filter_func, [line.split() for line in f])
            now = time.time()
            if self._report.has_key('diskstats'):
                self._t_diff = now - self.get_update_time()
            else:
                with open('/proc/uptime') as upf:
                    self._t_diff = float(upf.read().split()[0])
            self._update_t = now

        for l in self.rawdata:
            i = 3
            for k in self.rels:
                #if l[0] not in valid_partmajors:
                    #continue
                self._set_report(('diskstats', l[2], k), int(l[i]), True)
                i += 1
            
        if self.enabled_devices is None:
            self.enabled_devices = self._get_report('diskstats').keys()


    def _get_stats_diff(self, devname, stats):
        try:
            last = self._get_report(('last_diskstats', devname, stats))
        except KeyError:
            last = 0
        finally:
            return self._get_report(('diskstats', devname, stats)) - last


    def _metric_handler(self, devname, metric):
        try:
            return super(DiskModule, self).metric_handler(metric, devname)
        except ZeroDivisionError, e:
            #print e, metric
            return 0


    def metric_handler(self, metric, devlist=None):
        if devlist is None:
            devlist = self.enabled_devices

        if type(devlist) is str:
            return self._metric_handler(devlist, metric)
        else:
            ret = {}
            for dev in devlist:
                ret[dev] = self._metric_handler(dev, metric)
            return ret


    def get_rps(self, devname):
        return self._get_stats_diff(devname, 'reads') / self._get_time_diff()

    def get_wps(self, devname):
        return self._get_stats_diff(devname, 'writes') / self._get_time_diff()

    def get_rrqmps(self, devname):
        return self._get_stats_diff(devname, 'rd_mrg') / self._get_time_diff()

    def get_wrqmps(self, devname):
        return self._get_stats_diff(devname, 'wr_mrg') / self._get_time_diff()

    def get_rsecps(self, devname):
        return self._get_stats_diff(devname, 'rd_sectors') / self._get_time_diff()

    def get_wsecps(self, devname):
        return self._get_stats_diff(devname, 'wr_sectors') / self._get_time_diff()
        
    def get_rkbps(self, devname):
        return self.get_rsecps(devname) * self.sector_size

    def get_wkbps(self, devname):
        return self.get_wsecps(devname) * self.sector_size

    def get_util(self, devname):
        #return (self._get_stats_diff('ms_reading') + 
                #self._get_stats_diff('ms_writing')) / \
                #self._get_time_diff() / 10
        u = self._get_stats_diff(devname, 'ms_doing_io') / self._get_time_diff() / 10
        #if u > 100:
            #import pdb; pdb.set_trace()
        return u

    def get_await(self, devname):
        return float(self._get_stats_diff(devname, 'ms_reading') + 
                self._get_stats_diff(devname, 'ms_writing')) / \
                (self._get_stats_diff(devname, 'reads') + 
                 self._get_stats_diff(devname, 'writes'))

    def get_avgrq_sz(self, devname):
        return float(self._get_stats_diff(devname, 'rd_sectors') + 
                self._get_stats_diff(devname, 'wr_sectors')) /\
                (self._get_stats_diff(devname, 'reads') +
                 self._get_stats_diff(devname, 'writes'))

    def get_avgqu_sz(self, devname):
        return self._get_stats_diff(devname, 'ms_weighted') / self._get_time_diff() / 1000


if __name__ == '__main__':
    ins = DiskModule(('sda', 'sdb'))
    rels = ('Device:', 'rrqm/s', 'wrqm/s', 'r/s', 'w/s', 'rkB/s', 'wkB/s', 'avgrq-sz', 'avgqu-sz', 'await', '%util')
    m = ('rrqmps', 'wrqmps', 'rps', 'wps', 'rkbps', 'wkbps', 'avgrq_sz', 'avgqu_sz', 'await', 'util')
    caption = ('%-9s' +'%9s' * 10) % rels

    #print ins.metric_handler('rrqmps')
    while True:
        print
        print caption
        #print ('%-9s' + '%9.2f' * 10) % tuple([ins.data_source.split('/')[-2]] + [ins.metric_handler(i) for i in m])
        for d in ('sda', 'sdb'):
            print ('%-9s' + '%9.2f' * 10) % tuple([d] + [ins.metric_handler(i, d) for i in m])
        #print ins.info
        #print '%.2f' % ins.metric_handler('util')
        time.sleep(5)
        ins.update()
