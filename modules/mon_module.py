import os
import sys
import time

from mon_module_utils import *

class MonModuleException(Exception):
    pass

class MonModule(object):
    '''monitor moudle'''

    #__info = {}

    def __init__(self):
        #self.info = self.__info
        self.info = {}
        self.metric_init()

    def metric_init(self):
        self.update()

    def update(self):
        for item in self.proc_file_list:
            self.update_file2list(item['name'],item['path'])    

    #def metric_init(self):
        #pass
    
    #def metric_cleanup(self):
        #pass

    def metric_handler(self,metric):
        #return eval("self.get_" + metric + "()")
        mname = 'get_' + metric
        try:
            method = getattr(self, mname)
        except AttributeError, e:
            raise MonModuleException, 'no such metric: %s' % metric
        else:
            return method()

    def add_to_dict(self, key, value):
        self.info[key] = value

    def update_file2str(self,fname,fpath):
        data = {}
        try:
            astr = file2string(fpath)
        except IOError, e:
            if e.errno != 2:
                raise e
            else:
                raise MonModuleException, 'file %s not found' % fpath
        data['val'] = astr
        #data['timestamp'] = time.strftime('%Y%m%d%H%M%S')
        data['timestamp'] = time.time()
        #self.add_to_dict(fname,astr)
        self.add_to_dict(fname,data)
        
    def update_file2list(self,fname,fpath):
        data = {}
        try:
            lst = file2list(fpath)
        except IOError, e:
            if e.errno != 2:
                raise e
            else:
                raise MonModuleException, 'file %s not found' % fpath
        data['val'] = lst
        data['timestamp'] = time.time()
        self.info[fname] = data
        #self.add_to_dict(fname,lst)
     
    def update_file(self,fname,fpath,rtype='list'):
        data = {}
        if rtype == 'str':
            val = _file2str(fpath)
        else:
            val = file2list(fpath)
        data['val'] = val
        data['timestamp'] = time.time()
        self.info[fname] = data

    #update_file = update_file2list

    def get_val(self, keys):
        if type(keys) is str:
            keys = [keys, 'val']
        else:
            keys = list(keys)
            keys.insert(1, 'val')

        return getDictDeeply(self.info, keys)             

    def set_val(self, keys, val, create=False):
        if type(keys) is str:
            setDictDeeply(self.info, [keys, 'val'], val, create)
        else:
            keys = list(keys)
            keys.insert(1, 'val')
            setDictDeeply(self.info, keys, val, create)

    def get_timestamp(self, key):
        return getDictDeeply(self.info, [key, 'timestamp'])

    def set_timestamp(self, key, timestamp=time.time()):
        setDictDeeply(self.info, [key, 'timestamp'], timestamp, True)


if __name__=="__main__":
    print sys.argv[0]
    print sys.path
