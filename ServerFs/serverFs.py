#!/usr/bin/env python
import Skype4Py
import time
import os
from errno import EACCES
from os.path import realpath
from threading import Lock
import base64
import pickle

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

class ServerFs:

    def __init__(self, rootPath):
        # instatinate Skype object and set our event handlers
        skype = Skype4Py.Skype(Events=self, Transport='x11')
        # attach to Skype client
        skype.Attach()
        # obtain reference to Application object
        app = skype.Application('SkypeFs')
        # create application
        self._fuseHandler = FuseHandler(rootPath)
        app.Create()
        self.app = app

    def run(self):
        # wait forever until Ctrl+C (SIGINT) is issued
        while True:
            time.sleep(1)

    def close(self):
        self.app.Delete()

    ## SKYPE events
    def ApplicationReceiving(self, app, streams):
        ''' this handler is called when there is some
            data waiting to be read'''
        # streams contain all streams that have
        # some data, we scan all of them, read
        # and print the data out
        for s in streams:
            s.Write(self.execCmd(s.Read()))

    def execCmd(self, data):
        '''Call self.method depending of the method request
        in the request'''
        data = pickle.loads(base64.decodestring(data))
        print 'Executing %s' % data['method']
        methodToCall = getattr(self._fuseHandler, data['method'])
        output = methodToCall(*data['args'], **data['kwargs'])
        return base64.encodestring(pickle.dumps(output))

class FuseHandler(LoggingMixIn, Operations):
    def __init__(self, root):
        self.root = realpath(root)
        self.rwlock = Lock()

    def __call__(self, op, path, *args):
        return super(FuseHandler, self).__call__(op, self.root + path, *args)

    def access(self, path, mode):
        if not os.access(path, mode):
            raise FuseOSError(EACCES)

    chmod = os.chmod
    chown = os.chown

    def create(self, path, mode):
        return os.open(path, os.O_WRONLY | os.O_CREAT, mode)

    def flush(self, path, fh):
        return os.fsync(fh)

    def fsync(self, path, datasync, fh):
        return os.fsync(fh)

    def getattr(self, path, fh=None):
        st = os.lstat(path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    getxattr = None

    def link(self, target, source):
        return os.link(source, target)

    listxattr = None
    mkdir = os.mkdir
    mknod = os.mknod
    open = os.open

    def read(self, path, size, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)

    def readdir(self, path, fh):
        return ['.', '..'] + os.listdir(path)

    readlink = os.readlink

    def release(self, path, fh):
        return os.close(fh)

    def rename(self, old, new):
        return os.rename(old, self.root + new)

    rmdir = os.rmdir

    def statfs(self, path):
        stv = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def symlink(self, target, source):
        return os.symlink(source, target)

    def truncate(self, path, length, fh=None):
        with open(path, 'r+') as f:
            f.truncate(length)

    unlink = os.unlink
    utimens = os.utime

    def write(self, path, data, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.write(fh, data)
