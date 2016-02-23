#!/usr/bin/env python

import Skype4Py
import threading
import base64
import cPickle as pickle
import time
import sys
from fuse import FUSE, Operations

class ClientFs(Skype4Py.skype.SkypeEvents):
    '''This class is handle client-side communication
        using the Skype4py API'''

    def __init__(self, username, mntPath):
        # instatinate Skype object and set our event handlers
        skype = Skype4Py.Skype(Events=self, Transport='x11')
        # attach to Skype client
        skype.Attach()
        # obtain reference to Application object
        self._app = skype.Application('SkypeFs')
        # create application
        self._app.Create()
        self.connect = lambda : self._app.Connect(username, WaitConnected=True)
        self._username = username
        self._mntPath = mntPath
        self._events = {}
        self._data = {}

    def run(self):
        fuse = FUSE(FuseClient(self), self._mntPath, 
                foreground=True, nothreads=True)

    def close(self):
        self._app.Delete()

    ## SKYPE Events
    def ApplicationReceiving(self, app, streams):
        ''' this handler is called when there is some
            data waiting to be read'''
        # streams contain all streams that have
        # some data, we scan all of them, read
        # and print the data out
        for s in streams:
            if s in self._events:
                self._data[s] = s.Read()
                # release lock
                self._events[s].set()
                # s.Disconnect()

    def get_output(self, data):
        """This function send and object in
        the peer2peer network and return its response"""
        stream = self.connect()
        self._events[stream] = threading.Event()
        stream.Write(base64.encodestring(pickle.dumps(data)))
        self._events[stream].wait()
        del self._events[stream]
        if stream in self._data:
            output = pickle.loads(base64.decodestring(self._data[stream]))
            # print(output)
            del self._data[stream]
            return output
        return None

    def callServerMethod(self, method, *args, **kwargs):
        cmd = { 'method': method,
                'args': args,
                'kwargs': kwargs}
        return self.get_output(cmd)

class FuseClient(Operations):
    '''This class is a client-side interface for fuse,
        it redirect every operations
        to the server through a ClientFs instance'''

    def __init__(self, skypeClient):
        self.skypeClient = skypeClient

    def __call__(self, method, *args, **kwargs):
        '''Call Server side FuseServer'''
        output = self.skypeClient.callServerMethod(method, *args, **kwargs)
        if issubclass(type(output), BaseException):
            raise output
        return output

