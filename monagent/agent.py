#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import sys
sys.path.append(os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(__file__))))

import threading
import socket
import xmlrpclib

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
        self.CONT_FLAG = True
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
                        logger.exception("Oops, error occured")



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
        logger.info("starting controller...")
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


    def stop(self):
        logger.info("stopping controller...")
        for modname, senderlist in self._collectors.items():
            for sender in senderlist:
                sender.stop()
        self._collectors.clear()

    #def waitTillDie(self):
        #for cl in self._collectors.values():
            #for t in cl:
                #t.join()

class Agent(object):

    def __init__(self, config):
        # init the controller
        self.metric_list = load_metric_list()
        dserver_host, dserver_port = config["data_server"].split(":")
        dserver_port = int(dserver_port)
        self.controller = Controller(self.metric_list["metric_groups"], dserver_host, dserver_port)
        self.dataserver = (dserver_host, dserver_port)
        # create a rpc client
        mserver_host, mserver_port = config["monitor_server"].split(":")
        mserver_port = int(mserver_port)
        self.rpc_client = xmlrpclib.ServerProxy("http://%s:%d" % (mserver_host, mserver_port))
        self.monserver = (mserver_host, mserver_port)
        
        self.retry = config.as_int('retry')
        self.retry_interval = config.as_int('retry_interval')
        self.config = config

        self.start()
        
    def start(self):
        self.register()
        self.controller.start()
        threadinglize(self.checkAlive)()
        return True

    def stop(self):
        self.controller.stop()
        return True
    
    def restart(self):
        if self.stop():
            return self.start()
        else:
            return False

    def register(self):
        platforminfo = get_platform_info()
        platforminfo.update(self.metric_list)
        platforminfo['port'] = self.config.as_int('port')

        try:
            retcode, myid = self.rpc_client.register(encode(platforminfo))
            assert retcode
            logger.info("registered on server %s:%d" % self.monserver)
        except Exception, e:
            logger.exception('')
            raise AgentException, "register on %s:%d failed" % self.monserver

    def checkAlive(self):
        retry = self.retry
        while True:
            try:
                self.rpc_client.howru()
                retry = self.retry
            except socket.error, e:
                logger.exception('')
                if retry > 0:
                    retry -= 1
                    logger.warning("cannot connnect to server, %d time to go" % retry)
                else:
                    logger.error("server is down, stop sending now")
                    self.controller.stop()
                    break
                    #sys.exit(1)
            sleep(self.retry_interval)

def main():
    agent = Agent(global_config)
    server = SimpleXMLRPCServer(('0.0.0.0', global_config.as_int('port')))
    server.register_instance(agent)
    server.serve_forever()


if __name__ == "__main__":
    #mod = import_module("CPUModule")
    #print mod
    main()
    
   
