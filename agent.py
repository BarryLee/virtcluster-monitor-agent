#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
import os.path
import socket
import xmlrpclib
from time import sleep

from utils.utils import current_dir, encode, decode, _print
from utils.load_config import load_config
from utils.get_logger import get_logger
from modeler import model


logger = get_logger('agent')


class AgentException(Exception):
    pass


PLATFORM = 'linux'

def import_module(module_name):
    #print type(module_name)
    temp = __import__('modules.' + PLATFORM, globals(), locals(), [module_name,])
    return getattr(temp, module_name)
    #return __import__('.'.join(('modules', PLATFORM, module_name)))


class Collector(object):

    def __init__(self, mod_name, *args, **kwargs):
        self.mod_name = mod_name
        mod = import_module(mod_name)
        instance = getattr(mod, mod_name)(*args, **kwargs)
        self.worker = instance
        self.handler = instance.metric_handler
        self.update = instance.update
        self.prefix = instance.get_prefix()
        logger.debug('Collector.__init__: %s, %s' % (self.handler, self.update))
        self.metrics = []
        self.last_collect = 0
        self.report = {}
    
 
    def setMetricGroup(self, metrics):
        for metric in metrics:
            if metric["enabled"] == 1:
                self.metrics.append(metric)


    def setPeriod(self, period):
        self.period = period


    def doCollect(self):
        retval = self.report
        self.update()
        for metric in self.metrics:
            name = metric['name']
            val = self.handler(metric['name'])
            if type(val) is dict:
                for k, v in val.iteritems():
                    p_name = k + '_' + name
                    retval[p_name] = v
            else:
                if self.prefix is not None:
                    name = self.prefix + '_' + name
                retval[name] = val
        #self.last_collect = time()
        self.last_collect = self.worker.get_update_time()
        retval['timestamp'] = self.last_collect
        #logger.debug('doCollect:%s' % (retval,)) 
        return retval



class Sender(threading.Thread):
    
    def __init__(self, collector, channel):
        super(Sender, self).__init__()

        self.collector = collector
        self._interval = self.collector.period
        self._channel = channel
        # use condition instead of sleep
        #self.cond = threading.Condition()
        self.CONT_FLAG = True
        self.setName(collector.mod_name)
        # make sure this thread exits when the main thread exits
        self.setDaemon(True)   
    
    def stop(self):
        #self.cond.acquire()
        # let the run() loop stop
        self.CONT_FLAG = False  
        #self.cond.notify()
        #self.cond.release()


    def collectAndSend(self):
        self._send(self._channel, encode(self.collector.doCollect()))


    def _send(self, channel, data):
        #channel[2].sendto(data, (channel[0], channel[1]))
        logger.debug(data)


    def run(self):
        if self.CONT_FLAG:
            try:
                logger.debug('%s start working...' % self.getName())
                self.collectAndSend()
            except Exception, e:
                logger.exception('Oops, error occured')
                #Monitor.RUNNING = False
            else:
                #Monitor.RUNNING = True
                while self.CONT_FLAG:
                    sleep(self._interval)
                    try:
                        self.collectAndSend()
                    except Exception, e:
                        logger.exception('')
                        #Monitor.RUNNING = False
                        #break
                        raise
                    #self.cond.acquire()
                    # block until next collect
                    #self.cond.wait(self._interval)  



class Controller(object):
    
    def __init__(self, mgroups, 
                 #cinterval, 
                 targethost, targetport):
        self._metric_groups = mgroups
        #self._collect_interval = cinterval
        self._channel = (targethost, targetport,
                         socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        self._collectors = {}


    def start(self):
        for metric_group in self._metric_groups:
            modname = metric_group['name']
            if metric_group.has_key('args'):
                args = metric_group['args']
            else:
                args = {}
            collector = Collector(modname, **args)
            collector.setMetricGroup(metric_group["metrics"])
            collector.setPeriod(metric_group["period"])
            self.loadCollector(modname, collector)
            sleep(1)


    def loadCollector(self, cname, cinstance):
        # start this collector now
        s = Sender(cinstance, self._channel)
        if not self._collectors.has_key(cname):
            self._collectors[cname] = []
        self._collectors[cname].append(s) 
        s.start()


    #def waitTillDie(self):
        #for cl in self._collectors.values():
            #for t in cl:
                #t.join()

    
def main():

    global_config = load_config()
    #_print(global_config)

    #metric_conf_file = current_dir(__file__) + os.path.sep + 'metric_conf'
    #f = open(metric_conf_file)
    #metric_conf = decode(f.read())
    #f.close()

    #_print(metric_conf)
    server_host, server_port = global_config['monitor_server'].split(':')
    server_port = int(server_port)
    rpc_client = xmlrpclib.ServerProxy('http://%s:%d' % (server_host, server_port))

    try:
        retcode, retdata = rpc_client.sign_in(encode(model()))
        logger.debug('%d\n%s' % (retcode, retdata))
        assert retcode == 1
    except Exception, e:
        logger.exception('')
        raise AgentException, 'sign_in failed'

    metric_conf = decode(retdata)
    cont = Controller(metric_conf['metric_groups'], server_host, server_port)
    cont.start()
    #cont.waitTillDie()
    
    while True:
        _print(threading.enumerate())
        sleep(60)

if __name__ == '__main__':
    #mod = import_module('CPUModule')
    #print mod
    main()
   
