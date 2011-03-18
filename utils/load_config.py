# -*- coding: utf-8 -*-

import os.path

from configobj import ConfigObj

from utils import encode, decode, parent_dir

#_ = lambda f: os.path.dirname(os.path.abspath(f))

config_dir = parent_dir(__file__) + os.path.sep + 'config'
#config_dir = _(_(__file__)) + os.path.sep + 'config'
GLOBAL_CONFIG = config_dir + os.path.sep + 'agent.conf'
METRIC_CONFIG = config_dir + os.path.sep + 'metric.conf'
METRIC_LIST = config_dir + os.path.sep + 'metric.list'
DEFAULT_METRIC_LIST = config_dir + os.path.sep + 'metric.list.default'

#print GLOBAL_CONFIG

#def load_config():
    #exec(compile(open(GLOBAL_CONFIG).read(), GLOBAL_CONFIG, 'exec'))
    #return locals()


def load_config(filename):
    return ConfigObj(filename)


def load_global_config():
    return ConfigObj(GLOBAL_CONFIG)


def load_metric_list():
    #if not os.path.exists(METRIC_LIST):
    try:    
        fp = open(METRIC_LIST)
        ml = decode(fp.read())
        fp.close()
        return ml
    except Exception, e:
        def handle_device(device, metric_group, unmonitored_list):
            if device not in unmonitored_list:
                if not metric_group.has_key('instances'):
                    metric_group['instances'] = []
                metric_group['instances'].append({'device': device})

        from platform_info import get_network_info
        ifs = get_network_info().keys()

        from block import get_disk_partition
        disk_parts = get_disk_partition()

        metric_conf = load_config(METRIC_CONFIG)
        #df = open(metric_conf['default_list'])
        df = open(DEFAULT_METRIC_LIST)
        default_list = decode(df.read())
        df.close()
        
        new_list = default_list
        for metric_group in iter(new_list['metric_groups']):
            name = metric_group['name']
            if name == 'NetModule':
                total = metric_conf['network']['total']
                if len(total):
                    handle_device(total, metric_group, [])

                unmonitored_ifs = metric_conf['network']['black_list']
                for iname in ifs:
                    handle_device(iname, metric_group, unmonitored_ifs)

            elif name == 'DiskModule':
                unmonitored_parts = metric_conf['disk']['black_list']
                enable_partitions = int(metric_conf['disk']['enable_partitions'])
                for dname, dparts in disk_parts.iteritems():
                    handle_device(dname, metric_group, unmonitored_parts)
                    if enable_partitions:
                        for pname in dparts:
                            handle_device(pname, metric_group, unmonitored_parts)
                        
        fp = open(METRIC_LIST, 'w')
        fp.write(encode(new_list, True))
        fp.close()
        return new_list


if __name__ == '__main__':
    print load_metric_list()
