# -*- coding: utf-8 -*-
# platform: linux

import os.path

partitionfile = '/proc/partitions'
block_dir = '/sys/block'

def get_all_partitions():
    fd = open(partitionfile)
    parts = {}
    # skip first 2 lines
    fd.readline()
    fd.readline()
    for line in fd:
        temp = line.split()
        parts[temp[-1]] = map(lambda x: int(x), temp[0:-1])
    fd.close()
    return parts


def get_disk_partition():
    partordisks = get_all_partitions().keys()
    ret = {}
    for i in partordisks:
        temp_path = block_dir+'/'+i
        if os.path.exists(temp_path):
            #ret[i] = []
            parts = [f for f in os.listdir(temp_path) if f in partordisks]
            ret[i] = parts
    return ret
    

def get_partition_disk():
    diskparts = get_disk_partition()
    ret = {}
    for d, parts in diskparts.items():
        for p in parts:
            ret[p] = d
    return ret

if __name__ == '__main__':
    from utils import _print
    _print(get_all_partitions())
    _print(get_disk_partition())
    _print(get_partition_disk())
