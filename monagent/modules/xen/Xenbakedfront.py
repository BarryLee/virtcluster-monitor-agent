import mmap
import struct
import os
import time

# constants
NSAMPLES = 100
NDOMAINS = 32
IDLE_DOMAIN = -1 # idle domain's ID

# the struct strings for qos_info
ST_DOM_INFO = "6Q3i2H32s"
ST_QDATA = "%dQ" % (6*NDOMAINS + 4)

# size of mmaped file
QOS_DATA_SIZE = struct.calcsize(ST_QDATA)*NSAMPLES + struct.calcsize(ST_DOM_INFO)*NDOMAINS + struct.calcsize("4i")

# location of mmaped file, hard coded right now
if os.path.exists('/var/run/xenq-shm'):
    SHM_FILE = "/var/run/xenq-shm"
else:
    SHM_FILE = "/tmp/xenq-shm"


if os.uname()[0] == "SunOS":
    xenbaked_cmd = "sudo /usr/lib/xenbaked"
    stop_cmd = "sudo /usr/bin/pkill -INT -z global xenbaked"
    kill_cmd = "sudo /usr/bin/pkill -KILL -z global xenbaked"
else:
    # assumes that xenbaked is in your path
    xenbaked_cmd = "sudo xenbaked"
    stop_cmd = "sudo /usr/bin/pkill -INT xenbaked"
    kill_cmd = "sudo /usr/bin/pkill -KILL xenbaked"

mspersample = 100
interval = 1000

# start xenbaked
def start_xenbaked():
    global mspersample
    global kill_cmd
    global xenbaked_cmd

    os.system(kill_cmd)
    os.system(xenbaked_cmd + " --ms_per_sample=%d >/dev/null 2>/dev/null &" %
              mspersample)
    time.sleep(1)

# stop xenbaked
def stop_xenbaked():
    global stop_cmd
    os.system(stop_cmd + " >/dev/null 2>/dev/null &")

# encapsulate information about a domain
class DomainInfo:
    def __init__(self):
        self.allocated_sum = 0
        self.gotten_sum = 0
        self.blocked_sum = 0
        self.waited_sum = 0
        self.exec_count = 0;
        self.iocount_sum = 0
        self.ffp_samples = []

    def gotten_stats(self, passed):
        total = float(self.gotten_sum)
        per = 100*total/passed
        exs = self.exec_count
        if exs > 0:
            avg = total/exs
        else:
            avg = 0
        return [total/(float(passed)/10**9), per, avg]

    def waited_stats(self, passed):
        total = float(self.waited_sum)
        per = 100*total/passed
        exs = self.exec_count
        if exs > 0:
            avg = total/exs
        else:
            avg = 0
        return [total/(float(passed)/10**9), per, avg]

    def blocked_stats(self, passed):
        total = float(self.blocked_sum)
        per = 100*total/passed
        ios = self.iocount_sum
        if ios > 0:
            avg = total/float(ios)
        else:
            avg = 0
        return [total/(float(passed)/10**9), per, avg]

    def allocated_stats(self, passed):
        total = self.allocated_sum
        exs = self.exec_count
        if exs > 0:
            return float(total)/exs
        else:
            return 0

    def ec_stats(self, passed):
        total = float(self.exec_count/(float(passed)/10**9))
        return total

    def io_stats(self, passed):
        total = float(self.iocount_sum)
        exs = self.exec_count
        if exs > 0:
            avg = total/exs
        else:
            avg = 0
        return [total/(float(passed)/10**9), avg]

    def stats(self, passed):
        return [self.gotten_stats(passed), self.allocated_stats(passed), self.blocked_stats(passed), 
                self.waited_stats(passed), self.ec_stats(passed), self.io_stats(passed)]

# report values over desired interval
def summarize(startat, endat, duration, samples):
    dominfos = {}
    for i in range(0, NDOMAINS):
        dominfos[i] = DomainInfo()
        
    passed = 1              # to prevent zero division
    curid = startat
    numbuckets = 0
    lost_samples = []
    ffp_samples = []
    
    while passed < duration:
        for i in range(0, NDOMAINS):
            if dom_in_use[i]:
                dominfos[i].gotten_sum += samples[curid][0*NDOMAINS + i]
                dominfos[i].allocated_sum += samples[curid][1*NDOMAINS + i]
                dominfos[i].waited_sum += samples[curid][2*NDOMAINS + i]
                dominfos[i].blocked_sum += samples[curid][3*NDOMAINS + i]
                dominfos[i].exec_count += samples[curid][4*NDOMAINS + i]
                dominfos[i].iocount_sum += samples[curid][5*NDOMAINS + i]
    
        passed += samples[curid][6*NDOMAINS]
        lost_samples.append(samples[curid][6*NDOMAINS + 2])
        ffp_samples.append(samples[curid][6*NDOMAINS + 3])

        numbuckets += 1

        if curid > 0:
            curid -= 1
        else:
            curid = NSAMPLES - 1
        if curid == endat:
            break

    lostinfo = [min(lost_samples), sum(lost_samples), max(lost_samples)]
    ffpinfo = [min(ffp_samples), sum(ffp_samples), max(ffp_samples)]

    ldoms = []
    for x in range(0, NDOMAINS):
        if dom_in_use[x]:
            ldoms.append(dominfos[x].stats(passed))
        else:
            ldoms.append(0)

    return [ldoms, lostinfo, ffpinfo]

