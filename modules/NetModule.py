import time
from mon_module import MonModule


metric_list = [
    'bytes_in',
    'bytes_out',
    'packets_in',
    'packets_out'
]

class NetModule(MonModule):

    proc_file_list = [{
        'name'  :   'netdev',
        'path'  :   '/proc/net/dev'
    }]

    def update(self):
        if self.info.has_key('netdev'):
            self.info['last_netdev'] = self.info['netdev']
            self.info['netdev'] = {}
        
        f = open('/proc/net/dev', 'r')
        now = time.time()
        lines = [line.strip() for line in f][2:] # discard the two-line header
        f.close()
        #self.set_val('netdev', {}, True)
        self.set_timestamp('netdev', now)

        rbi = rbo = rpi = rpo = 0
        for line in lines:
            tmp = line.split(':', 1)
            if tmp[0] in ('lo', 'bond'):
                continue
            data = tmp[1].split()
            rbi += int(data[0])
            rpi += int(data[1])
            rbo += int(data[8])
            rpo += int(data[9])

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
    ins = NetModule()
    while True:
        ins.update()
        val = ins.get_bytes_out()
        if val > 0:
            print val
        time.sleep(0)
