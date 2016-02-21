#!/usr/bin/env python

import Skype4Py
import threading
import base64
import pickle
import time
import sys
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

skypeClient = None
class ClientFs(Skype4Py.skype.SkypeEvents):

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
        global skypeClient
        skypeClient = self
        fuse = FUSE(FuseClient(), self._mntPath, foreground=True)

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
            s.Disconnect()

    def get_output(self, data):
        """This function send and object in
        the peer2peer network and return its responce"""
        # stream = self._app.Connect(self._username, WaitConnected=True)
        stream = self.connect()
        self._events[stream] = threading.Event()
        stream.Write(base64.encodestring(pickle.dumps(data)))
        # lock until responce
        self._events[stream].wait()
        del self._events[stream]
        if stream in self._data:
            output = pickle.loads(base64.decodestring(self._data[stream]))
            del self._data[stream]
            return output
        return None

    # ## Fuse function
    # def __getattr__(self, method):
        # '''Called when __getattribute__ fails'''
        # def sendCmdWrapper(*args, **kwargs):
            # return self.sendCmd(method, *args, **kwargs)
        # return sendCmdWrapper
    
    def sendCmd(self, method, *args, **kwargs):
        cmd = { 'method': method,
                'args': args,
                'kwargs': kwargs}
        return self.get_output(cmd)

class FuseClient(Operations): # (Operations, LoggingMixIn):

    # def __init__(self, skypeClient):
        # self.skypeClient = skypeClient

    # ## Fuse function
    # def __getattr__(self, method):
        # '''Called when __getattribute__ fails'''
        # def sendCmdWrapper(*args, **kwargs):
            # return self.skypeClient.sendCmd(method, *args, **kwargs)
        # return sendCmdWrapper

    def __call__(self, method, *args, **kwargs):
        global skypeClient
        # return super(FuseHandler, self).__call__(op, self.root + path, *args)
        return skypeClient.sendCmd(method, *args, **kwargs)

