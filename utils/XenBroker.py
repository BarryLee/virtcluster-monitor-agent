import os
import re

from utils import *

def get_total_domU_memory(xm_path, xentop_path):
    return XenBroker(xm_path, xentop_path).getTotalDomUMemory()

def get_total_cpu_usage(xm_path, xentop_path):
    return XenBroker(xm_path, xentop_path).getTotalCPUUsage()

def get_xen_version(xm_path, xentop_path):
    return XenBroker(xm_path, xentop_path).getXenVersion()

def get_mem_total(xm_path, xentop_path):
    return XenBroker(xm_path, xentop_path).getTotalMemory()


class XenBrokerException(Exception): pass
    

class XenBroker(object):

    xentopDelay = 1

    xentopIters = 2

    def __init__(self, xm_path, xentop_path, dom0_min_mem=128):
        self.dom0MinMem = dom0_min_mem
        self._info = {}

        if os.getuid() != 0:
            prefix = 'sudo '
        else:
            prefix = ''

        self.xmCmd = prefix + xm_path
        self.xentopCmd = prefix + xentop_path

        self.xmInfo()

    def _xenCmd(self, cmd):
        try:
            return exec_cmd(cmd)
        except ExecCmdException, e:
            raise XenBrokerException, str(e)

    def update(self):
        self.updateDomainsBasicInfo()
        self.updateDomainsDynamicInfo()

    def xmInfo(self):
        xminfo = proc2dict(self._xenCmd(self.xmCmd + ' info'))
        self._info['mem_total'] = int(xminfo['total_memory']) * 1024
        self._info['version'] = '%s.%s%s' % (xminfo['xen_major'], 
                xminfo['xen_minor'], xminfo['xen_extra'])

    def updateDomainsBasicInfo(self):
        self._info['domains'] = self._parseXmListOutput(
                self._xenCmd(self.xmCmd + ' list'))
        
    def _parseXmListOutput(self, output):
        xmlist = []
        output = output.splitlines()
        caps = output[0].split()
        for l in output[1:]:
            d = {}
            l = l.split()
            for i in range(len(caps)):
                d[caps[i].strip()] = l[i].strip()
            xmlist.append(d)
        return xmlist

    def updateDomainsDynamicInfo(self):
        """exec xentop and get the updated info of:
            total allocated memory for guest domains,
            total CPU usage
        """
        xentop = self._parseXentopOutput(self._runXentop(self.xentopDelay, 
                self.xentopIters))

        dom0 = xentop['dom0detail']
        domUs = xentop['domUdetails']

        # dom[4] is the allocated memory for each dom, sum them up
        self._info['total_domU_memory'] = reduce(lambda x,y:x+y, [int(dom[4]) 
                for dom in domUs], 0)

        # sum up the 4th column for each domain(including domain-0), then divide
        # the sum of all 9th column. Still not sure this is the correct method
        total_cpu_usage = float(dom0[3])
        total_vcpus = int(dom0[8])
        for d in domUs:
            total_vcpus += int(d[8])
            total_cpu_usage += float(d[3])
        self._info['total_cpu_usage'] = round(total_cpu_usage / total_vcpus, 1)


    def _runXentop(self, delay=1, iterations=2):
        cmd = '%s -b -d %d -i %d' % (self.xentopCmd, delay, iterations)
        return self._xenCmd(cmd)

    def _parseXentopOutput(self, output):
        output = output.splitlines()
        olen = len(output)
        seg_start = []
        i = olen
        while i > 0:
            i -= 1
            if output[i].strip().startswith('NAME'):
                seg_start.append(i)
                break

        if len(seg_start) == 0:
            raise XenBrokerException, 'invalid output of xentop %s' % output

        output = output[seg_start[0]:]
        
        caps = output[0].split()
        dom0detail = []
        domUdetails = []
        for line in output[1:]:
            if line.strip().startswith('Domain-0 '):
                dom0detail = [i.strip() for i in 
                               re.split(r'(?<=[\w-]) +(?!limit)', line)]
                #dom0detail = [i.strip() for i in line.split()]
                #if len(dom0detail) == 18:
                    #dom0detail.pop(6)
            else:
                domUdetails.append([i.strip() for i in line.split()])

        result = {}
        result['dom0detail'] = dom0detail
        result['domUdetails'] = domUdetails

        return result


    def getXenVersion(self):
        return self._info['version']

    def getTotalMemory(self):
        return self._info['mem_total']
    
    def getTotalCPUUsage(self):
        try:
            return self._info['total_cpu_usage']
        except KeyError, e:
            self.updateDomainsDynamicInfo()
            return self._info['total_cpu_usage']

    def getTotalDomUMemory(self):
        try:
            return self._info['total_domU_memory']
        except KeyError, e:
            self.updateDomainsDynamicInfo()
            return self._info['total_domU_memory']


if __name__ == '__main__':
    xm_path = '/usr/sbin/xm'
    xentop_path = '/usr/sbin/xentop'

    xb = XenBroker(xm_path, xentop_path)
    #print xb._xenCmd('sudo xm list')
    #xb.updateDomainsBasicInfo()
    #print xb._info['domains']
    #print xb.getXenVersion()
    #print xb.getTotalCPUUsage()
    #print xb.getTotalDomUMemory()

    count = 5
    import time
    while count:
        xb.updateDomainsDynamicInfo()
        print xb.getTotalCPUUsage()
        #print get_total_cpu_usage(xm_path, xentop_path)
        #time.sleep(1)
        count -= 1
    #print get_xen_version(xm_path, xentop_path)
    #print get_total_cpu_usage(xm_path, xentop_path)
    #print get_total_domU_memory(xm_path, xentop_path)

