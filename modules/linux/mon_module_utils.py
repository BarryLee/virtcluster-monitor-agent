#-*- coding:utf-8 -*-
import os

def file2list(path):
    fd = open(path, 'r')
    lst = [[i.strip() for i in pair] for pair in [line.split(':') \
                        for line in fd if line.strip() != '']] 
    fd.close()
    return lst

def file2string(path):
    fd = open(path, 'r')
    astr = fd.read()
    fd.close()
    return astr

def system_(cmd):
    fd = os.popen(cmd)
    output = fd.read()
    fd.close()
    return output

def getDictDeeply(dict_, keys):
    ret = dict_
    if type(keys) is str:
        ret = dict_[keys]
    else:
        keys = list(keys)
        for i in keys:
            ret = ret[i]

    return ret

def setDictDeeply(dict_, keys, val, createMidNodes=False):
    if type(keys) is str:
        dict_[keys] = val
    else:
        keys = list(keys)
        midKeys = keys[0:-1]
        theKey = keys[-1]
        sub = dict_
        for i in midKeys:
            try:
                sub = sub[i]
            except KeyError, e:
                if createMidNodes:
                    sub[i] = {}
                    sub = sub[i]
                else:
                    raise
        sub[theKey] = val


if __name__ == '__main__':
    import unittest

    class test_util(unittest.TestCase):

        def testFile2List(self):
            ret = file2list('/proc/cpuinfo')
            print ret

        def testGetDictDeeply(self):
            test = { '1': { '2': { '3': 4 } } }
            self.assertEquals(test['1']['2']['3'], \
                              getDictDeeply(test, ('1', '2', '3')))
            self.assertEquals(test['1'], \
                              getDictDeeply(test, '1'))

        def testSetDictDeeply(self):
            test = {}
            setDictDeeply(test, (1, 2, 3), 4, True)
            self.assertEquals(test[1][2][3], 4)
            setDictDeeply(test, (1, 2, 3), 'phsyco')
            self.assertEquals(test[1][2][3], 'phsyco')
            self.assertRaises(KeyError, setDictDeeply, test, (1,2,4,5), '')

    
    unittest.main()
