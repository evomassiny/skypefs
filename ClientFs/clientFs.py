#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Skype4Py
import threading
from threading import Lock
import base64
import cPickle as pickle
import time
import sys
from fuse import FUSE, Operations

class ClientFs(Skype4Py.skype.SkypeEvents, object):
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
        # self.connect = lambda : self._app.Connect(username, WaitConnected=True)
        self.connect = lambda : self._app.Connect(username, WaitConnected=True)
        self._username = username
        self._mntPath = mntPath
        self._events = {}
        self._data = {}
        # Command ID
        self._id_lock = Lock()
        self._command_id = 0
        self._connect_event = threading.Event()
        self.stream = None

    @property
    def new_command_id(self):
        '''Return a new id, 
        used to track request'''
        with self._id_lock:
            self._command_id += 1
            self._command_id %= 10000
            return self._command_id

    @staticmethod
    def encode_command(data, cmd_id):
        '''Turn an object into a str'''
        return base64.encodestring(
                pickle.dumps((cmd_id, data)))

    @staticmethod
    def decode_response(data):
        '''turns a str into an object'''
        return pickle.loads(
            base64.decodestring(data))

    def run(self):
        fuse = FUSE(FuseClient(self), self._mntPath, 
                foreground=True)

    def close(self):
        self._app.Delete()

    # this handler is called when streams are opened or
    # closed, the streams argument contains a list of
    # all currently opened streams
    def ApplicationStreams(self, app, streams):
        # if streams is not empty then a stream to
        # the user was opened, we use its Write
        # method to send data; if streams is empty
        # then it means a stream was closed and we
        # can signal the main thread that we're done
        if streams:
            self.stream = streams[0]
            # release connect lock
            self._connect_event.set()
        else:
            self.stream = None

    ## SKYPE Events
    def ApplicationReceiving(self, app, streams):
        ''' this handler is called when there is some
            data waiting to be read'''
        # streams contain all streams that have
        # some data, we scan all of them, read
        # and print the data out
        for i, s in enumerate(streams):
            cmd_id, data = self.decode_response(s.Read())
            print 'receiving command %d' % cmd_id
            self._data[cmd_id] = data
            # release lock
            self._events[cmd_id].set()
            # s.Disconnect()

    # # this handler is called when data is sent over a
    # # stream, the streams argument contains a list of
    # # all currently sending streams
    # def ApplicationSending(self, app, streams):
        # # if streams is empty then it means that all
        # # streams have finished sending data, since
        # # we have only one, we disconnect it here;
        # # this will cause ApplicationStreams event
        # # to be called
        # if not streams:
            # app.Streams[0].Disconnect()

    def get_output(self, data):
        """This function send and object in
        the peer2peer network and return its response"""
        cmd_id = self.new_command_id
        self._events[cmd_id] = threading.Event()
        cmd = self.encode_command(data, cmd_id)
        if self.stream is None:
            self.connect()
            self._connect_event.wait()
        self.stream.Write(data)
        print 'sending command %d' % cmd_id
        self._events[cmd_id].wait()
        if cmd_id in self._data:
            output = self._data[cmd_id]
            del self._data[cmd_id]
            del self._events[cmd_id]
            return output
        return None

    def callServerMethod(self, method, *args):
        cmd = { 'method': method,
                'args': args }
        return self.get_output(cmd)

class FuseClient(Operations):
    '''This class is a client-side interface for fuse,
        it redirect every operations
        to the server through a ClientFs instance'''

    def __init__(self, skypeClient):
        self.skypeClient = skypeClient


    def __call__(self, method, *args):
        '''Call Server side FuseServer'''
        output = self.skypeClient.callServerMethod(method, *args)
        if issubclass(type(output), BaseException):
            raise output
        return output

