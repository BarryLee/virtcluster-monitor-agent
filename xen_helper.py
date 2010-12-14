import os
import re
import fcntl
import select
import subprocess

from mon_common import *
from mon_base import MonDaemonException

def exec_and_copy(cmd):
    p = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE, \
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o = p.stdout
    fd = o.fileno()
    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    epoll = select.epoll()
    epoll.register(fd, select.EPOLLIN)
    while True:
        #print rs
        events = epoll.poll()
        for fileno, event in events:
            if fileno == fd:
                data = ''
                while True:
                    try:
                        output = o.readline()
                        if not output:
                            break
                        data += output
                    except IOError, e:
                        #print e
                        break
                retcode = p.poll()
                yield data, retcode
                #print data, retcode
                if retcode is not None:
                    break

def get_xen_version():
    return xentop2list()['vmm_version']

#def run_xentop(delay):
    #cmd = 'sudo %s -b -d %d' % (xentop_path, delay)
    #for r in exec_and_copy(cmd):
        #yield r
def run_xentop(delay, iterations=None):
    cmd = 'sudo %s -b -d %d' % (xentop_path, delay)
    if iterations is not None:
        cmd += ' -i %s' % iterations
    try:
        ret = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, \
                stderr=subprocess.PIPE).communicate()[0]
        return ret
    except OSError, e:
        #logger.exception('')
        raise MonDaemonException, 'failed to exec xentop'
    
def xentop2list_(output):
    output = output.splitlines()
    olen = len(output)
    seg_start = []
    i = olen
    while i > 0:
        i -= 1
        if output[i].strip().startswith('xentop'):
            seg_start.append(i)
            break

    if len(seg_start) == 0:
        raise MonDaemonException, 'invalid output of xentop %s' % output

    output = output[seg_start[0]:]
    
    title = output[0].split()
    domsum = output[1]
    memcpu = output[2].split()
    caps = output[3].split()
    dom0detail = []
    domUdetails = []
    for line in output[4:]:
        if line.strip().startswith('Domain-0 '):
            dom0detail = [i.strip() for i in 
                           re.split(r'(?<=[\w-]) +(?!limit)', line)]
        else:
            domUdetails.append([i.strip() for i in line.split()])

    #dom0detail = [i.strip() for i in re.split(r'(?<=[\w-]) +(?!limit)', \
                                      #output[4])]
    #domUdetails = [line.split() for line in output[5:]]

    result = {}
    result['vmm_version'] = title[-1]
    result['memtotal'] = memcpu[1]
    result['memused'] = memcpu[3]
    result['memfree'] = memcpu[5]
    result['dom0detail'] = dom0detail
    result['domUdetails'] = domUdetails

    return result

def xentop2list():
    return xentop2list_(run_xentop(1, 1))
    #fd = os.popen('sudo %s -b -d 1 -i 1' % xentop_path)
    
    #general = fd.readline().split()
    #if len(general) == 0:
        #raise MonDaemonException, 'failed to exec xentop'
    #fd.readline()
    #memcpu = fd.readline().split()
    #caps = fd.readline().split() 
    #dom0detail = [i.strip() for i in re.split(r'(?<=[\w-]) +(?!limit)', \
                                      #fd.readline())]
    #domUdetails = [line.split() for line in fd]

    #fd.close()

    #result = {}
    #result['vmm_version'] = general[-1]
    #result['memtotal'] = memcpu[1]
    #result['memused'] = memcpu[3]
    #result['memfree'] = memcpu[5]
    #result['dom0detail'] = dom0detail
    #result['domUdetails'] = domUdetails

    #return result

def get_total_domU_memory():
    domUs = xentop2list()['domUdetails']
    ret = 0
    for dom in domUs:
        ret += int(dom[4])

    return ret

def get_total_domU_memory_used():
    domUs = xentop2list()['domUdetails']
    ret = 0
    for dom in domUs:
        ret += float(dom[4]) * float(dom[5]) * 0.01

    return int(ret)

def get_total_cpu_usage():
    total_vcpus = 0
    total_dom_cpu_usage = 0.0
    output = run_xentop(1, 2)
    #print output
    xt = xentop2list_(output)
    total_vcpus += int(xt['dom0detail'][8])
    total_dom_cpu_usage += float(xt['dom0detail'][3])
    for d in xt['domUdetails']:
        total_vcpus += int(d[8])
        total_dom_cpu_usage += float(d[3])
    return round(total_dom_cpu_usage / total_vcpus, 1)


if __name__ == '__main__':
    #print get_total_cpu_usage()
    out = run_xentop(1, 2)
    print out.split('xentop')

