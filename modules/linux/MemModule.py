import os
import sys
from mon_module import MonModule

metric_list = [
    'mem_total',
    'cached',
    'mem_free',
    'mem_available',
    'mem_used',
    'mem_usage',
    'buffers',
    'swap_total',
    'swap_cached',
    'swap_free'
]

class MemModule(MonModule):

    data_sources = [{
        'name'  :   'meminfo',
        'path'  :   '/proc/meminfo',
        'type'  :   'dict'
    }]

    #def update(self):
        #for item in self.proc_file_list:
            #self.update_file(item['name'], item['path'])
        
        #self.set_val('meminfo', dict(self.get_val('meminfo')))
        #self.set_val(['meminfo', 'MemUsed'], \
                     #str(int(self.get_val(['meminfo', 'MemTotal']).split()[0]) - \
                     #int(self.get_val(['meminfo', 'MemFree']).split()[0]) - \
                     #int(self.get_val(['meminfo', 'Buffers']).split()[0]) - \
                     #int(self.get_val(['meminfo', 'Cached']).split()[0])))

    def get_mem_total(self):
        return int(self._get_rawdata('meminfo')['MemTotal'].split()[0])

    def get_cached(self):
        return int(self._get_rawdata(['meminfo', 'Cached']).split()[0])

    def get_mem_free(self):
        return int(self._get_rawdata(['meminfo', 'MemFree']).split()[0])

    def get_mem_available(self):
        return int(self._get_rawdata(['meminfo', 'MemFree']).split()[0]) + \
             int(self._get_rawdata(['meminfo', 'Buffers']).split()[0]) + \
             int(self._get_rawdata(['meminfo', 'Cached']).split()[0])

    def get_buffers(self):
        return int(self._get_rawdata(['meminfo', 'Buffers']).split()[0])

    def get_mem_used(self):
        return int(self._get_rawdata(['meminfo', 'MemTotal']).split()[0]) - \
             int(self._get_rawdata(['meminfo', 'MemFree']).split()[0]) - \
             int(self._get_rawdata(['meminfo', 'Buffers']).split()[0]) - \
             int(self._get_rawdata(['meminfo', 'Cached']).split()[0])

    def get_mem_usage(self):
        return self.get_mem_used() * 100.0 / self.get_mem_total()

    def get_swap_total(self):
        return int(self._get_rawdata(['meminfo', 'SwapTotal']).split()[0])

    def get_swap_cached(self):
        return int(self._get_rawdata(['meminfo', 'SwapCached']).split()[0])

    def get_swap_free(self):
        return int(self._get_rawdata(['meminfo', 'SwapFree']).split()[0])
        


if __name__ == '__main__':
    ins = MemModule()
    print ins.metric_handler('mem_usage')
