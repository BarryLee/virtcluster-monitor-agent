from monagent.modules.linux.LoadModule import LoadModule

metric_list = ['dom0_load_one',
               'dom0_load_five',
               'dom0_load_fifteen']

class Dom0LoadModule(LoadModule):

    def get_dom0_load_one(self):
        return super(Dom0LoadModule, self).get_load_one()

    def get_dom0_load_five(self):
        return super(Dom0LoadModule, self).get_load_five()

    def get_dom0_load_fifteen(self):
        return super(Dom0LoadModule, self).get_load_fifteen()

