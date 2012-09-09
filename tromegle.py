#!/usr/bin/env python

# http://forums.hackthissite.org/viewtopic.php?f=37&t=3783

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from sys import stderr
from json import loads
from random import choice
from urllib import urlencode
from traceback import print_stack
from collections import namedtuple, defaultdict, deque
from weakref import WeakValueDictionary

from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers


Event = namedtuple('OmegleEvent', ['id', 'type', 'data'])
startTrolling = lambda: reactor.run()
stopTrolling = lambda: reactor.stop()


def spell(fn):
    """Spell decorator
    """
    if fn is not None:
        return fn
    else:
        def throwNone(out, ev):
            return None


class NoStrangerIDError(Exception):
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return repr({'Code': response.code, 'Phrase': response.phrase})


class Transmogrifier(object):
    def __init__(self, spells=None):
        self.purge(spells)
        self.push = self._spells.append

    def __call__(self, events):
        """Cast all spells for each event in an iterable of events.
        """
        for ev in events:
            for spell in self._spells:
                ev = spell(self, ev)
            if ev:  # Functions may return None in order to "blackhole" an event
                self.output(ev)

    def purge(self, spells=None):
        if spells:
            self._spells = [s for s in spells]
        else:
            self._spells = []

    def connect(self, eventQueue):
        if not isinstance(eventQueue, deque):
            raise TypeError('Event queue must be a deque.')
        self._evQueue = eventQueue
        self.output = self._evQueue.append


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
        tag = 'Stranger_' + str(len(self.strangers.keys()) + 1)
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


class HTTP(Protocol):
    def __init__(self, response):
        self.response = response
        self.data = ''

    def dataReceived(self, bytes):
        self.data += bytes

    def connectionLost(self, reason):
        self.response.callback(self.data)


class Stranger(object):
    """Class to encapsulate I/O to an Omegle user.
    """
    _api = {k: 'http://omegle.com/' + k for
            k in ['start', 'events', 'send', 'typing', 'disconnect']}
    uagents = ["Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1",
              "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)",
              "Mozilla/5.0 (Windows; U; Windows NT 6.1; es-AR; rv:1.9) Gecko/2008051206 Firefox/3.0"]

    def __init__(self, reactor, troll, protocol):
        """reactor : twisted reactor instance
        protocol : class object
            Class of protocol being used
        """
        self.typing = False
        self.connected = False
        self.id = None

        self.reactor = reactor
        self.troll = troll  # exposes troll.notify
        self.protocol = protocol
        self.agent = choice(self.uagents)

        self._getStrangerID()

    def request(self, api_call, data):
        agent = Agent(self.reactor)
        header = {'User-Agent': [self.agent],
                  'content-type': ['application/x-www-form-urlencoded']}
        data = urlencode(data)
        return agent.request(
                'POST', self._api[api_call], Headers(header),
                FileBodyProducer(StringIO(data)))

    def getBody(self, response):
        body = Deferred()
        response.deliverBody(self.protocol(body))
        return body

    def _getStrangerID(self):
        d = self.request('start', '')
        # lvl 1
        d.addCallback(self.checkForOkStatus)
        # lvl 2
        d.addCallback(self.getBody)
        # lvl 3
        d.addCallback(self._assignID)

    def checkForOkStatus(self, response):
        if response.code == 200:
            return response
        else:
            raise NoStrangerIDError(response)  # pass response so it can be examined

    def _assignID(self, body):
        """Download the body on successful header fetch
        from _getStrangerID
        """
        self.id = body.replace('"', '')
        ev = Event(self.id, 'idSet', '')
        self.troll.feed(ev)  # ready to go!

    def parse_raw_events(self, events):
        """Produce OmegleEvents from a list of raw events.
        events : string
            String of raw events from a POST request to
            an omegle subpage.
        """
        events = loads(events)  # json.loads
        if events is None:
            return tuple()

        parsedEvts = []
        for ev in (e for e in events):
            if len(ev) == 1:
                data = None
            else:
                data = ev[1]
            parsedEvts.append(Event(self.id, ev[0].encode('ascii'), data))  # move to function with 'yield' for memory efficiency?

        return parsedEvts

    def getEventsPage(self):
        d = self.request('events', {'id': self.id})
        d.addCallback(self.getBody)
        d.addCallback(self.parse_raw_events)
        d.addCallback(self.troll.feed)

    def toggle_typing(self):
        def flip(resp):
            self.typing = not self.typing

        d = self.request('typing', {'id': self.id})
        d.addCallback(self.checkForOkStatus)
        d.addCallback(flip)

    def announceDisconnect(self):
        d = self.request('disconnect', {'id': self.id})

    def sendMessage(self, msg):
        d = self.request('send', {'msg': msg, 'id': self.id})


class TrollReactor(CBDictInterface):
    """Base class for all Omegle I/O.
    """
    def __init__(self, transmog=Transmogrifier(), listen=Viewport(), n=2, refresh=1.5):
        # Independent setup
        super(TrollReactor, self).__init__()
        self.listeners = WeakValueDictionary()
        # Argument assignment
        self.eventQueue = deque()
        self.transmogrifier = transmog
        self.transmogrifier.connect(self.eventQueue)
        self.addListeners(listen)
        self._n = n
        self.refresh = refresh

        self.initializeStrangers()  # Now we wait to receive idSet events

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

# Demonstration
if __name__ == '__main__':
    m = MiddleMan()
    startTrolling()
