#!/usr/bin/env python

# http://forums.hackthissite.org/viewtopic.php?f=37&t=3783

from sys import stderr
from json import loads
from random import choice
from urllib import urlencode
from StringIO import StringIO
from traceback import print_stack
from collections import namedtuple
from weakref import WeakValueDictionary

from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers


Event = namedtuple('OmegleEvent', ['id', 'type', 'data'])


class NoStrangerIDError(Exception):
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return repr({'Code': response.code, 'Phrase': response.phrase})


class CBDictInterface(object):
    """Base class for all classes responding to OmegleEvents.
    """
    def __init__(self, callbackdict=None):
        if not callbackdict:
            self.callbacks = {'idSet': self.on_idSet,
                              'waiting': self.on_waiting,
                              'connected': self.on_connected,
                              'typing': self.on_typing,
                              'stoppedTyping': self.on_stoppedTyping,
                              'gotMessage': self.on_gotMessage,
                              'strangerDisconnected': self.on_strangerDisconnected}
        else:
            self.callbacks = callbackdict

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
        self.troll.notify(ev)  # ready to go!

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
        d.addCallback(self.troll.notify)

    def toggle_typing(self):
        def flip(resp):
            self.typing = not self.typing

        d = self.request('typing', {'id': self.id})
        d.addCallback(self.checkForOkStatus)
        d.addCallback(flip)

    def announceDisconnect(self):
        d = self.request('disconnect', {'id': self.id})

    def sendMessage(self, msg):
        d = self.request('send', {'mst': msg, 'id': self.id})


class TrollReactor(CBDictInterface):
    """Base class for all Omegle I/O.
    """
    def __init__(self, n=2, refresh=2):
        super(TrollReactor, self).__init__()
        self._n = n
        self.refresh = refresh
        self.initializeStrangers()

        self.listeners = WeakValueDictionary()

        # Now we wait to receive idSet events

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

    def addListener(self, listener):
        self.listeners[listener] = listener  # weak-value dict

    def removeListener(self, listener):
        self.listeners.pop(listener)

    def notify(self, events):
        """Notify the TrollReactor of an event.
        """
        if hasattr(events, '_fields'):
            events = (events,)  # convert to tuple

        for ev in events:
            for listener in self.listeners:
                listener.notify(ev)

            self.callbacks[ev.type](ev)


class MiddleMan(TrollReactor):
    """Implementation of man-in-the-middle attack on two omegle users.
    """
    def __init__(self):
        super(MiddleMan, self).__init__()

        self.addListener(Viewport())

        self.on_stoppedTyping = self.on_typing

    def on_typing(self, ev):
        self.strangers[ev.id].toggle_typing()

    def on_strangerDisconnected(self, ev):
        active = (s for s in self.strangers if s != ev.id)
        self.multicastDisconnect(active)  # announce disconnect to everyone
        self.strangers.clear()  # disconnect from everyone (clear the dict)
        self.initializeStrangers()

    def on_gotMessage(self, ev):
        for nonspeaker_id in (nspkr for nspkr in self.strangers if nspkr != ev.id):
            self.strangers[nonspeaker_id].sendMessage(ev.data)
