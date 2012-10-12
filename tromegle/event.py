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
NULL_EVENT = OmegleEvent(None, None, None)

# Reactor events
_ReactorEvent = namedtuple('ReactorEvent', ['type', 'data'])
IDLE_TIMEOUT = 'timeout'

# Message Modified event
_MessageModifiedEvent = namedtuple('MessageModifiedEvent', ['type', 'data', 'old'])
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


def spell(fn):
    """Spell decorator
    """
    if fn is not None:  # TODO:  wrapper function to reject events for which Transmogrifier.isMessage == False
        return fn
    else:
        def throwNone(out, ev):
            return None
        return throwNone


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
        if ev.type == MESSAGE_MODIFIED:
            ev = ev.old
        return MessageModifiedEvent(new_msg, ev)

    def output(self, ev):
        """Output event to the registered event queue.
        """
        assert self._evQueue is not None, 'Transmogrifier is not connected.'
        self._evQueue.append(ev)

    @staticmethod
    def levenshtein_dist(s1, s2):
        """
        Use:
        ====
        levenshtein_dist offers an intuitive metric for the "closeness"
        of two strings.  It is useful for catching permutation of target strings
        that differ in such aspects as capitalization and misspellings.

        Note:  for single words, a distance of 2 or 3 will catch most permutations.


        Details:
        ========
        Calculate the Levenshtein edit-distance between two strings.
        The edit distance is the number of characters that need to be
        substituted, inserted, or deleted, to transform s1 into s2.  For
        example, transforming "rain" to "shine" requires three steps,
        consisting of two substitutions and one insertion:
        "rain" -> "sain" -> "shin" -> "shine".  These operations could have
        been done in other orders, but at least three steps are needed.

        :param s1, s2: The strings to be analysed
        :type s1: str
        :type s2: str
        :rtype int
        """
        # set up a 2-D array
        len1 = len(s1)
        len2 = len(s2)
        lev = Transmogrifier._edit_dist_init(len1 + 1, len2 + 1)

        # iterate over the array
        for i in range(len1):
            for j in range(len2):
                Transmogrifier._edit_dist_step(lev, i + 1, j + 1, s1[i], s2[j])

        return lev[len1][len2]

    @staticmethod
    def _edit_dist_init(len1, len2):
        """from NLTK 2.0
        """
        lev = []
        for i in range(len1):
            lev.append([0] * len2)  # initialize 2-D array to zero
        for i in range(len1):
            lev[i][0] = i  # column 0: 0,1,2,3,4,...
        for j in range(len2):
            lev[0][j] = j  # row 0: 0,1,2,3,4,...
        return lev

    @staticmethod
    def _edit_dist_step(lev, i, j, c1, c2):
        """from NLTK 2.0
        """
        a = lev[i - 1][j] + 1  # skipping s1[i]
        b = lev[i - 1][j - 1] + (c1 != c2)  # matching s1[i] with s2[j]
        c = lev[i][j - 1] + 1  # skipping s2[j]
        lev[i][j] = min(a, b, c)  # pick the cheapest
