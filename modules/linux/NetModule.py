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
        if self.info.has_key('netdev'):
            self.info['last_netdev'] = self.info['netdev']
            self.info['netdev'] = {}
        
        super(NetModule, self).update()

        rawdata = self.get_val('netdev')
        for k,v in rawdata.items():
            self.set_val(['netdev', k], [int(i) for i in v.split()])

        rbi = rbo = rpi = rpo = 0
        for k,v in rawdata.items():
            for i in self._black_list:
                if re.match(i, k) is not None:
                    continue
            rbi += v[0]
            rpi += v[1]
            rbo += v[8]
            rpo += v[9]

        self.set_val(('netdev', 'realbytesin'), rbi, True)
        self.set_val(('netdev', 'realbytesout'), rbo, True)
        self.set_val(('netdev', 'realpacketsin'), rpi, True)
        self.set_val(('netdev', 'realpacketsout'), rpo, True)

        if not self.info.has_key('last_netdev'):
            self.info['last_netdev'] = self.info['netdev']

    def get_bytes_in(self):
        vdiff = self.get_val(('netdev', 'realbytesin')) - \
                self.get_val(('last_netdev', 'realbytesin'))
        if not vdiff > 0:
            return 0
        tdiff = self.get_timestamp('netdev') - self.get_timestamp('last_netdev')
        if tdiff < 1:
            tdiff = 1
        return int(vdiff / tdiff)

    def get_bytes_out(self):
        vdiff = self.get_val(('netdev', 'realbytesout')) - \
                self.get_val(('last_netdev', 'realbytesout'))
        if not vdiff > 0:
            return 0
        tdiff = self.get_timestamp('netdev') - self.get_timestamp('last_netdev')
        if tdiff < 1:
            tdiff = 1
        return int(vdiff / tdiff)

    def get_packets_in(self):
        vdiff = self.get_val(('netdev', 'realpacketsin')) - \
                self.get_val(('last_netdev', 'realpacketsin'))
        if not vdiff > 0:
            return 0
        tdiff = self.get_timestamp('netdev') - self.get_timestamp('last_netdev')
        if tdiff < 1:
            tdiff = 1
        return int(vdiff / tdiff)

    def get_packets_out(self):
        vdiff = self.get_val(('netdev', 'realpacketsout')) - \
                self.get_val(('last_netdev', 'realpacketsout'))
        if not vdiff > 0:
            return 0
        tdiff = self.get_timestamp('netdev') - self.get_timestamp('last_netdev')
        if tdiff < 1:
            tdiff = 1
        return int(vdiff / tdiff)

if __name__ == '__main__':
    ins = NetModule(['lo', 'bond'])

    while True:
        ins.update()
        val = ins.get_bytes_out()
        if val > 0:
            print val
        time.sleep(0)
