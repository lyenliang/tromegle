#!/usr/bin/env python

# http://forums.hackthissite.org/viewtopic.php?f=37&t=3783

from sys import stderr
from json import loads
from random import choice
from urllib import urlencode
from StringIO import StringIO
from collections import namedtuple
from traceback import print_stack

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers


Event = namedtuple('OmegleEvent', ['id', 'type', 'data'])


class NoStrangerIDError(Exception):
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return repr({'Code': response.code, 'Phrase': response.phrase})


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
        self.troll = troll  # exposes troll.feed
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
        self.troll.feed(Event(self.id, 'idSet', ''))  # ready to go!

    def parse_raw_events(self, events):
        """Produce OmegleEvents from a list of raw events.
        events : string
            String of raw events from a POST request to
            an omegle subpage.
        """
        events = loads(events)  # json.loads
        # Events == None every time... urlencoding probably screwed up
        if events:
            parsedEvts = []
            for ev in (e for e in events):
                if len(ev) == 1:
                    data = None
                else:
                    data = ev[1]
                parsedEvts.append(Event(self.id, ev[0].encode('ascii'), data))

            return parsedEvts
        else:
            return Event(self.id, 'tick', None)

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
        d = self.request('send', {'mst': msg, 'id': self.id})


class TrollReactor(object):
    """Base class for all Omegle I/O.
    """
    def __init__(self, n=2, refresh=2):
        self.refresh = refresh
        self._volatile = {Stranger(reactor, self, HTTP): None for _ in xrange(n)}
        self._waiting = len(self._volatile.keys())
        self.strangers = {}
        self.callbacks = {'tick': self.on_tick,
                          'idSet': self.on_idSet,
                          'waiting': self.on_waiting,
                          'connected': self.on_connected,
                          'typing': self.on_typing,
                          'stoppedTyping': self.on_stoppedTyping,
                          'gotMessage': self.on_gotMessage,
                          'strangerDisconnected': self.on_strangerDisconnected}

        # Now we wait to receive idSet events

    def _startTrolling(self):
        for id_ in self.strangers:
            self.strangers[id_].getEventsPage()

    def on_tick(self, ev):
        print ev  # DEBUG
        reactor.callLater(self.refresh, self.strangers[ev.id].getEventsPage)

    def on_idSet(self, ev):
        for s in self._volatile:
            if s.id == ev.id:  # we have the stranger that notified
                self.strangers[s.id] = s  # move to {id: stranger} dict
                self._waiting -= 1
        if self._waiting == 0:
            self._startTrolling()
        elif self._waiting < 0:
            print_stack()
            stderr.write("ERROR:  too many stranger IDs.")
            reactor.stop()

    def on_waiting(self, ev):
        print ev

    def on_connected(self, ev):
        print ev

    def on_typing(self, ev):
        print ev

    def on_stoppedTyping(self, ev):
        print ev

    def on_gotMessage(self, ev):
        print ev

    def on_strangerDisconnected(self, ev):
        print ev

    def feed(self, events):
        """Notify the TrollReactor of an event.
        """
        if hasattr(events, '_fields'):
            events = (events,)  # tuplify

        for ev in events:
            self.callbacks[ev.type](ev)
