#!/usr/bin/env python

import threading
import os
import sys
from time import time, sleep, gmtime, strftime
from SimpleXMLRPCServer import SimpleXMLRPCServer
import socket
import xmlrpclib

curdir = os.path.dirname(os.path.abspath(__file__))
if os.system('python %s%s%s' % (curdir, os.path.sep, 'mon_config_gen.py')) != 0:
    print 'cannot generate config file'
    sys.exit(1)

from mon_agent_base import ThreadingXMLRPCServer, Singleton, MonAgentException
from mon_agent_utils import get_ip_address, threadinglize, remote_call, \
                        load_config, encode
import mon_agent_logger

logger = mon_agent_logger.instance()

MODULE_DIR = curdir + os.path.sep + 'modules'
sys.path.append(MODULE_DIR)

DEFAULT_CONF = curdir + os.path.sep + "agent_default_config"
global_config = load_config(DEFAULT_CONF)

def collect_basic_info():
    result = {}
    for mod in global_config['basic_info']:
        collector = Collector(mod['name'])
        collector.set_metric_group(mod['metrics'])
        info = collector.do_collect()
        del info['timestamp']
        result[mod['title']] = info

    return result

def generate_metadata():
    ret = {}
    ret['metric_groups'] = global_config['metric_groups']
    ret['basic_info'] = collect_basic_info()
    ret['listen_channel'] = global_config['listen_channel']

    return ret


class Controller(object):

    def __init__(self, config=[]):
        self._config = config

    def _listMethods(self):
        return []
    
    def set_config(self, config):
        self._config = config

    def get_metadata(self):
        return encode(generate_metadata())

    def start_monitor(self):
        for cthread in threading.enumerate():
            if cthread.getName() == "monitor":
                return "Monitor is already running!"
        logger.info("Starting monitor...")
        #if not hasattr(self, "_monitor"):
        self._monitor = Monitor(self._config)
        self._monitor.setName("monitor")
        self._monitor.setDaemon(True)   # make sure this thread exits when the
                                        #  main thread exits
        self._monitor.start()
        countdown = 60
        for i in range(countdown):
            if self._monitor.is_running():
                return "ok"
                #return 1    # return 0 if ok
            sleep(1)
        logger.error('failed to start monitor')
        return "failed"
        #return 0    # return 1 if failed

    def stop_monitor(self):
        if hasattr(self, "_monitor") and self._monitor.isAlive():
            logger.info("Stopping monitor...")
            #print self._monitor.isAlive()
            self._monitor.halt()
            #self._monitor.pause()
            self._monitor.join()
            #print self._monitor.isAlive()
            #del self._monitor
            return "ok"
        return "Monitor is not running"

    def restart_monitor(self):
        pass

class Monitor(Singleton, threading.Thread):

    #_LOADED = False
    RUNNING = False

    def __init__(self, config):
        threading.Thread.__init__(self)
        self.CONT_FLAG = True
        self._lock = threading.RLock()
        #if not Monitor._LOADED:
        logger.info('loading config...')
        self._interval = config["collect_interval"]
        self._metric_groups = config["metric_groups"]
        self._targets = config["remote_servers"]
        self._collectors = {}
        self._channel = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cond = threading.Condition()
        for metric_group in self._metric_groups:
            modname = metric_group['name']
            collector = Collector(modname)
            collector.set_metric_group(metric_group["metrics"])
            collector.set_period(metric_group["period"])
            self.load_collector(modname, collector)
        #Monitor._LOADED = True
            
    #def __del__(self):
        #print '__del__ called'

    #def __call__(self):
        #self.run()

    def load_collector(self, cname, collector):
        self._lock.acquire()
        self._collectors[cname] = collector
        self._lock.release()

    def unload_collector(self, cname):
        self._lock.acquire()
        self._collectors.pop(cname)
        self._lock.release()

    def _send(self, sock, data):
        for target in self._targets:
            addr = (target['host'], target['port'])
            sock.sendto(data, addr) 

    def _collect_and_send(self):
        #self._channel = socket(AF_INET, SOCK_DGRAM)
        for name, collector in self._collectors.items():
            if time() - collector.last_collect > collector.period:
                #print encode(collector.do_collect())
                self._send(self._channel, encode(collector.do_collect()))

    def run(self):
        if self.CONT_FLAG:
            try:
                #self._setup_send_channels()
                self._collect_and_send()
            except Exception, e:
                logger.exception('Oops, error occured')
                Monitor.RUNNING = False
            else:
                Monitor.RUNNING = True
                while self.CONT_FLAG:
                    #self.cond.acquire()
                    #self.cond.wait(10)
                    #self.cond.wait(self._interval)
                    try:
                        self._collect_and_send()
                    except Exception, e:
                        logger.exception('')
                        Monitor.RUNNING = False
                        break
                    self.cond.acquire()
                    self.cond.wait(self._interval)  # block until next collect

    #def set_reload_required(self):
        #self.CONT_FLAG = True
        #Monitor._LOADED = False

    def is_running(self):
        return Monitor.RUNNING

    def pause(self):
        self.cond.acquire()
        self.CONT_FLAG = False  # let the run loop stop
        self.cond.notify()
        self.cond.release()
        Monitor.RUNNING = False

    def halt(self):
        self.pause()
        self._teardown_send_channels()

    def reload_config(self):
        pass

    def _teardown_send_channels(self):
        self._channel.close()


