import os
import sys
import time

from utils import *

class MonModuleException(Exception):
    pass

class MonModule(object):
    '''monitor moudle'''


    def __init__(self):
        self.info = {}
        self.metric_init()


    def metric_init(self):
        self.update()


    def update(self):
        for item in self.data_sources:
            data = {}
            val = self._parse_file(item['path'], item['type'])
            data['val'] = val
            data['timestamp'] = time.time()
            self.info[item['name']] = data


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


    def get_val(self, keys):
        if type(keys) is str:
            keys = [keys, 'val']
        else:
            keys = list(keys)
            keys.insert(1, 'val')

        return get_from_dict(self.info, keys)             


    def set_val(self, keys, val, create=False):
        if type(keys) is str:
            put_to_dict(self.info, [keys, 'val'], val, create)
        else:
            keys = list(keys)
            keys.insert(1, 'val')
            put_to_dict(self.info, keys, val, create)


    def get_timestamp(self, key):
        return get_from_dict(self.info, [key, 'timestamp'])


    def set_timestamp(self, key, timestamp=time.time()):
        put_to_dict(self.info, [key, 'timestamp'], timestamp, True)



