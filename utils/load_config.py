# -*- coding: utf-8 -*-

import os.path

from utils import parent_direcroty

DEFAULT_CONFIG = parent_direcroty(__file__) + os.path.sep + 'agentrc'

#print DEFAULT_CONFIG

def load_config():
    exec(compile(open(DEFAULT_CONFIG).read(), DEFAULT_CONFIG, 'exec'))
    return locals()

if __name__ == '__main__':
    print load_config()