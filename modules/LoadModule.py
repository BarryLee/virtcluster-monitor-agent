from mon_module import MonModule

metric_list = [
    'load_one',
    'load_five',
    'load_fifteen'
]

class LoadModule(MonModule):

    proc_file_list = [
        {
            'name'  :   'loadavg',
            'path'  :   '/proc/loadavg'
        }]

    def update(self):
        super(LoadModule, self).update()
        self.set_val('loadavg', self.get_val('loadavg')[0][0].split())

    def get_load_one(self):
        return self.get_val('loadavg')[0]

    def get_load_five(self):
        return self.get_val('loadavg')[1]

    def get_load_fifteen(self):
        return self.get_val('loadavg')[2]
