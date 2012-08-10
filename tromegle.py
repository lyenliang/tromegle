#!/usr/bin/env python

# import asyncore
# import socket
from urllib import urlencode
import urllib2 as url


class Partner(object):
    OMEGLE = "http://omegle.com/"
    START = OMEGLE + "start"
    EVENTS = OMEGLE + "events"
    SEND = OMEGLE + "send"
    TYPING = OMEGLE + "typing"
    DISCONNECT = OMEGLE + "disconnect"

    def __init__(self, name):
        self.typing = False
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
        evbuffer = evbuffer.replace('[', '').replace(']', '').replace('"', '')
        return evbuffer.split(',')
