#!/usr/bin/env python

from blessings import Terminal
from core import CBDictInterface


class Viewport(CBDictInterface):
    """Interface for printing conversations to standard output.

    ~~~DEPRECATED~~~
    """
    def __init__(self, callbackdict=None):
        super(Viewport, self).__init__(callbackdict)
        self.strangers = {}
        self.ready = 0  # no strangers connected

        print "WARNING:  This class is deprecated; It is no longer under active development and is retained as a convenience only.  Use InteractiveViewport instead."

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

        self.term = Terminal()
        sc = [self.term.color(i) for i in xrange(1, 7)]
        self.strangerColLabels = tuple(sc)  # tweak order of colors
        self.strangerColors = {}

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
            self.write('')
            self.ready = 0

    def on_strangerDisconnected(self, ev):
        output = self.strangers[ev.id] + " has disconnected"
        self.write(self.formatNotification(output), '')  # print empty string to skip a line
        self.strangers.clear()

    def on_error(self, ev):
        self.write(self.formatError(ev.id, ev.data))

    def on_gotMessage(self, ev):
        self.write(self.formatMessage(ev.id, ev.data))

    def on_timeout(self, ev):
        self.write(self.formatNotification("Idle timeout."))
        self.strangers.clear()

    def on_messageModified(self, ev):
        mod_string, orig_string = self.formatCorrection(ev.data['old'].id, ev.data['msg'], ev.data['old'].data)
        self.write(mod_string, orig_string)

    def formatNotification(self, string):
        return "{t.red}{msg}{t.normal}".format(t=self.term, msg=string)

    def formatMessage(self, sid, msg):
        """Return a string with standard Omegle message formatting.

        sid : str
            Stranger id string

        msg : str
            Message body.
        """
        strngrName = self.strangers[sid]
        return "{t.bold}{color}{strngr}: {t.normal}{msg}".format(t=self.term, color=self.strangerColors[sid], strngr=strngrName, msg=msg)

    def formatCorrection(self, stranger_id, mod_string, orig_string):
        mod_string = self.formatMessage(stranger_id, mod_string)

        indent = ' ' * len(self.strangers[stranger_id])
        orig_string = "{t.cyan}{0}  {msg}{t.normal}".format(indent, t=self.term, msg=orig_string)
        return mod_string, orig_string

    def formatError(self, sid, err_msg):
        return "{t.bold}{t.red_on_white}ERROR <{s}>: {t.normal}{t.red_on_white}{msg}{t.normal}".format(t=self.term, s=self.strangers[sid], msg=err_msg)

    def write(self, *args):
        """Print message to output.
        """
        for msg in args:
            print msg


class EventLogger(object):
    """Class to log Tromegle events for debugging purposes.
    """
    def __init__(self, logfile='tromegleEvents.log', backupCount=2, maxbytes=200):
        import logging
        import logging.handlers
        self.file = logfile
        self.logger = logging.getLogger('tromegleEvents')
        self.logger.setLevel(logging.DEBUG)
        self.handler = logging.handlers.RotatingFileHandler(self.file,
                                                            maxBytes=maxbytes,
                                                            backupCount=backupCount)
        self.logger.addHandler(self.handler)

    def notify(self, ev):
        self.logger.debug('{0}'.format(ev))


class MessageLogger(CBDictInterface):
    """
    """
    def __init__(self, logfile='chat.log', backupCount=10, maxbytes=0, callbackdict=None):
        super(MessageLogger, self).__init__(callbackdict)
        self.strangers = {}

        import logging
        import logging.handlers
        self.lognum = 0
        self.file = logfile
        self.logger = logging.getLogger('tromegleChat')
        self.logger.setLevel(logging.DEBUG)
        self.handler = logging.handlers.RotatingFileHandler(self.file,
                                                            maxBytes=maxbytes,
                                                            backupCount=backupCount)
        self.logger.addHandler(self.handler)

    def on_idSet(self, ev):
        tag = 'Stranger_{0}'.format(len(self.strangers.keys()) + 1)
        self.strangers[ev.id] = tag

    def on_connected(self, ev):
        if self.lognum:
            self.handler.doRollover()
        self.lognum += 1

    def on_strangerDisconnected(self, ev):
        self.log("{0} disconnected".format(self.strangers[ev.id]))

    def on_gotMessage(self, ev):
        self.log("{strngr}: {msg}".format(strngr=self.strangers[ev.id], msg=ev.data))

    def on_messageModified(self, ev):
        stranger = self.strangers[ev.data['old'].id]
        mod_string = "{0}: {1}".format(stranger, ev.data)
        orig_string = "{0}  {1}".format('' * len(stranger), ev.data['old'].data)
        self.log(mod_string, orig_string)

    def log(self, *args):
        for msg in args:
            self.logger.debug(msg)
