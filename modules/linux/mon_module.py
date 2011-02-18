import os
import sys
import time

from utils import *

class MonModuleException(Exception):
    pass

class MonModule(object):
    '''monitor moudle'''


    def __init__(self):
        self._rawdata = {}
        self._report = {}
        #self.info = {}
        self._t_diff = 0
        self._update_t = 0
        self.metric_init()


    def metric_init(self):
        self.update()


    def update(self):
        for item in self.data_sources:
            #data = {}
            val = self._parse_file(item['path'], item['type'])
            #data['val'] = val
            #data['timestamp'] = time.time()
            now = time.time()
            self._t_diff = now - self._update_t
            self._update_t = now
            #self.info[item['name']] = data
            self._rawdata[item['name']] = val


    def _parse_file(self, fpath, ftype):
        if ftype == 'list':
            return file2list(fpath)
        elif ftype == 'string':
            return file2string(fpath)
        elif ftype == 'dict':
            return file2dict(fpath)


    def metric_handler(self, metric, *args, **kwargs):
        #return eval("self.get_" + metric + "()")
        mname = 'get_' + metric
        try:
            method = getattr(self, mname)
        except AttributeError, e:
            raise MonModuleException, 'no such metric: %s' % metric
        else:
            return method(*args, **kwargs)


    def get_update_time(self):
        return self._update_t
 

    def _get_time_diff(self):
        return self._t_diff


    def _get_rawdata(self, keys):
        return get_from_dict(self._rawdata, keys)             


    def _set_rawdata(self, keys, val, create=False):
        put_to_dict(self._rawdata, keys, val, create)


    def _get_report(self, keys):
        #if type(keys) is str:
            #keys = [keys, 'val']
        #else:
            #keys = list(keys)
            #keys.insert(1, 'val')

        #return get_from_dict(self.info, keys)             
        return get_from_dict(self._report, keys)             


    def _set_report(self, keys, val, create=False):
        #if type(keys) is str:
            #put_to_dict(self.info, [keys, 'val'], val, create)
        #else:
            #keys = list(keys)
            #keys.insert(1, 'val')
            #put_to_dict(self.info, keys, val, create)
        put_to_dict(self._report, keys, val, create)


    def get_timestamp(self, key):
        #return get_from_dict(self.info, [key, 'timestamp'])
        return self._update_t


    def set_timestamp(self, key, timestamp=time.time()):
        #put_to_dict(self.info, [key, 'timestamp'], timestamp, True)
        self._update_t = timestamp



