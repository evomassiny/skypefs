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
            print 'Sending msg...'
            streams[0].Write('TEST')
            streams[0].Disconnect()
            print 'Done'
        # else:
            global event
            event.set()

    # this handler is called when data is sent over a
    # stream, the streams argument contains a list of
    # all currently sending streams
    def ApplicationSending(self, app, streams):
        # if streams is empty then it means that all
        # streams have finished sending data, since
        # we have only one, we disconnect it here;
        # this will cause ApplicationStreams event
        # to be called
        if not streams:
            app.Streams[0].Disconnect()

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
            print 'Connecting ...'
            stream = app.Connect(username, WaitConnected=True)
            # wait until the event handlers do the job
            event.wait()
        except KeyboardInterrupt:
            pass

        # delete application
        app.Delete()
