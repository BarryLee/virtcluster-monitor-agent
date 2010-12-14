from SocketServer import ThreadingTCPServer
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher, SimpleXMLRPCRequestHandler
try:
    import fcntl
except ImportError:
    fcntl = None

class Singleton(object):

    _instance = None

    def __new__(cls, *args, **kargs):
        #return cls._getInstance()
        return cls._getInstance(*args, **kargs)

    @classmethod
    def _getInstance(cls, *args, **kargs):
    #def _getInstance(cls):
        # Check to see if a __single exists already for this class
        # Compare class types instead of just looking for None so
        # that subclasses will create their own __single objects
        if type(cls._instance) is not cls:
            cls._instance = object.__new__(cls)
            #import weakref
            #ins = object.__new__(cls)
            #cls._instance = weakref.ref(ins)
            #return ins
            #cls._instance.init(*args, **kargs)
        return cls._instance

    #def init(self, *args, **kargs):
        #"""may be overriden.
        #"""
        #pass

class ThreadingXMLRPCServer(ThreadingTCPServer, SimpleXMLRPCDispatcher):
    
    allow_reuse_address = True
    
    # Warning: this is for debugging purposes only! Never set this to True in
    # production code, as will be sending out sensitive information (exception
    # and stack trace details) when exceptions are raised inside
    # SimpleXMLRPCRequestHandler.do_POST
    _send_traceback_header = False

    def __init__(self, addr, requestHandler=SimpleXMLRPCRequestHandler,
                 logRequests=True, allow_none=False, encoding=None, bind_and_activate=True):
        self.logRequests = logRequests

        SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)
        ThreadingTCPServer.__init__(self, addr, requestHandler, bind_and_activate)

        # [Bug #1222790] If possible, set close-on-exec flag; if a
        # method spawns a subprocess, the subprocess shouldn't have
        # the listening socket open.
        if fcntl is not None and hasattr(fcntl, 'FD_CLOEXEC'):
            flags = fcntl.fcntl(self.fileno(), fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(self.fileno(), fcntl.F_SETFD, flags)

class MonAgentException(Exception):
    pass
