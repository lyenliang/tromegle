#!/usr/bin/env python
from twisted.internet import reactor

from event import ID_SET, WAITING, CONNECTED, TYPING, STOPPED_TYPING, GOT_MESSAGE, DISCONNECTED, ERROR, IDLE_TIMEOUT, MESSAGE_MODIFIED

startTrolling = reactor.run
stopTrolling = reactor.stop

_doNothing = lambda x: None


class CBDictInterface(object):
    """Base class for all classes responding to OmegleEvents.
    """
    def __init__(self, callbackdict=None):
        self.callbacks = callbackdict or {
                            ID_SET: self.on_idSet,
                            WAITING: self.on_waiting,
                            CONNECTED: self.on_connected,
                            TYPING: self.on_typing,
                            STOPPED_TYPING: self.on_stoppedTyping,
                            GOT_MESSAGE: self.on_gotMessage,
                            DISCONNECTED: self.on_strangerDisconnected,
                            ERROR: self.on_error,
                            IDLE_TIMEOUT: self.on_timeout,
                            MESSAGE_MODIFIED: self.on_messageModified}

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

    def on_error(self, ev):
        pass

    def on_timeout(self, ev):
        pass

    def on_messageModified(self, ev):
        pass

    def notify(self, ev):
        self.callbacks.get(ev.type, _doNothing)(ev)
