#!/usr/bin/env python

# http://forums.hackthissite.org/viewtopic.php?f=37&t=3783

# import asyncore
# import socket
from urllib import urlencode
from collections import deque, namedtuple
from weakref import WeakValueDictionary
import urllib2 as url


Event = namedtuple('OmegleEvent', ['id', 'type', 'data'])


class Stranger(object):
    """Class to encapsulate a "stranger" and all associated I/O.
    """
    OMEGLE = "http://omegle.com/"
    START = OMEGLE + "start"
    EVENTS = OMEGLE + "events"
    SEND = OMEGLE + "send"
    TYPING = OMEGLE + "typing"
    DISCONNECT = OMEGLE + "disconnect"

    def __init__(self, name):
        self.typing = False
        self.isconnected = False
        self.name = name

        self.id = self.getStrangerID()
        self.events = self.getEventsPage()

    def getStrangerID(self):
        strangerID = url.urlopen(self.START, '')
        return strangerID.read().replace('"', '')

    def getEventsPage(self):
        # We build a request object for the current stranger
        # The request object just polls the ~/events page, specifying an id
        events = url.Request(self.EVENTS, urlencode({'id': self.id}))
        return events

    def checkConnect(self, events):
        for ev in events:
            if ev.type == 'connected':
                self.isconnected = True
            elif ev.type == 'strangerDisconnected':
                self.isconnected = False
        return self.isconnected

    def toggle_typing(self):
        typing = url.urlopen(self.TYPING, '&id=' + self.id)
        typing.close()
        self.typing = not self.typing
        return self.typing

    def sendMessage(self, msg):
        # NOTE:  this function takes the msg param because the outbuffer
        # is the responsibility of the user, not his partner!
        send = url.urlopen(self.SEND, '&msg=' + msg + '&id=' + self.id)
        send.close()

    def announceDisconnect(self):
        politeExit = url.urlopen(self.DISCONNECT, '&id=' + self.id)
        politeExit.close()

    def pullEvents(self):
        evbuffer = url.urlopen(self.events).read()
        evbuffer = self.parse_raw_events(evbuffer)
        self.checkConnect(evbuffer)
        return evbuffer

    def parse_raw_events(self, events):
        events = [ev for ev in events.split('[') if ev is not '']
        events = [ev.replace(']', '') for ev in events]
        events = [ev.replace('"', '').strip() for ev in events]
        events = [ev[:-1].strip() for ev in events if ev.endswith(',')]
        events = [ev.split(',') for ev in events]

        parsedEvts = []
        for ev in events:
            if len(ev) > 1:
                data = ev[1]
            else:
                data = None
            parsedEvts.append(Event(self.id, ev[0], data))
        return parsedEvts


class Viewport(object):
    """Interface for printing conversation messages to standard output.

    strangers : list
        Strangers to add to the Viewport instance

    maxlines : int
        Maximum length of the messages buffer

    callbacks : dict
        A non-empty dict overrides default event callbacks.
    """
    def __init__(self, strangers, maxlines=25, callbackdict={}):
        self.strangers = WeakValueDictionary(strangers)
        self.messages = deque(maxlen=maxlines)

        if callbackdict == {}:
            self.callbacks = {'waiting': self.onWaiting,
                              'connected': self.onConnect,
                              'typing': self.onTyping,
                              'gotMessage': self.gotMessage,
                              'strangerDisconnected': self.onDisconnect
                             }
        else:
            self.callbacks = callbackdict

        self.waiting = False

    def addStranger(self, stranger):
        self.strangers[stranger.id] = stranger

    def notify(self, eventlist):
        for ev in eventlist:
            self.callbacks[ev.type](ev)

    def onWaiting(self, ev):
        if not self.waiting:
            print "Waiting..."
            self.waiting = True

    def onConnect(self, ev):
        if self.waiting:
            self.waiting = False  # reset waiting flag so that we get proper wait notification
        print self.strangers[ev.id].name, "connected!"

    def onTyping(self, ev):
        print "Typing..."

    def gotMessage(self, ev):
        print self.strangers[ev.id].name + ":  ", ev.data

    def onDisconnect(self, ev):
        print self.strangers[ev.id].name, "disconnected"


class MiddleMan(object):
    """Class to implement a man-in-the-middle attack on two
    Omegle users.
    """
    def __init__(self):
        self.getStrangers()  # set self.strangers
        self.view = Viewport(self.strangers)
        self.go()

    def getStrangers(self):
        strangers = [Stranger('Stranger_' + str(i + 1)) for i in xrange(2)]
        self.strangers = {s.id: s for s in strangers}

    def getEvents(self):
        # Thread this...
        # You want to fetch events for each stranger seperately
        eventPolls = [self.strangers[s].pullEvents() for s in self.strangers]
        # print "Got events..."  # DEBUG
        stranger_IDs = [self.strangers[s].id for s in self.strangers]
        for idstr, evts in enumerate(eventPolls):
            self.view.notify(evts)
            self.notify(evts)

            messages = [e for e in evts if e.type == "gotMessage"]
            if messages is not []:
                self.propagateMessages(stranger_IDs[idstr], messages)

    def propagateMessages(self, idstr, eventlist):
        targets = [self.strangers[s] for s in self.strangers if self.strangers[s].id != idstr]
        for stranger in targets:
            for ev in eventlist:
                stranger.sendMessage(ev.data)

    def notify(self, evts):
        for ev in evts:
            if ev.type == "strangerDisconnected":
                self.strangers.pop(ev.id)
                # politely exit
                for key in self.strangers:
                    self.strangers[key].announceDisconnect()
                self.strangers.clear()  # empty the dict

                # start over
                self.getStrangers()

    def go(self):
        while True:
            self.getEvents()


class ChatRoom(object):  # consider inheriting from viewport?
    """Class to implement an Omegle chat room between n number
    of users.

    Handles notification of users and accepts special commands
    and nickname setting.
    """
    pass


class Ominer(object):
    """Initiates n number of conversations in separate threads and
    logs them until a stranger disconnects.
    """
    pass
