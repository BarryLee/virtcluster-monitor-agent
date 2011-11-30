#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
import os.path
import socket
import xmlrpclib
import sys

from time import sleep
from SimpleXMLRPCServer import SimpleXMLRPCServer

from utils.utils import current_dir, encode, decode, _print, threadinglize
from utils.load_config import load_global_config, load_metric_list
from utils.get_logger import get_logger
from utils.platform_info import get_platform_info


logger = get_logger("agent")

global_config = load_global_config()

PLATFORM = global_config["platform"]

# change to the current directory
#os.chdir(current_dir(__file__))


class AgentException(Exception):
    pass


def import_module(module_name):
    #print type(module_name)
    temp = __import__("modules." + PLATFORM, globals(), locals(), [module_name,])
    return getattr(temp, module_name)
    #return __import__(".".join(("modules", PLATFORM, module_name)))


class Collector(object):

    def __init__(self, mod_name, metric_group, period, *args, **kwargs):
        self.mod_name = mod_name
        mod = import_module(mod_name)
        instance = getattr(mod, mod_name)(*args, **kwargs)
        self.worker = instance
        self.handler = instance.metric_handler
        self.update = instance.update
        #logger.debug("Collector.__init__: %s, %s" % (self.handler, self.update))

        self.metrics = []
        self.setMetricGroup(metric_group)
        self.setPeriod(period)

        self.last_collect = 0
        self.report = {"timestamp": 0, "val": {}}
        device = instance.get_device()
        if device is not None:
            self.report["device"] = device
    
 
    def setMetricGroup(self, metrics):
        for metric in metrics:
            if metric["enabled"] == 1:
                self.metrics.append(metric)


    def setPeriod(self, period):
        self.period = period


    def doCollect(self):
        ret = self.report
        retval = ret["val"]
        self.update()
        for metric in self.metrics:
            name = metric["name"]
            retval[name] =self.handler(name)
        #self.last_collect = time()
        self.last_collect = self.worker.get_update_time()
        ret["timestamp"] = self.last_collect
        #logger.debug("doCollect:%s" % (retval,)) 
        return ret



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
        channel[2].sendto(data, (channel[0], channel[1]))
        #logger.debug(data)


    def run(self):
        if self.CONT_FLAG:
            try:
                logger.debug("%s start working..." % self.getName())
                self.collectAndSend()
            except Exception, e:
                logger.exception("Oops, error occured")
            else:
                while self.CONT_FLAG:
                    sleep(self._interval)
                    try:
                        self.collectAndSend()
                    except Exception, e:
                        logger.exception("")
                        raise



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
            modname = metric_group["name"]
            if metric_group.has_key("instances"):
                for args in metric_group["instances"]:
                    collector = Collector(modname, 
                                          metric_group["metrics"], 
                                          metric_group["period"], 
                                          **args)
                    #collector.setMetricGroup(metric_group["metrics"])
                    #collector.setPeriod(metric_group["period"])
                    self.loadCollector(modname, collector)
                    sleep(1)
            #if metric_group.has_key("args"):
                #args = metric_group["args"]
            #else:
                #args = {}
            else:
                collector = Collector(modname, 
                                      metric_group["metrics"], 
                                      metric_group["period"])
                #collector.setMetricGroup(metric_group["metrics"])
                #collector.setPeriod(metric_group["period"])
                self.loadCollector(modname, collector)
                sleep(1)


    def loadCollector(self, cname, cinstance):
        # start this collector now
        s = Sender(cinstance, self._channel)
        self._collectors.setdefault(cname, [])
        #if not self._collectors.has_key(cname):
            #self._collectors[cname] = []
        self._collectors[cname].append(s) 
        s.start()


    #def waitTillDie(self):
        #for cl in self._collectors.values():
            #for t in cl:
                #t.join()

    
def main():

    platforminfo = get_platform_info()
    metric_list = load_metric_list()
    platforminfo.update(metric_list)

    mserver_host, mserver_port = global_config["monitor_server"].split(":")
    mserver_port = int(mserver_port)
    rpc_client = xmlrpclib.ServerProxy("http://%s:%d" % (mserver_host, mserver_port))

    try:
        retcode, myid = rpc_client.register(encode(platforminfo))
        assert retcode
        logger.info("registered on server %s:%d" % (mserver_host, mserver_port))
    except Exception, e:
        logger.exception(myid)
        raise AgentException, "register on %s:%d failed" % (mserver_host, mserver_port)

    #metric_list = decode(retdata)
    dserver_host, dserver_port = global_config["data_server"].split(":")
    dserver_port = int(dserver_port)
    controller = Controller(metric_list["metric_groups"], dserver_host, dserver_port)
    #cont.waitTillDie()
    server = SimpleXMLRPCServer(('0.0.0.0', int(global_config['port'])))
    server.register_instance(controller)
    threadinglize(server.serve_forever)()

    controller.start()
    logger.info("start sending to server %s:%d" % (dserver_host, dserver_port))

    retry = 2
    while True:
        #_print(threading.enumerate())
        try:
            rpc_client.howru()
            retry = 2
        except socket.error, e:
            logger.exception("")
            if retry > 0:
                retry -= 1
                logger.warning("cannot connnect to server, %d time to go" % retry)
            else:
                logger.error("server is down, exit now")
                sys.exit(1)
        sleep(60)

if __name__ == "__main__":
    #mod = import_module("CPUModule")
    #print mod
    main()
   
