import time
#import re
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


    def __init__(self, device='eth0'):
        super(NetModule, self).__init__(device)


    def update(self):
        if self._report.has_key('netdev'):
            self._report['last_netdev'] = self._report['netdev']
            self._report['netdev'] = {}
        
        super(NetModule, self).update()

        rawdata = self._get_rawdata('netdev')
        for k, v in rawdata.iteritems():
            self._set_report(['netdev', k], [int(i) for i in v.split()], True)

        rbi = rbo = rpi = rpo = 0
        report = self._get_report('netdev')
        for k,v in report.iteritems():
            if type(self._device) is str:
                if k == self._device:
            #for i in self._black_list:
                #if re.match(i, k) is not None:
                    #continue
                    rbi = v[0]
                    rpi = v[1]
                    rbo = v[8]
                    rpo = v[9]
                    break
            else:
                if k in self._device:
                    rbi += v[0]
                    rpi += v[1]
                    rbo += v[8]
                    rpo += v[9]
                    
        self._set_report(('netdev', 'realbytesin'), rbi, True)
        self._set_report(('netdev', 'realbytesout'), rbo, True)
        self._set_report(('netdev', 'realpacketsin'), rpi, True)
        self._set_report(('netdev', 'realpacketsout'), rpo, True)

        self._report.setdefault('last_netdev', self._report['netdev'])
        #if not self._report.has_key('last_netdev'):
            #self._report['last_netdev'] = self._report['netdev']


    def _get_time_diff(self):
        ret = super(NetModule, self)._get_time_diff() 
        return ret < 1 and 1 or ret


    def get_bytes_in(self):
        vdiff = self._get_report(('netdev', 'realbytesin')) - \
                self._get_report(('last_netdev', 'realbytesin'))
        if not vdiff > 0:
            return 0
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
        #if tdiff < 1:
            #tdiff = 1
        return int(vdiff / tdiff)


    def get_packets_in(self):
        vdiff = self._get_report(('netdev', 'realpacketsin')) - \
                self._get_report(('last_netdev', 'realpacketsin'))
        if not vdiff > 0:
            return 0
        tdiff = self._get_time_diff()
        #if tdiff < 1:
            #tdiff = 1
        return int(vdiff / tdiff)


    def get_packets_out(self):
        vdiff = self._get_report(('netdev', 'realpacketsout')) - \
                self._get_report(('last_netdev', 'realpacketsout'))
        if not vdiff > 0:
            return 0
        tdiff = self._get_time_diff()
        #if tdiff < 1:
            #tdiff = 1
        return int(vdiff / tdiff)


    def get_device(self):
        if type(self._device) is str:
            return self._device
        else:
            return None


if __name__ == '__main__':
    ins = NetModule()
    #ins = NetModule(['lo', 'bond'])

    while True:
        ins.update()
        val = ins.get_bytes_out()
        if val > 0:
            print val
        time.sleep(0)
