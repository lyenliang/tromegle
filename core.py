#!/usr/bin/env python
from collections import defaultdict

from twisted.internet import reactor

startTrolling = lambda: reactor.run()
stopTrolling = lambda: reactor.stop()


class CBDictInterface(object):
    """Base class for all classes responding to OmegleEvents.
    """
    def __init__(self, callbackdict=None):
        if not callbackdict:
            callbackdict = {'idSet': self.on_idSet,
                            'waiting': self.on_waiting,
                            'connected': self.on_connected,
                            'typing': self.on_typing,
                            'stoppedTyping': self.on_stoppedTyping,
                            'gotMessage': self.on_gotMessage,
                            'strangerDisconnected': self.on_strangerDisconnected}

        self.callbacks = defaultdict(lambda: lambda ev: None,
                                     callbackdict)
        # self.callbacks = callbackdict

    def on_idSet(self, ev):
        pass

    def on_waiting(self, ev):
        pass

    def on_connected(self, ev):
        pass

    def on_typing(self, ev):
        pass

    def on_stoppedTyping(self, ev):
        pass

    def on_gotMessage(self, ev):
        pass

    def on_strangerDisconnected(self, ev):
        pass

    def notify(self, ev):
        self.callbacks[ev.type](ev)
