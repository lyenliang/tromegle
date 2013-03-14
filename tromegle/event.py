#!/usr/bin/env python
from collections import namedtuple, deque

# Omegle events
OmegleEvent = namedtuple('OmegleEvent', ['id', 'type', 'data'])
ID_SET = "idSet"
WAITING = "waiting"
CONNECTED = "connected"
TYPING = "typing"
STOPPED_TYPING = "stoppedTyping"
GOT_MESSAGE = "gotMessage"
DISCONNECTED = "strangerDisconnected"
ERROR = "error"
TIMEOUT_EVENT = 'connectionTimeout'
NULL_EVENT = OmegleEvent(None, None, None)

# Reactor events
_ReactorEvent = namedtuple('ReactorEvent', ['type', 'data'])
IDLE_TIMEOUT = 'timeout'

# Transmogrifier Events
_MessageModifiedEvent = namedtuple('TransmogrifierEvent', ['type', 'data', 'old'])
MESSAGE_MODIFIED = 'messageModified'


def IdleTimeoutEvent(delta_t):
    return _ReactorEvent(IDLE_TIMEOUT, delta_t)


def MessageModifiedEvent(data, old):
    """Create MessageModifiedEvent.

    data : str
        New message string

    old : OmegleEvent
        The gotMessage OmegleEvent being modified.

    return : MessageModifiedEvent
    """
    return _MessageModifiedEvent(MESSAGE_MODIFIED, data, old)


def isEvent(obj):
    """Return True if object is a Tromegle event of any variety.
    """
    return hasattr(obj, '_fields')


def mkIterableSequence(obj):
    """Place obj in a tuple if obj is not a sequence container.

    Useful for handing cases where a single event can be passed to
        a function that habitually handles sequences of events.
    """
    if not hasattr(obj, '__iter__'):
        obj = (obj,)
    return obj


def spell_(fn):
    """Spell decorator
    """
    if fn is not None:
        return fn
    else:
        def throwNone(t, ev):
            return None
        return throwNone


def onlyMessages_(spell_fn):
    """Decorator which returns non-message events unaltered and passes
    message events to the spell it wraps.
    """
    def wrapper(t, ev):
        if t.isMessage(ev):
            return spell_fn(t, ev)
        else:
            return ev
    return wrapper


class Transmogrifier(object):
    def __init__(self, spells=()):
        self._spells = ()

        self._evQueue = None
        self.purge(spells)

    def __call__(self, events):
        """Cast all spells for each event in an iterable of events.
        """
        if isEvent(events):
            events = (events,)
        for ev in events:
            for spell in self._spells:
                ev = spell(self, ev)
            if ev:  # Functions may return None in order to "blackhole" an event
                self.output(ev)

    def connect(self, eventQueue):
        """Connect Transmogrifier to an eventQueue.
        """
        assert isinstance(eventQueue, deque), 'Event queue must be a deque.'
        self._evQueue = eventQueue

    def push(self, spell):
        self._spells.append(spell)

    def purge(self, spells=()):
        """Remove all spells from the Transmogrifier and optionally assigns
        new ones.

        spells : tuple or list
            Spells to add (in FIFO order).
        """
        self._spells = list(mkIterableSequence(spells))

    def getSpells(self):
        """Get spell queue.

        return:  tuple
            Tuple containing spells in the order in which they will be cast.
        """
        return tuple(self._spells)

    @staticmethod
    def isMessage(ev):
        """Returns True if event is a `gotMessage` or `messageModified` event.
        """
        return ev.type == MESSAGE_MODIFIED or ev.type == GOT_MESSAGE

    @staticmethod
    def modifyMessage(ev, new_msg):
        """Take in a gotMessage event and modify its message contents.

        ev : OmegleEvent
            Must be a gotMessage event.

        new_msg : str
            String with which to replace the original message.

        return : ReactorEvent
            ReactorEvent containing old and new message.
        """
        assert Transmogrifier.isMessage(ev), 'Cannot modify non-message events.'
        if ev.type == MESSAGE_MODIFIED:
            ev = ev.old  # make sure the original message is always in .old
        return MessageModifiedEvent(new_msg, ev)

    @staticmethod
    def msg_contents_modified(msg1, msg2):
        return msg1.strip().lower().replace(' ', '') != msg2.strip().lower().replace(' ', '')

    def output(self, ev):
        """Output event to the registered event queue.
        """
        assert self._evQueue is not None, 'Transmogrifier is not connected.'
        self._evQueue.append(ev)
