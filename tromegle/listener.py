#!/usr/bin/env python

from collections import deque
from core import CBDictInterface
from blessings import Terminal


class Viewport(CBDictInterface):
    """Interface for printing conversations to standard output.

    ~~~DEPRECATED~~~
    """
    def __init__(self, callbackdict=None):
        super(Viewport, self).__init__(callbackdict)
        self.strangers = {}
        self.ready = 0  # no strangers connected

    def on_idSet(self, ev):
        tag = 'Stranger_{0}'.format(len(self.strangers.keys()) + 1)
        self.strangers[ev.id] = tag
        print tag, "identified..."

    def on_waiting(self, ev):
        print "Waiting to connect to", self.strangers[ev.id]

    def on_connected(self, ev):
        print "Connected to", self.strangers[ev.id]
        self.ready += 1
        if self.ready == len(self.strangers.keys()):
            print
            self.ready = 0

    def on_strangerDisconnected(self, ev):
        print self.strangers[ev.id], "has disconnected."
        print
        print
        self.strangers.clear()

    def on_gotMessage(self, ev):
        print self.strangers[ev.id] + ": ", ev.data

    def on_timeout(self, ev):
        print "Idle timeout."
        self.strangers.clear()


class InteractiveViewport(CBDictInterface):
    """Interface for printing conversations, with intelligent formatting.
    """
    def __init__(self, callbackdict=None):
        super(InteractiveViewport, self).__init__(callbackdict)
        self.strangers = {}
        self.ready = 0  # no strangers connected

        self.messageQueue = deque()

        self.term = Terminal()
        sc = [t.color(i) for i in range(1,7)]
        self.strangerColLabels = tuple(sc.insert(1, sc.pop(3)))  # tweak order of colors
        self.strangerColors = {}

    def write(self, *args):
        """Add a message-carrying event to the output buffer and print the tail
        of the buffer.
        """
        for msg in args:
            self.messageQueue.append(msg)

        # "flip" the buffer

    def on_idSet(self, ev):
        tag = 'Stranger_{0}'.format(len(self.strangers.keys()) + 1)
        self.strangers[ev.id] = tag
        self.write(self.formatNotification('{0} identified...'.format(tag)))

    def on_waiting(self, ev):
        output = "Waiting to connect to " + self.strangers[ev.id]
        self.write(self.formatNotification(output))

    def on_connected(self, ev):
        output = "Connected to " + self.strangers[ev.id]
        self.write(self.formatNotification(output))

        self.ready += 1
        self.strangerColors[ev.id] = self.strangerColLabels[self.ready % len(self.strangerColLabels)]
        if self.ready == len(self.strangers.keys()):
            print
            self.ready = 0

    def on_strangerDisconnected(self, ev):
        output = self.strangers[ev.id] + " has disconnected"
        self.write(formatNotification(output))
        self.strangers.clear()

    def on_gotMessage(self, ev):
        output = self.strangers[ev.id] + ": " + ev.data
        self.write(self.formatMessage(output))

    def on_timeout(self, ev):
        self.write(self.formatNotification("Idle timeout."))
        self.strangers.clear()

    def on_messageModified(self, ev):
        # ev.data = (modified_msg, original_msg)
        self.write(self.formatMessage(ev.data[0]), self.formatCorrection(ev.data[1]))

    def formatNotification(self, string):
        return "{t.bold}{t.yellow}{msg}{t.normal}".format(t=self.term, msg=string)

    def formatMessage(self, stranger_id, string):
        return "{t.bold}{color}{sid}: {t.normal}{msg}".format(t=self.term, color=self.strangerColors[stranger_id], sid=stranger_id, msg=string)

    def formatCorrection(self, stranger_id, mod_string, orig_string):
        mod_string = self.messageFormat(stranger_id, mod_string)
        orig_string = "{t.cyan}{msg}{t.normal}".format(t=self.term, msg=orig_string)
        return mod_string, orig_string