# scale microseconds to milliseconds or seconds as necessary
def time_scale(ns):
    if ns < 1000:
        return "%4.2f ns" % float(ns)
    elif ns < 1000*1000:
        return "%4.2f us" % (float(ns)/10**3)
    elif ns < 10**9:
        return "%4.2f ms" % (float(ns)/10**6)
    else:
        return "%4.2f s" % (float(ns)/10**9)

def update():
    ncpu = 1         # number of cpu's on this platform
    slen = 0         # size of shared data structure, incuding padding
    global dom_in_use
    global domain_id
    allinfo = []

    # mmap the (the first chunk of the) file
    shmf = open(SHM_FILE, 'r')
    shm = mmap.mmap(shmf.fileno(), QOS_DATA_SIZE, access=mmap.ACCESS_COPY)

    cpuidx = 0
    while cpuidx < ncpu:

        # calculate offset in mmap file to start from
        idx = cpuidx * slen

        samples = []
        doms = []
        dom_in_use = []
        domain_id = []

        # read in data
        for i in range(0, NSAMPLES):
            qlen = struct.calcsize(ST_QDATA)
            sample = struct.unpack(ST_QDATA, shm[idx:idx+qlen])
            samples.append(sample)
            idx += qlen

        #print 'samples:', samples

        for i in range(0, NDOMAINS):
            qlen = struct.calcsize(ST_DOM_INFO)
            dom = struct.unpack(ST_DOM_INFO, shm[idx:idx+qlen])
            doms.append(dom)

            (last_update_time, start_time, runnable_start_time, blocked_start_time,
            ns_since_boot, ns_oncpu_since_boot, runnable_at_last_update,
            runnable, in_use, domid, junk, name) = dom

            dom_in_use.append(in_use)
            if domid == 32767 :
                domid = IDLE_DOMAIN
            domain_id.append(domid)
            idx += qlen
        
        #print 'dom_in_use:', dom_in_use
        #print 'domain_id:', domain_id

        qlen = struct.calcsize("4i")
        oldncpu = ncpu
        (next, ncpu, slen, freq) = struct.unpack("4i", shm[idx:idx+qlen])
        idx += qlen

        #print 'ncpu:', ncpu

        # xenbaked tells us how many cpu's it's got, so re-do
        # the mmap if necessary to get multiple cpu data
        if oldncpu != ncpu:
            shm = mmap.mmap(shmf.fileno(), ncpu*slen, access=mmap.ACCESS_COPY)


        # calculate starting and ending datapoints; never look at "next" since
        # it represents live data that may be in transition. 
        startat = next - 1
        if next + 10 < NSAMPLES:
            endat = next + 10
        else:
            endat = 10

        # get summary over desired interval
        [h1, l1, f1] = summarize(startat, endat, interval * 10**6, samples)
        #print h1
        #print l1
        #print f1
        
        allinfo.append([h1, l1, f1]) 

        cpuidx = cpuidx + 1

    shm.close()
    shmf.close()
    return allinfo

def test():
    while True:
        allinfo = update()
        rncpu = len(allinfo)
        for i in range(rncpu):
            [h, l, f] = allinfo[i]
            print 'cpu %d:' % i
            for dom in range(0, NDOMAINS):
                if not dom_in_use[dom]:
                    continue

                # display gotten
                print '%4s  %-14s%-10s%-14s%-14s' % \
                    (displayed_domid(domain_id[dom]),
                     time_scale(h[dom][0][0]),
                     '%3.2f%%' % h[dom][0][1],
                     '%s/ex' % time_scale(h[dom][0][2]),
                     'Gotten')

                # display allocated
                print '%4s%26s%-14s%-14s' % \
                    (displayed_domid(domain_id[dom]),
                     '',
                     '%s/ex' % time_scale(h[dom][1]),
                     'Allocated')

                # display blocked
                print '%4s  %-14s%-10s%-14s%-14s' % \
                    (displayed_domid(domain_id[dom]),
                     time_scale(h[dom][2][0]),
                     '%3.2f%%' % h[dom][2][1],
                     '%s/io' % time_scale(h[dom][2][2]),
                     'Blocked')

                # display waited
                print '%4s  %-14s%-10s%-14s%-14s' % \
                    (displayed_domid(domain_id[dom]),
                     time_scale(h[dom][3][0]),
                     '%3.2f%%' % h[dom][3][1],
                     '%s/io' % time_scale(h[dom][3][2]),
                     'Waited')

                # display ex count
                print '%4s%26s%-14s%-14s' % \
                    (displayed_domid(domain_id[dom]),
                     '',
                     '%d/s' % h[dom][4],
                     'Execution Count')
                    
                # display io count
                print '%4s  %-14s%-10s%-14s%-14s' % \
                    (displayed_domid(domain_id[dom]),
                     '%d/s' % h[dom][5][0],
                     '',
                     '%3.2f/ex' % h[dom][5][1],
                     'I/O Count')


        time.sleep(5)

def displayed_domid(id):
    if id == -1:
        return 'IDLE'
    else:
        return str(id)

def main():
    start_xenbaked()
    try:
        test()
    except KeyboardInterrupt:
        print 'Quitting.'
    stop_xenbaked()

if __name__ == '__main__':
    main()
