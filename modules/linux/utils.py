#-*- coding:utf-8 -*-
import os


def file2list(path):
    with open(path) as fd:
        return [l for l in [line.strip() for line in fd] if l != '']


def file2string(path):
    fd = open(path, 'r')
    astr = fd.read()
    fd.close()
    return astr


def file2dict(path, delimiter=':'):
    with open(path, 'r') as fd:
        return dict([[i.strip() for i in pair] for pair in [line.split(delimiter, 1)
                for line in fd] if len(pair) == 2])
        #return dict([[i.strip() for i in pair] for pair in [line.split(delimiter, 1) 
                #for line in fd if line.strip() != '']])
 

def get_from_dict(dict_, keys):
    ret = dict_
    if type(keys) is str:
        ret = dict_[keys]
    else:
        keys = list(keys)
        for i in keys:
            ret = ret[i]

    return ret


def put_to_dict(dict_, keys, val, createMidNodes=False):
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



