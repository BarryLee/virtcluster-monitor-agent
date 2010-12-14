import os.path
import subprocess
import re

from utils.utils import exec_cmd, proc2dict
from config.env_var import *

XEN_VIRTTYPE = 'xen'

def model():

    host = {}
    host['virt_type'] = get_virt_type()
    host['components'] = {}
    host['components']['cpu'] = get_cpu_info()
    host['components']['memory'] = get_mem_info()
    host['components']['filesystem'] = get_disk_info()
    host['components']['network'] = get_network_info()

    return host

def get_cpu_info():
    cpuinfopath = CPUINFO_PROC

    fd = open(cpuinfopath)
    cpuinfo = fd.read().strip().split('\n\n')
    fd.close()
    
    cpu = {}
    cpu['cpu_num'] = len(cpuinfo)
    processorinfo = dict([[i.strip() for i in pair] for pair in [l.split(':') \
                          for l in cpuinfo[0].split('\n')]])
    cpu['vendor_id'] = processorinfo['vendor_id']
    cpu['model_name'] = processorinfo['model name']
    cpu['cpu_MHz'] = processorinfo['cpu MHz']
    
    flags = processorinfo['flags'].split()
    if INTEL_VT_FLAG in flags:
        cpu['vt_support'] = INTEL_VT
    elif AMD_VT_FLAG in flags:
        cpu['vt_support'] = AMD_VT
    else:
        cpu['vt_support'] = None

    cpu['cache_size'] = processorinfo['cache size']

    cpu['width'] = ('lm' in flags) and 64 or 32
    
    return cpu

def get_virt_type():
    if os.path.exists(XEN_PROC):
        return XEN_VIRTTYPE
    else:
        return None

def get_mem_info():
    t = get_virt_type()
    if t is None:
        return get_phy_mem_info()
    else:
        return eval('get_%s_mem_info()' % t)

def get_phy_mem_info():
    fd = open(MEMINFO_PROC)
    memory = {}
    memory['mem_total'] = int(proc2dict(fd)['MemTotal'].split()[0])
    fd.close()
    return memory 

def get_xen_mem_info():
    from utils import XenBroker
    memory = {}
    memory['mem_total'] = XenBroker.get_mem_total(XM_PARH, XENTOP_PATH)
    return memory
    
def get_disk_info():
    disk = { 'local' : {},
             'other' : {} }

    # get info of mounted fs
    output = exec_cmd('df')
    mounts = [line.strip().split() for line in output.splitlines()][1:]
    for i in range(len(mounts)-1):
        if len(mounts[i]) < 6:
            mounts[i] += mounts[i+1]
            del mounts[i+1]

    # obtain info of all partitions
    fd = open('/proc/partitions')
    parts = [line.strip().split() for line in fd][2:]
    fd.close()
    #parts = map(lambda x: x[:-1]+['/dev/'+x[-1]], parts)

    for i in mounts:
        fsname = i[0]
        if fsname.startswith('/dev/'):
            fsname = fsname.rsplit('/')[-1]
            catagory = 'local'
        else:
            catagory = 'other'
        disk[catagory][fsname] = {}
        disk[catagory][fsname]['capacity'] = int(i[1])
        disk[catagory][fsname]['used'] = int(i[2])
        disk[catagory][fsname]['avail'] = int(i[3])
        disk[catagory][fsname]['usage'] = i[4]
        disk[catagory][fsname]['mounted_on'] = i[5]

    for i in parts:
        partname = i[-1]
        # skip disk
        if not partname[-1].isdigit():
            continue
        if not disk['local'].has_key(partname):
            disk['local'][partname] = {}
            disk['local'][partname]['capacity'] = int(i[2])

    return disk

def get_network_info():
    network = {}
    cmd = IFCONFIG_PATH
    #output = exec_cmd(IFCONFIG_PATH)
    #return ifconfig_parser(output)
    ifcfg = ifconfig_parser(exec_cmd(IFCONFIG_PATH))
    for i in ifcfg:
        network[i.pop('name')] = i

    return network

def ifconfig_parser(output):
    output = output.strip().split('\n\n')
    ifs = []
    for i in output:    # process each interface
        interface = {}
        lines = i.splitlines()
        fl = lines[0].strip().split()
        interface['name'], interface['hwaddr'] = fl[0], fl[-1]

        for line in lines[1:]:
            m = re.search('(?<= MTU:)\d+(?= )', line)
            if m is not None:
                interface['mtu'] = m.group(0)
                break   # our processing stops at this line

            m = re.findall('[^|(?<= )]\w+ *\w+: ?[^ ]+', line.strip())
            for field in m:
                #print field.split(':', 1)
                k, v = field.split(':', 1)
                k = k.lower().replace(' ', '_')
                # sometimes a interface has multiple address
                # (only need one of them)
                if interface.has_key(k):   
                    continue
                v = v.strip().lower()
                interface[k] = v

        ifs.append(interface)
    return ifs

def get_os_info():
    cmd = 'uname -sr'
    return exec_cmd(cmd).strip()    


if __name__ == '__main__':
    #print 'CPU:\n', get_cpu_info()
    #print
    #print 'OS:\n', get_os_info()
    #print
    #print 'Memory:\n', get_mem_info()
    #print 
    #print 'Disk:\n', get_disk_info()
    import pprint
    pp = pprint.PrettyPrinter(indent=2)
    
    pp.pprint(model())
