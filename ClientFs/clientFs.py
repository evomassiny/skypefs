#!/usr/bin/env python

import Skype4Py
import threading
import time
import sys

# create event; we will need one since Skype4Py's event
# handlers are called asynchronously on a separate thread
event = threading.Event()

# class with our Skype event handlers
class SkypeEvents:

    # this handler is called when there is some
    # data waiting to be read
    def ApplicationReceiving(self, app, streams):
        # streams contain all streams that have
        # some data, we scan all of them, read
        # and print the data out
        for s in streams:
            print 'Receiving from %s' % s.Handle
            print s.Read()


class ClientFs:

    def __init__(self, username):
        # instatinate Skype object and set our event handlers
        skype = Skype4Py.Skype(Events=SkypeEvents(), Transport='x11')

        # attach to Skype client
        skype.Attach()

        # obtain reference to Application object
        app = skype.Application('App2AppServer')

        # create application
        app.Create()

        # connect application to user specified by script args
        try:
            while True:
                time.sleep(2)
                stream = app.Connect(username, WaitConnected=True)
                stream.Write("TEST waiting")
        except KeyboardInterrupt:
            pass

        # delete application
        app.Delete()