class Collector(object):
    def __init__(self, mod_name):
        self.mod_name = mod_name
        mod = __import__(mod_name)  
        instance = getattr(mod, mod_name)()
        self.handler = instance.metric_handler
        self.update = instance.update
        logger.debug('Collector.__init__: %s, %s' % (self.handler, self.update))
        self.metrics = []
        self.last_collect = 0
    
    def set_metric_group(self, metrics):
        for metric in metrics:
            if metric["enabled"] == 1:
                self.metrics.append(metric)

    def add_metric(self, metric):
        pass
    
    def rm_metric(self, metric):
        pass

    def set_period(self, period):
        self.period = period

    def do_collect(self):
        #retval = []
        retval = {}
        self.update()
        for metric in self.metrics:
            #retval.append({ "name" : metric["name"],
                            #"val" : self.handler(metric["name"]) })#,
                            #"unit" : metric["unit"] })
            name = metric['name']
            retval[name] = self.handler(name)
        self.last_collect = time()
        #t_format = '%Y-%m-%d,%H:%M:%S'
        #retval.append({ "time" : strftime(t_format,gmtime(self.last_collect)) })
        #retval.append({ "time" : self.last_collect })
        retval['timestamp'] = self.last_collect
        logger.debug('do_collect:%s' % (retval,)) 
        return retval



def discover_server():
    global_config['remote_servers'][0]['host'] = \
            socket.gethostbyname(global_config['remote_servers'][0]['host'])
    logger.info('discovered server on %s' \
                % global_config['remote_servers'][0]['host'])
    return global_config['remote_servers']

@remote_call(5, 5)
def sign_into_server(server_addr, message):
    host = server_addr[0]
    port = server_addr[1]
    protocol = 'http'
    proxy = xmlrpclib.ServerProxy(protocol + "://" + host + ":" + str(port))
    return proxy.vm_sign_in(message)
   
def heartbeat(server_addr):
    is_server_down = False
    while True:
        ret = ping_server(server_addr)
        if ret[0]:
            logger.debug('pinged server. server returned %s' % ret[1])
            if is_server_down:
                controller.start_monitor()
                is_server_down = False
            sleep(60)
        else:
            if not is_server_down:
                logger.critical('center server down')
                controller.stop_monitor()
                is_server_down = True
            sleep(15)
            #break
    # TODO do something
    #shutdown()

@remote_call()
def ping_server(server_addr):
    proxy = xmlrpclib.ServerProxy('http://' + server_addr[0] + 
                              ':' + str(server_addr[1]))
    return proxy.ping()

#def start_controller_server():
    #logger.info("running server on port %d" % global_config["listen_channel"]["port"])
    #server = SimpleXMLRPCServer((get_ip_address('eth0'), \
                                 #global_config['listen_channel']['port']))
    #server.register_introspection_functions()
    #server.register_instance(Controller(global_config))
    #server.serve_forever()

def startup():

    #global global_config 
    global controller

    #global_config = load_config(DEFAULT_CONF)

    my_addr = get_ip_address('eth0')
    global_config['listen_channel']['host'] = my_addr

    server_addrs = discover_server()
    #t = threading.Thread(target=start_controller_server)
    #t.setDaemon(True)
    #t.setName('controller_server')
    #t.start()
    metadata = generate_metadata()
    logger.debug('%s' % (metadata,))
    sign = sign_into_server((server_addrs[0]['host'], 
                            server_addrs[0]['port']), encode(metadata))
    if not sign[0]:
        logger.critical('failed to connect to server %s, agent down'\
                        % (server_addrs[0],))
        sys.exit(1)
    elif not sign[1]:
        logger.critical('failed to sign in server %s, agent down' \
                        % (server_addrs[0],))
        sys.exit(1)

    logger.info('sign in server %s' % (server_addrs[0],))

    controller = Controller(global_config)
    controller.start_monitor()
    threadinglize(heartbeat)((server_addrs[0]['host'], server_addrs[0]['port']))

    logger.info("running mond on port %d" % global_config["listen_channel"]["port"])
    server = SimpleXMLRPCServer((global_config["listen_channel"]["host"], \
                                 global_config["listen_channel"]["port"]))
    server.register_introspection_functions()
    server.register_instance(controller)
    try:
        server.serve_forever()
    except KeyboardInterrupt, e:
        logger.info('mannuly shutdown')

def shutdown():
    controller.stop_monitor()

if __name__ == "__main__":
    startup()
