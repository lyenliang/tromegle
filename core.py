#!/usr/bin/env python
from twisted.internet import reactor

startTrolling = reactor.run
stopTrolling = reactor.stop

_nothing = lambda x: None

class CBDictInterface(object):
    """Base class for all classes responding to OmegleEvents.
    """
    def __init__(self, callbackdict=None):
        self.callbacks = callbackdict or {
                            'idSet': self.on_idSet,
                            'waiting': self.on_waiting,
                            'connected': self.on_connected,
                            'typing': self.on_typing,
                            'stoppedTyping': self.on_stoppedTyping,
                            'gotMessage': self.on_gotMessage,
                            'strangerDisconnected': self.on_strangerDisconnected}

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
        self.callbacks.get(ev.type, _nothing)(ev)
