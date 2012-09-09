#!/usr/bin/env python
from sys import stderr
from collections import deque
from weakref import WeakValueDictionary

from event import Transmogrifier
from listener import Viewport


class TrollReactor(CBDictInterface):
    """Base class for Omegle API.
    """
    def __init__(self, transmog=Transmogrifier(), listen=Viewport(), n=2, refresh=1.5):
        # Independent setup
        super(TrollReactor, self).__init__()
        self.listeners = WeakValueDictionary()
        # Argument assignment
        self.eventQueue = deque()
        self.connectTransmogrifier(transmog)
        self.addListeners(listen)
        self._n = n
        self.refresh = refresh

        self.initializeStrangers()  # Now we wait to receive idSet events

    def connectTransmogrifier(self, transmog):
        self.transmogrifier = transmog
        self.transmogrifier.connect(self.eventQueue)

    def initializeStrangers(self):
        self._volatile = {Stranger(reactor, self, HTTP): None for _ in xrange(self._n)}
        self._waiting = len(self._volatile.keys())
        self.strangers = {}

    def multicastDisconnect(self, ids):
        """Announce disconnect for a group of strangers.

        ids : iterable
            id strings of strangers from whom to politely disconnect.
        """
        for i in ids:
            self.strangers[i].announceDisconnect()

    def pumpEvents(self):
        for id_ in self.strangers:
            self.strangers[id_].getEventsPage()

        reactor.callLater(self.refresh, self.pumpEvents)

    def on_idSet(self, ev):
        for s in self._volatile:
            if s.id == ev.id:  # we have the stranger that notified
                self.strangers[s.id] = s  # move to {id: stranger} dict
                self._waiting -= 1
        if self._waiting == 0:
            self.pumpEvents()
        elif self._waiting < 0:
            print_stack()
            stderr.write("ERROR:  too many stranger IDs.")
            reactor.stop()

    def addListeners(self, listeners):
        """Add a listener or group of listeners to the reactor.

        listeners : CBDictInterface instance or iterable
        """
        if not hasattr(listeners, '__iter__'):
            listeners = (listeners,)

        for listen in listeners:
            self.listeners[listen] = listen  # weak-value dict

    def removeListener(self, listener):
        self.listeners.pop(listener)

    def _processEventQueue(self):
        while len(self.eventQueue):
            ev = self.eventQueue.popleft()
            for listener in self.listeners:
                listener.notify(ev)

            self.notify(ev)

    def feed(self, events):
        """Notify the TrollReactor of an event.
        """
        if hasattr(events, '_fields'):
            events = (events,)  # convert to tuple

        self.transmogrifier(events)
        self._processEventQueue()


class Client(TrollReactor):
    """Extensible client for omegle.com.
    """
    def __init__(self, listen=Viewport()):
        super(Client, self).__init__(listen=listen, n=1)


class MiddleMan(TrollReactor):
    """Implementation of man-in-the-middle attack on two omegle users.
    """
    def __init__(self, transmog=Transmogrifier(), listen=Viewport()):
        super(MiddleMan, self).__init__(transmog=transmog, listen=listen)
        self.on_stoppedTyping = self.on_typing

    def on_typing(self, ev):
        self.strangers[ev.id].toggle_typing()

    def on_strangerDisconnected(self, ev):
        print "Restarting..."
        active = (i for i in self.strangers if i != ev.id)
        self.multicastDisconnect(active)  # announce disconnect to everyone
        self.strangers.clear()  # disconnect from everyone (clear the dict)
        self.initializeStrangers()

    def on_gotMessage(self, ev):
        for nonspeaker_id in (nspkr for nspkr in self.strangers if nspkr != ev.id):
            self.strangers[nonspeaker_id].sendMessage(ev.data)


class OMiner(object):
    """Data minig class
    """
