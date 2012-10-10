#!/usr/bin/env python
from time import time
from collections import deque
from weakref import WeakValueDictionary

from twisted.internet import reactor

from omegle import Stranger, HTTP
from core import CBDictInterface
from event import isEvent, mkIterableSequence, Transmogrifier, ReactorEvent, IDLE_TIMEOUT, NULL_EVENT
from listener import InteractiveViewport


class TrollReactor(CBDictInterface):
    """Base class for Omegle API.
    """
    def __init__(self, transmog=Transmogrifier(), listen=InteractiveViewport(), n=2, refresh=1.5):
        # Independent setup
        super(TrollReactor, self).__init__()
        self.listeners = WeakValueDictionary()
        # Argument assignment
        self.eventQueue = deque()
        self.connectTransmogrifier(transmog)
        self.addListeners(listen)
        self._n = n
        self.refresh = refresh

        self._allConnected = False
        self.idleTime = None
        self.initializeStrangers()  # Now we wait to receive idSet events

    def connectTransmogrifier(self, transmog):
        self.transmogrifier = transmog
        self.transmogrifier.connect(self.eventQueue)

    def initializeStrangers(self):
        self._volatile = dict((Stranger(reactor, self, HTTP), None) for _ in xrange(self._n))
        self._waiting = len(self._volatile.keys())
        self.strangers = {}
        self.idleTime = time()
        self._allConnected = False

    def multicastDisconnect(self, ids):
        """Announce disconnect for a group of strangers.

        ids : iterable
            id strings of strangers from whom to politely disconnect.
        """
        for i in ids:
            self.strangers[i].announceDisconnect()

    def restart(self):
        self.strangers.clear()
        self._allConnected = False
        self.initializeStrangers()

    def pumpEvents(self):
        for id_ in self.strangers:
            self.strangers[id_].getEventsPage()

        reactor.callLater(self.refresh, self.pumpEvents)

    def on_idSet(self, ev):
        for s in self._volatile:
            if s.id == ev.id:  # we have the stranger that notified
                self.strangers[s.id] = s  # move to {id: stranger} dict
                self._waiting -= 1

        assert self._waiting >= 0, "Too many stranger IDs"
        if self._waiting == 0:
            self._allConnected = True
            self.idleTime = time()
            self.pumpEvents()

    def on_error(self, ev):
        pass  #  This is where we handle RECAPCHA

    def addListeners(self, listeners):
        """Add a listener or group of listeners to the reactor.

        listeners : CBDictInterface instance or iterable
        """
        listeners = mkIterableSequence(listeners)

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

    def deltaIdleTime(self):
        return time() - self.idleTime

    def idle(self):
        """Respond to idle state.

        This function is run whenever feed encounters a null event, and
        does nothing by default.  Override to define functionality.
        """
        pass

    def feed(self, events):
        """Notify the TrollReactor of event(s).
        """
        if not events or events is NULL_EVENT:
            events = (NULL_EVENT,)
            self.idle()
        else:
            self.idleTime = time()

        if isEvent(events):  # if events is a single event
            events = (events,)

        self.transmogrifier(events)
        self._processEventQueue()


class Client(TrollReactor):
    """Extensible client for omegle.com.
    """
    def __init__(self, refresh=2):
        super(Client, self).__init__(listen=listen, n=1)
        self.refresh = 2
        self._connected = False
        self.stranger = None

        self.amTyping = False
        self.isTyping = False
        self.on_stoppedTyping = self.on_typing

        self.reset()

    def reset(self):
        self._connected = False
        self.stranger = None
        self.amTyping = False
        self.isTyping = False

    def getStranger(self):
        self.stranger = Stranger(reactor, self, HTTP)

    def on_idSet(self, ev):
        self._connected = True
        self.pumpEvents()

    def on_typing(self, ev):
        self.isTyping = not self.isTyping

    def on_strangerDisconnected(self, ev):
        self.reset()

    def disconnect(self):
        self.stranger.announceDisconnect()
        self.reset()

    def sendMessage(self, msg):
        self.stranger.sendMessage(msg)

    def pumpEvents(self):
        self.strangers.getEventsPage()
        reactor.callLater(self.refresh, self.pumpEvents)


class MiddleMan(TrollReactor):
    """Implementation of man-in-the-middle attack on two omegle users.
    """
    def __init__(self, transmog=Transmogrifier(), listen=InteractiveViewport(), idle=(0., 0.)):
        """Instantiate MiddleMan class

        transmog : Transmogrifier instance

        listen : single listener instance or iterable.
            listeners to assign.

        idle : tuple of floats
            idle[0] =   maximum time to wait for all connections (seconds)
            idle[1] =   maximum time to wait for an idle conversation to resume (seconds)
        """
        super(MiddleMan, self).__init__(transmog=transmog, listen=listen)
        self.max_connect_time, self.max_idle_time = idle
        self.on_stoppedTyping = self.on_typing

    def on_typing(self, ev):
        self.strangers[ev.id].toggle_typing()

    def on_strangerDisconnected(self, ev):
        active = (i for i in self.strangers if i != ev.id)
        self.multicastDisconnect(active)  # announce disconnect to everyone
        self.restart()

    def on_gotMessage(self, ev):
        for nonspeaker_id in (nspkr for nspkr in self.strangers if nspkr != ev.id):
            self.strangers[nonspeaker_id].sendMessage(ev.data)

    def idle(self):
        if not self.max_idle_time and not self.max_connect_time:
            return

        dIdle = self.deltaIdleTime()
        slow_conn = not self._allConnected and (dIdle > self.max_connect_time) and self.max_connect_time
        slow_conv = self._allConnected and (dIdle > self.max_idle_time) and self.max_idle_time

        if slow_conn or slow_conv:
            self.feed(ReactorEvent(IDLE_TIMEOUT, None))

    def on_timeout(self, ev):
        self.multicastDisconnect((i for i in self.strangers))
        self.restart()


class OMiner(object):
    """Data minig class
    """
