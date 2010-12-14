'''Basic platform informations'''

import os
import sys
import time
from mon_module import MonModule


metric_list = (
    'cpu_num',
    'cpu_model_name',
    'vt_support',
    'os_version',
    'mem_total',
    'disk_total',
    'disk_free'
)


class PlatformInfo(MonModule):

    proc_file_list = [{
            'name'  :   'cpuinfo',
            'path'  :   '/proc/cpuinfo'
          },{
            'name'  :   'version',
            'path'  :   '/proc/version'
          }]

    def update(self):
        for item in PlatformInfo.proc_file_list:
            self.update_file(item['name'],item['path'])

        fd = os.popen('df')
        fd.readline()
        lines = [line.strip().split() for line in fd]
        fd.close()
        for i in range(len(lines)-1):
            if len(lines[i]) < 6:
                lines[i] += lines[i+1]
                del lines[i+1]
        self.set_val('df', lines, True)
        total = 0
        for line in lines:
            total += int(line[1])
        #total = '%.0fG' % (total / (1024.0 ** 2))
        self.set_val('disk_total', total, True)     

    def get_cpu_num(self):
        if 'cpu_num' not in self.info:
            cpu_num = 0
            for elem in self.info['cpuinfo']['val']:
                if elem[0].startswith('processor'):
                    cpu_num += 1
            self.add_to_dict('cpu_num',cpu_num)
        return self.info['cpu_num']

    def get_cpu_model_name(self):
        if 'cpu_module_name' not in self.info:
            for elem in self.info['cpuinfo']['val']:
                if elem[0].startswith('model name'):
                     cpu_model_name = elem[1]
            self.info['cpu_model_name'] = cpu_model_name
        return self.info['cpu_model_name']
    
    def get_vt_support(self):
        if 'vt_support' not in self.info:
            for elem in self.info['cpuinfo']['val']:
                if elem[0].startswith('flag'):
                    if elem[1].find(' vmx ') > 0:
                        vt_support = 'Intel_VT'
                    elif elem[1].find(' svm ') > 0:
                        vt_support = 'AMD_VT'
                    else:
                        vt_support = 'No'
                    break
            self.info['vt_support'] = vt_support
        return self.info['vt_support']

    def get_os_version(self):
        #if not os.access('/proc/version', os.F_OK):
            #self.info['os_version'] = 'other'
        return self.info['version']['val'][0][0].split('(')[0].strip()

    def get_mem_total(self):
        fd = open('/proc/meminfo', 'r')
        firstline = fd.readline()
        fd.close()
        return firstline.split(':')[1].strip()

    def get_disk_total(self):
        #lines = self.get_val('df')
        #total = 0
        #for line in lines:
            #total += int(line.split()[1])
        total = '%.0fG' % (self.get_val('disk_total') / (1024.0 ** 2))
        return total 

    def get_disk_free(self):
        total = self.get_val('disk_total')
        lines = self.get_val('df')
        free = 0
        for line in lines:
            free += int(line[3])
        return '%.0f%%' % (100.0 * free / total)

if __name__ == "__main__":
    pi = PlatformInfo()
    print pi.info
    print '================================================================'
    print 'number of processors : %d' % (pi.metric_handler('cpu_num'), )
    print 'cpu model name : ' + pi.metric_handler('cpu_model_name')
    print 'cpu vt support : ' + pi.metric_handler('vt_support')
    print 'disk_total : %s' % pi.metric_handler('disk_total')
    print 'disk_free : %s' % pi.metric_handler('disk_free')
