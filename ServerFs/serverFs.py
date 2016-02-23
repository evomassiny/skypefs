#!/usr/bin/env python
import Skype4Py
import time
import os
from errno import EACCES
from os.path import realpath
from threading import Lock
import base64
import cPickle as pickle
import xattr

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

class ServerFs:
    '''This class is handle client-side communication
        using the Skype4py API'''

    def __init__(self, rootPath):
        # instatinate Skype object and set our event handlers
        skype = Skype4Py.Skype(Events=self, Transport='x11')
        # attach to Skype client
        skype.Attach()
        # obtain reference to Application object
        app = skype.Application('SkypeFs')
        # create application
        self._fuseServer = FuseServer(rootPath)
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
        methodToCall = getattr(self._fuseServer, data['method'])
        try:
            output = methodToCall(*data['args'], **data['kwargs'])
        except OSError as e:
            output = e
        except FuseOSError as e:
            output = e
        except IOError as e:
            output = OSError()
        return base64.encodestring(pickle.dumps(output))


class FuseServer(LoggingMixIn, Operations):
    """This class is an Interface for server-side Fuse"""

    def __init__(self, root):
        self.root = realpath(root)
        self.rwlock = Lock()

    def abs_path(self, path):
        return self.root + path

    def access(self, path, mode):
        path = self.abs_path(path)
        if not os.access(path, mode):
            raise FuseOSError(EACCES)
            # return FuseOSError(EACCES)

    def chmod(self, path, *args, **kwargs):
        path = self.abs_path(path)
        return os.chmod(path, *args, **kwargs)

    def chown(self, path, *args, **kwargs):
        path = self.abs_path(path)
        return os.chown(path, *args, **kwargs)

    def create(self, path, mode):
        path = self.abs_path(path)
        return os.open(path, os.O_WRONLY | os.O_CREAT, mode)

    def flush(self, path, fh):
        path = self.abs_path(path)
        return os.fsync(fh)

    def fsync(self, path, datasync, fh):
        path = self.abs_path(path)
        return os.fsync(fh)

    def getattr(self, path, fh=None):
        path = self.abs_path(path)
        st = os.lstat(path)
        return dict(
                (key, getattr(st, key)) for key in (
                    'st_atime', 'st_ctime',
                    'st_gid', 'st_mode',
                    'st_mtime', 'st_nlink',
                    'st_size', 'st_uid')
                )

    def link(self, target, source):
        path = self.abs_path(target)
        return os.link(source, target)

    def unlink(self, path, *args, **kwargs):
        path = self.abs_path(path)
        return os.unlink(path, *args, **kwargs)

    def mknod(self, path, *args, **kwargs):
        path = self.abs_path(path)
        return os.mknod(path, *args, **kwargs)

    def mkdir(self, path, *args, **kwargs):
        path = self.abs_path(path)
        return os.mkdir(path, *args, **kwargs)

    def open(self, path, *args, **kwargs):
        path = self.abs_path(path)
        return os.open(path, *args, **kwargs)


    def read(self, path, size, offset, fh):
        path = self.abs_path(path)
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)

    def readdir(self, path, fh):
        path = self.abs_path(path)
        return ['.', '..'] + os.listdir(path)

    def release(self, path, fh):
        path = self.abs_path(path)
        return os.close(fh)

    def rename(self, old, new):
        return os.rename(old, self.root + new)

    def rmdir(path, *args, **kwargs):
        path = self.abs_path(path)
        return os.rmdir(path, *path, **kwargs)

    def readlink(path, *args, **kwargs):
        path = self.abs_path(path)
        return os.readlink(path, *path, **kwargs)

    def statfs(self, path):
        path = self.abs_path(path)
        stv = os.statvfs(path)
        return dict(
                (key, getattr(stv, key)) for key in (
                    'f_bavail', 'f_bfree',
                    'f_blocks', 'f_bsize',
                    'f_favail', 'f_ffree',
                    'f_files', 'f_flag',
                    'f_frsize', 'f_namemax')
                )

    def symlink(self, target, source):
        source = self.abs_path(source)
        target = self.abs_path(target)
        return os.symlink(source, target)

    def truncate(self, path, length, fh=None):
        path = self.abs_path(path)
        with open(path, 'r+') as f:
            f.truncate(length)

    utimens = os.utime

    def write(self, path, data, offset, fh):
        path = self.abs_path(path)
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.write(fh, data)

    def getxattr(self, path, *args, **kwargs):
        path = self.abs_path(path)
        return xattr.getxattr(path, *args, **kwargs)

    def listxattr(self, path, *args, **kwargs):
        path = self.abs_path(path)
        return xattr.listxattr(path, *args, **kwargs)
