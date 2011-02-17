from mon_module import MonModule

metric_list = [
    'load_one',
    'load_five',
    'load_fifteen'
]

class LoadModule(MonModule):

    data_sources = [
        {
            'name'  :   'loadavg',
            'path'  :   '/proc/loadavg',
            'type'  :   'string'
        }]

    def update(self):
        super(LoadModule, self).update()
        self.set_val('loadavg', self.get_val('loadavg').split())

    def get_load_one(self):
        return self.get_val('loadavg')[0]

    def get_load_five(self):
        return self.get_val('loadavg')[1]

    def get_load_fifteen(self):
        return self.get_val('loadavg')[2]

if __name__ == '__main__':
    import time
    ins = LoadModule()
    for i in range(5):
        print '%s    %s    %s' % (ins.metric_handler('load_one'), 
                                  ins.metric_handler('load_five'), 
                                  ins.metric_handler('load_fifteen'))
        time.sleep(2)
        ins.update()
