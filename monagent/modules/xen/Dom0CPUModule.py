from monagent.modules.linux.CPUModule import CPUModule

metric_list = ['dom0_cpu_user', 
               'dom0_cpu_nice', 
               'dom0_cpu_system', 
               'dom0_cpu_iowait',
               'dom0_cpu_irq', 
               'dom0_cpu_softirq']

class Dom0CPUModule(CPUModule):
    def get_dom0_cpu_user(self):
        return super(Dom0CPUModule, self).get_cpu_user()

    def get_dom0_cpu_nice(self):
        return super(Dom0CPUModule, self).get_cpu_nice()

    def get_dom0_cpu_system(self):
        return super(Dom0CPUModule, self).get_cpu_system()

    def get_dom0_cpu_iowait(self):
        return super(Dom0CPUModule, self).get_cpu_iowait()

    def get_dom0_cpu_irq(self):
        return super(Dom0CPUModule, self).get_cpu_irq()

    def get_dom0_cpu_softirq(self):
        return super(Dom0CPUModule, self).get_cpu_softirq()

if __name__ == '__main__':
    ins = Dom0CPUModule()
    cnt = 10
    while cnt > 0:
        ins.update()
        for i in metric_list:
            print '%s:%s' % (i, ins.metric_handler(i))
        print 
        #ins.update()
        #print ins.metric_handler('cpu_system')
        from time import sleep
        cnt -= 1
        sleep(1)
