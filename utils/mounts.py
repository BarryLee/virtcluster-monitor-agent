# -*- coding: utf-8 -*-
"""Retrive info of filesystem, disk usage and mount points, etc

This module is derived from pydf by Radovan Garabík 
<garabik @ kassiopeia.juls.savba.sk>
http://kassiopeia.juls.savba.sk/~garabik/software/pydf/
"""
import sys, os
from utils import subprocess

mountfile = ['/etc/mtab', '/etc/mnttab', '/proc/mounts']


class DumbStatus(object):
    "emulates statvfs results with only zero values"
    f_bsize = f_frsize = f_blocks = f_bfree = f_bavail = f_files = f_ffree = f_favail = f_flag = f_namemax =0


def get_all_mountpoints():
    "return all mountpoints in fs"

    # fallback when nothing else works
    dummy_result = {'/': ('/', '')}

    if isinstance(mountfile, str):
        f = open(mountfile,"rb")
    else:
        for i in mountfile:
            if os.path.exists(i):
                f = open(i,"rb")
                break
        else:
            # fallback, first try to parse mount output
            status, mout = subprocess.getstatusoutput('mount')
            if status != 0:
                return dummy_result
            mlines = mout.split('\n')
            r = {}
            for line in mlines:
                if not ' on ' in line:
                    continue
                device, on = line.split(' on ', 1)
                device = device.split()[0]
                onparts = on.split()
                on = onparts[0]
                # option format: (a,b,..)
                opts = onparts[-1][1:-1].split(',')
                r[on] = (device, '', opts)

            if r:
                return r
            else:
                return dummy_result

    mountlines = f.readlines() # bytes in python3

    # convert to representable strings (for python3)
    # unfortunately, we cannot keep it as bytes, because of a known bug
    # in python3 forcing us to use string, not bytes as filename for os.statvfs
    if sys.version_info[0]>=3:
        mountlines = [x.decode(sys.stdin.encoding, 'replace') for x in mountlines]
    r = {}
    for l in mountlines:
        spl = l.split()
        if len(spl)<4:
            print("Error in", mountfile)
            print(repr(l))
            continue
        device, mp, typ, opts = spl[0:4]
        opts = opts.split(',')
        r[mp] = (device, typ, opts)
    return r


def is_remote_fs(fs):
    "test if fs (as type) is a remote one"
    fs = fs.lower()
    return fs in [ "nfs", "smbfs", "cifs", "ncpfs", "afs", "coda", "ftpfs", "mfs", "sshfs", "fuse.sshfs" ]


def is_special_fs(fs):
    "test if fs (as type) is a special one"
    "in addition, a filesystem is special if it has number of blocks equal to 0"
    fs = fs.lower()
    return fs in [ "tmpfs", "devpts", "proc", "sysfs", "usbfs" ]


def is_local_fs(fs):
    return not (is_special_fs(fs) or is_remote_fs(fs))


def myformat(number, sizeformat, fs_blocksize):
    "format number as file size. fs_blocksize here is a filesysem blocksize"
    size = int(number)*fs_blocksize
    if sizeformat == "-k":
        sn = round(size/1024.)
        sn = int(sn)
        return sn
    elif sizeformat == "-m":
        sn = round(size/(1024.*1024))
        sn = int(sn)
        return sn
    elif sizeformat == "-g":
        sn = round(size/(1024.*1024*1024))
        sn = int(sn)
        return sn
    elif sizeformat == "--blocks":
        return int(number)
    else: # this should not happen
        raise ValueError("Impossible error, contact the author, sizeformat="+repr(sizeformat))


def get_mp_stat(mp):
    if mp:
        try:
            status = os.statvfs(mp)
        except (OSError, IOError):
            status = DumbStatus()
        fs_blocksize = status.f_bsize
        if fs_blocksize == 0:
            fs_blocksize = status.f_frsize
        free = status.f_bfree
        size = status.f_blocks
        avail = status.f_bavail
        #inodes_free = status.f_ffree
        #inodes_size = status.f_files
        #inodes_avail = status.f_favail

        used = size-free

        return {
            'blocksize' : fs_blocksize,
            'size'   :    size,
            'used'   :    used,
            'avail'  :    avail,
            }



if __name__ == "__main__":
    mountpoints = get_all_mountpoints()
    #print mountpoints
    print [mountpoints[x][1] for x in mountpoints.keys() if not (is_remote_fs(mountpoints[x][1]) or is_special_fs(mountpoints[x][1]))]


