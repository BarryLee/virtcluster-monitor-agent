#-*- coding:utf-8 -*-
import socket
import fcntl
import struct
import os
import time
import threading
import subprocess
import sys

current_dir = lambda f: os.path.dirname(os.path.abspath(f))

parent_dir = lambda f: os.path.dirname(current_dir(f))

if sys.version[:3] >= '2.6':
    import json
else:
    # Because of simplejson's intra-package import statements, the path
    # of simplejson has to be temporarily add to system path, otherwise 
    # we will get ImportError when import from the upper level.
    cur_dir = current_dir(__file__)
    sys.path.append(cur_dir)
    import simplejson as json
    sys.path.remove(cur_dir)

#import mon_agent_logger
from Exceptions import ExecCmdException

#logger = mon_agent_logger.instance()

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def is_virt_plat():
    return os.access('/proc/xen', os.F_OK)


#def get_from_dict(dict_, keys):
    #ret = dict_
    #if type(keys) is str:
        #ret = dict_[keys]
    #else:
        #keys = list(keys)
        #for i in keys:
            #ret = ret[i]

    #return ret

#def put_to_dict(dict_, keys, val, createMidNodes=False):
    #if type(keys) is str:
        #dict_[keys] = val
    #else:
        #keys = list(keys)
        #midKeys = keys[0:-1]
        #theKey = keys[-1]
        #sub = dict_
        #for i in midKeys:
            #try:
                #sub = sub[i]
            #except KeyError, e:
                #if createMidNodes:
                    #sub[i] = {}
                    #sub = sub[i]
                #else:
                    #raise
        #sub[theKey] = val


def remote_call(retry=3, timeout=5):
    wrapped_args = [retry, timeout]
    def try_call(procedure):
        def wrapper(*args, **kwargs):
            retry_ = retry = wrapped_args[0]
            timeout = wrapped_args[1]
            while retry:
                try:
                    result = procedure(*args, **kwargs)
                except socket.error, e:
                    #logger.error("call %s(%s) failed, retry later..." \
                                 #% (procedure.__name__, args))
                    retry -= 1
                    time.sleep(timeout)
                else:
                    #logger.debug("call %s(%s) succeeded" % (procedure.__name__, args))
                    return True, result

            #logger.error("retried call %s(%s) %d times and failed"
                         #% (procedure.__name__, args, retry_))
            return False, None 

        return wrapper

    return try_call

def threadinglize(target_, tName=None, isDaemon_=True):
    def func_(*args_, **kwargs_):
        t = threading.Thread(target=target_, args=args_, kwargs=kwargs_)
        if isDaemon_:
            t.setDaemon(True)
        if tName:
            t.setName(tName)
        else:
            t.setName(target_.__name__)
        t.start()
    return func_


def decode(data):
    #return json.loads(data)
    #return eval(data)
    return _parseJSON(json.loads(data))


def encode(data, pretty=False):
    if pretty:
        return json.dumps(data, sort_keys=True, indent=2)
    return json.dumps(data)


# turns unicode back into str
def _parseJSON(obj):
    if obj is None:
        return obj
    elif type(obj) in (int, float, str, bool):
        return obj
    elif type(obj) == unicode:
        return str(obj)
    elif type(obj) in (list, tuple, set):
        obj = list(obj)
        for i,v in enumerate(obj):
            obj[i] = _parseJSON(v)
    elif type(obj) == dict:
        for i,v in obj.iteritems():
            obj.pop(i)
            obj[_parseJSON(i)] = _parseJSON(v)
    else:
        print "invalid object in data, converting to string"
        obj = str(obj) 
    return obj


def exec_cmd(cmd):
    try:
        out, err = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, \
                                  stderr=subprocess.PIPE).communicate()
    except Exception, e:
        raise ExecCmdException, '%s, %s' % (str(e), __file__)
    else:
        if err:
            raise ExecCmdException, err
        else:
            return out

# a hack for upward compatility to python 3
if sys.version_info[0] < 3:
    def subp_getstatusoutput(cmd):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, shell=True)
        # communicate() will terminate the process, hence waitpid will
        # encounter an error
        #output = reduce(lambda x,y: x+y, map(lambda x: x and x or '', 
                                             #p.communicate()))
        status = os.waitpid(p.pid, 0)[1]
        output = p.stdout.read() + p.stderr.read()
        return status, output

    subprocess.getstatusoutput = subp_getstatusoutput
    subprocess.getoutput = lambda cmd: os.popen(cmd).read()

def proc2dict(proc):
    '''
    The argument proc can be a string consists of several lines of <key>:<value>,
    then we should split it into a list of lines, or a file object so that we can
    leverage the generator to iterate lines.
    '''
    return dict([[i.strip() for i in pair] for pair in [line.split(':', 1) 
            for line in ((type(proc) is str) and proc.splitlines() or proc) 
            if line.strip() != '']])


import pprint
pp = pprint.PrettyPrinter(indent=2)
def _print(msg):
    pp.pprint(msg)



if __name__ == '__main__':
    import unittest

    class test_util(unittest.TestCase):

        def testFile2List(self):
            ret = file2list('/proc/cpuinfo')
            print ret

        def testGetDictDeeply(self):
            test = { '1': { '2': { '3': 4 } } }
            self.assertEquals(test['1']['2']['3'], \
                              getDictDeeply(test, ('1', '2', '3')))
            self.assertEquals(test['1'], \
                              getDictDeeply(test, '1'))

        def testSetDictDeeply(self):
            test = {}
            setDictDeeply(test, (1, 2, 3), 4, True)
            self.assertEquals(test[1][2][3], 4)
            setDictDeeply(test, (1, 2, 3), 'phsyco')
            self.assertEquals(test[1][2][3], 'phsyco')
            self.assertRaises(KeyError, setDictDeeply, test, (1,2,4,5), '')

        #def testThreadinglize(self):
            #def echo(i,j,msg='step'):
                #for n in range(3):
                    #print i,j,msg
                    #print threading.currentThread().name
                    #time.sleep(3)

            #threadinglize(echo, 'ECHO', False)(1,2)
            #for t in threading.enumerate():
                #if t is not threading.currentThread():
                    #t.join()
        
        #def testExecCmd(self):
            #exec_cmd('ls /root')
            #self.assertRaises(ExecCmdException, exec_cmd, 'ls /root')
            #exec_cmd('xm list')

        def testProc2Dict(self):
            fd = open('/proc/cpuinfo')
            print proc2dict(fd)
            fd.close()
            print proc2dict(exec_cmd('cat /proc/meminfo'))

        def testSubpNewMethod(self):
            print subprocess.getoutput('ls /')
            print subprocess.getstatusoutput('ls /root')
            print subprocess.getstatusoutput('xm list')
    
    unittest.main()
