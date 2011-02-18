import time
import re
from mon_module import MonModule


metric_list = [
    'bytes_in',
    'bytes_out',
    'packets_in',
    'packets_out'
]

class NetModule(MonModule):

    data_sources = [{
        'name'  :   'netdev',
        'path'  :   '/proc/net/dev',
        'type'  :   'dict'
    }]


    def __init__(self, black_list=[]):
        self._black_list = black_list
        super(NetModule, self).__init__()

    def update(self):
        if self._report.has_key('netdev'):
            self._report['last_netdev'] = self._report['netdev']
            self._report['netdev'] = {}
        
        super(NetModule, self).update()

        rawdata = self._get_rawdata('netdev')
        for k, v in rawdata.items():
            self._set_report(['netdev', k], [int(i) for i in v.split()], True)

        rbi = rbo = rpi = rpo = 0
        report = self._get_report('netdev')
        for k,v in report.items():
            for i in self._black_list:
                if re.match(i, k) is not None:
                    continue
            rbi += v[0]
            rpi += v[1]
            rbo += v[8]
            rpo += v[9]

        self._set_report(('netdev', 'realbytesin'), rbi, True)
        self._set_report(('netdev', 'realbytesout'), rbo, True)
        self._set_report(('netdev', 'realpacketsin'), rpi, True)
        self._set_report(('netdev', 'realpacketsout'), rpo, True)

        if not self._report.has_key('last_netdev'):
            self._report['last_netdev'] = self._report['netdev']


    def _get_time_diff(self):
        ret = super(NetModule, self)._get_time_diff() 
        return ret < 1 and 1 or ret


    def get_bytes_in(self):
        vdiff = self._get_report(('netdev', 'realbytesin')) - \
                self._get_report(('last_netdev', 'realbytesin'))
        if not vdiff > 0:
            return 0
        #tdiff = self.get_timestamp('netdev') - self.get_timestamp('last_netdev')
        tdiff = self._get_time_diff()
        #if tdiff < 1:
            #tdiff = 1
        return int(vdiff / tdiff)

    def get_bytes_out(self):
        vdiff = self._get_report(('netdev', 'realbytesout')) - \
                self._get_report(('last_netdev', 'realbytesout'))
        if not vdiff > 0:
            return 0
        tdiff = self._get_time_diff()
        #tdiff = self.get_timestamp('netdev') - self.get_timestamp('last_netdev')
        #if tdiff < 1:
            #tdiff = 1
        return int(vdiff / tdiff)

    def get_packets_in(self):
        vdiff = self._get_report(('netdev', 'realpacketsin')) - \
                self._get_report(('last_netdev', 'realpacketsin'))
        if not vdiff > 0:
            return 0
        tdiff = self._get_time_diff()
        #tdiff = self.get_timestamp('netdev') - self.get_timestamp('last_netdev')
        #if tdiff < 1:
            #tdiff = 1
        return int(vdiff / tdiff)

    def get_packets_out(self):
        vdiff = self._get_report(('netdev', 'realpacketsout')) - \
                self._get_report(('last_netdev', 'realpacketsout'))
        if not vdiff > 0:
            return 0
        tdiff = self._get_time_diff()
        #tdiff = self.get_timestamp('netdev') - self.get_timestamp('last_netdev')
        #if tdiff < 1:
            #tdiff = 1
        return int(vdiff / tdiff)

if __name__ == '__main__':
    ins = NetModule(['lo', 'bond'])

    while True:
        ins.update()
        val = ins.get_bytes_out()
        if val > 0:
            print val
        time.sleep(0)
