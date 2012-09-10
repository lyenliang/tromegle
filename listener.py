#!/usr/bin/env python
from collections import namedtuple

from core import CBDictInterface


class Viewport(CBDictInterface):
    """Interfae for printing conversations to standard output.
    """
    # container for viewport messages.  'orig' parameter contains
    #   untransmogrified message, or NoneType if the message was not altered.
    Message = namedtuple('ViewportMessage', ['id', 'msg', 'orig'])

    def __init__(self, callbackdict=None):
        super(Viewport, self).__init__(callbackdict)
        self.strangers = {}
        self.ready = 0  # no strangers connected

    def on_idSet(self, ev):
        tag = 'Stranger_{0}'.format(len(self.strangers.keys()) + 1)
        self.strangers[ev.id] = tag
        print tag, "identified..."

    def on_waiting(self, ev):
        print "Waiting to connect to", self.strangers[ev.id]

    def on_connected(self, ev):
        print "Connected to", self.strangers[ev.id]
        self.ready += 1
        if self.ready == len(self.strangers.keys()):
            print

    def on_strangerDisconnected(self, ev):
        print self.strangers[ev.id], "has disconnected."
        print
        print
        self.strangers.clear()

    def on_gotMessage(self, ev):
        print self.strangers[ev.id] + ": ", ev.data
