import logging
import logging.config
import os.path

from utils import current_dir

logging.config.fileConfig(current_dir(__file__) + os.path.sep + 'logging.conf')

def get_logger(name):
    return logging.getLogger(name)

if __name__ == '__main__':
    logger = logging.getLogger('this')
    count = 7
    while count:
        logger.error('asasfasaddsasfdvxcwergfgerterwf')
        count -= 1
