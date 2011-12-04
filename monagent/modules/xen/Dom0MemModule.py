from monagent.modules.linux.MemModule import MemModule

metric_list = ['dom0_cached',
               'dom0_mem_free',
               'dom0_buffers',
               'dom0_swap_total',
               'dom0_swap_cached',
               'dom0_swap_free']

class Dom0MemModule(MemModule):

    def get_dom0_cached(self):
        return super(Dom0MemModule, self).get_cached()

    def get_dom0_mem_free(self):
        return super(Dom0MemModule, self).get_mem_free()

    def get_dom0_buffers(self):
        return super(Dom0MemModule, self).get_buffers()

    def get_dom0_swap_total(self):
        return super(Dom0MemModule, self).get_swap_total()

    def get_dom0_swap_cached(self):
        return super(Dom0MemModule, self).get_swap_cached()

    def get_dom0_swap_free(self):
        return super(Dom0MemModule, self).get_swap_free()

