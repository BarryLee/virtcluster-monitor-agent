import logging
import logging.handlers

LOG_FILE = '/tmp/mon_agent.log'

#logging.basicConfig(level=logging.DEBUG,
                    #datefmt='%m-%d %H:%M:%S')

logger = logging.getLogger('agent')
logger.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)

fileHandler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=2*2**20, backupCount=2)
fileHandler.setLevel(logging.DEBUG)

simpleFormatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s: %(message)s')
verboseFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s: %(message)s')

consoleHandler.setFormatter(simpleFormatter)
fileHandler.setFormatter(verboseFormatter)

logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)

def instance():
    return logger

if __name__ == '__main__':
    lg = instance()
    lg.debug('debug')
    lg.info('info')

