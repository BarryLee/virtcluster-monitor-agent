import sys
import os
from utils.utils import get_ip_address, encode

curdir = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = curdir + os.path.sep + 'modules'
sys.path.append(MODULE_DIR)

standard_module_set = ('CPUModule', 'MemModule', 'LoadModule', 'NetModule')
xen_platform_module_set = ('CPUModule', 'MemModule', 'NetModule')

moduleprefix = ''

briefs = ('cpu', 'vmm', 'os', 'vt')

def generate_metric_groups(module_set):
    metric_groups = []
    for module in module_set:
        modname = moduleprefix + module
        mod = __import__(modname)
        metric_group = {}
        metric_group['name'] = modname
        metric_group['metrics'] = []
        for metric in mod.metric_list:
            metricspec = {}
            metricspec['name'] = metric
            tmp = metric.split('_')
            for i in range(len(tmp)):
                if tmp[i] in briefs:
                    tmp[i] = tmp[i].upper()
            metricspec['title'] = ' '.join(tmp)
            # determine the unit
            if modname.find('Mem') != -1:
                if metric == 'mem_usage':
                    metricspec['unit'] = 'pct'
                else:
                    metricspec['unit'] = 'kB'
            elif modname.find('CPU') != -1 or modname.find('Load') != -1:
                metricspec['unit'] = 'pct'
            elif modname.find('Net') != -1:
                if metric.find('byte') != -1:
                    metricspec['unit'] = 'B/s'
                elif metric.find('packet') != -1:
                    metricspec['unit'] = 'pkt/s'
            else:
                metricspec['unit'] = None
            #metricspec['type'] = 'discrete' # for now we don't have a second type
            metricspec['enabled'] = 1 # enable all by default
            metric_group['metrics'].append(metricspec)
        # determine the collecting period of this module
        if module in intensively_collect:
            metric_group['period'] = intensive_period
        else:
            metric_group['period'] = loose_period

        metric_group['consolidation_intervals'] = [60, 600, 900, 1800, 3600]
        metric_groups.append(metric_group)
    return metric_groups

##############################
# generate basic_info configs
##############################

basic_info = []
platform_module = moduleprefix + 'PlatformInfo'
mod = __import__(platform_module)
modspec = {}
modspec['name'] = platform_module
modspec['title'] = 'Platform Info'
modspec['metrics'] = []
for metric in mod.metric_list:
    metricspec = {}
    metricspec['name'] = metric
    tmp = metric.split('_')
    for i in range(len(tmp)):
        if tmp[i] in briefs:
            tmp[i] = tmp[i].upper()
    metricspec['title'] = ' '.join(tmp)
    metricspec['unit'] = None
    metricspec['enabled'] = 1
    modspec['metrics'].append(metricspec)

basic_info.append(modspec)


##############################
# generate metric_groups
##############################

intensively_collect = ('CPUModule', 'MemModule')
loosely_collect = ('LoadModule', 'NetModule')

intensive_period = 15
loose_period = 15

if moduleprefix == '':
    metric_groups = generate_metric_groups(standard_module_set)
else:
    metric_groups = generate_metric_groups(xen_platform_module_set)
   

#########################
# generate other configs
#########################

ip = get_ip_address('eth0')

remote_servers = [
    { 
        'host' : '10.0.0.11',
        'port' : 20060
    }
]

listen_channel = {
    'port' : 20070
}

collect_interval = 5

#ofile = curdir + os.path.sep + 'mon_agent.out'
#pfile = curdir + os.path.sep + 'mon_agent.pid'
ofile = '/tmp/mon_agent.out'
pfile = '/tmp/mon_agent.pid'

logfile = '/tmp/mon_agent.log'

###################
# merge everything
###################

all = { 
    'ofile'         :   ofile,
    'pfile'         :   pfile,
    'logfile'       :   logfile,
    'basic_info'    :   basic_info,
    'metric_groups' :   metric_groups, 
    'remote_servers':   remote_servers,
    'listen_channel':   listen_channel,
    'collect_interval'  :   collect_interval
}


if __name__ == '__main__':
    config_path = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + \
            'agent_default_config' 
    fp = file(config_path, 'w+')
    s = encode(all)
    fp.write(s)
    fp.close()
