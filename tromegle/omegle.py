#!/usr/bin/env python
from urllib import urlencode
import json
from random import choice
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.internet.error import TimeoutError
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers

from tromegle.event import OmegleEvent, ID_SET, TIMEOUT_EVENT


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
    _RESPONSE_OK = 200
    _ACTIONS = ('start', 'events', 'send', 'typing', 'disconnect')
    _api = dict(((a, 'http://omegle.com/' + a) for a in _ACTIONS))
    uagents = ["Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1",
              "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)",
              "Mozilla/5.0 (Windows; U; Windows NT 6.1; es-AR; rv:1.9) Gecko/2008051206 Firefox/3.0"]

    def __init__(self, reactor, troll, protocol, debug=0):
        """
        reactor : twisted reactor instance

        troll : TrollReactor
            TrollReactor (or subclass) to manage stranger(s)

        protocol : class object
            Class of protocol being used

        debug : int
            Debugging level.  0 = no debugging.
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
                  'content-type': ['application/x-www-form-urlencoded; charset=utf-8']}

        data = urlencode(data)
        request = agent.request('POST',
                                self._api[api_call],
                                Headers(header),
                                FileBodyProducer(StringIO(data)))

        return request  # .addErrback(log.err, 'Error sending %r to %s' % (data, api_call))

    def getBody(self, response):
        body = Deferred()
        response.deliverBody(self.protocol(body))
        return body

    def trapTimeout(self, err):
        """Errback function to suppress TimeoutError exceptions,
        optionally feeding a connectionTimeout event to self.troll,
        which can be logged or used as a trigger for arbitrary events.

        If self.debug > 1, trapTimeout will feed a connectionTimeout
        event, otherwise it will not.

        err : Exception
            Exception passed by Deferred instance.

        return : Exception or None
        """
        if isinstance(err, TimeoutError):
            if self.debug:
                self.troll.feed(OmegleEvent(self.id, TIMEOUT_EVENT, ''))
            return None

        return err

    def _getStrangerID(self):
        d = self.request('start', '')
        # lvl 1
        d.addCallback(self.checkForOkStatus)
        # lvl 2
        d.addCallback(self.getBody)
        # lvl 3
        d.addCallbacks(self._assignID, self.trapTimeout)

    def checkForOkStatus(self, response):
        assert response.code == self._RESPONSE_OK, "Bad response to HTTP request."
        return response

    def _assignID(self, body):
        """Download the body on successful header fetch
        from _getStrangerID
        """
        self.id = body.replace('"', '')
        ev = OmegleEvent(self.id, ID_SET, '')
        self.troll.feed(ev)  # ready to go!

    def parse_raw_events(self, events):
        """Produce OmegleEvents from a list of raw events.
        events : string
            String of raw events from a POST request to
            an omegle subpage.

        return : generator or NoneType
            Return generator with events or None if there are no events.
        """
        events = json.loads(events) or None
        if events:
            events = (OmegleEvent(self.id,
                                  ev[0],
                                  None if len(ev) == 1 else ev[1])
                      for ev in events)

        return events

    def getEventsPage(self):
        d = self.request('events', {'id': self.id})
        d.addCallback(self.getBody)
        d.addCallback(self.parse_raw_events)
        d.addCallbacks(self.troll.feed, self.trapTimeout)

    def toggle_typing(self):
        d = self.request('typing', {'id': self.id})
        d.addCallback(self.checkForOkStatus)
        d.addCallbacks(self._toggle_typing, self.trapTimeout)

    def _toggle_typing(self, resp):
        self.typing = not self.typing

    def announceDisconnect(self):
        self.request('disconnect', {'id': self.id})

    def sendMessage(self, msg):
        self.request('send', {'msg': msg.encode('utf-8'), 'id': self.id})
