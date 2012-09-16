#!/usr/bin/env python
from collections import namedtuple, deque

OmegleEvent = namedtuple('OmegleEvent', ['id', 'type', 'data'])
ID_SET = "idSet"
WAITING = "waiting"
CONNECTED = "connected"
TYPING = "typing"
STOPPED_TYPING = "stoppedTyping"
GOT_MESSAGE = "gotMessage"
DISCONNECTED = "strangerDisconnected"
NULL_EVENT = OmegleEvent(None, None, None)

ReactorEvent = namedtuple('ReactorEvent', ['type', 'data'])
IDLE_TIMEOUT = 'timeout'


def spell(fn):
    """Spell decorator
    """
    if fn is not None:
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

    def push(self, spell):
        self._spells.append(spell)

    def output(self, ev):
        assert self._evQueue is not None, 'Transmogrifier is not connected.'
        self._evQueue.append(ev)

    def __call__(self, events):
        """Cast all spells for each event in an iterable of events.
        """
        for ev in events:
            for spell in self._spells:
                ev = spell(self, ev)
            if ev:  # Functions may return None in order to "blackhole" an event
                self.output(ev)

    def purge(self, spells=()):
        self._spells = list(spells)

    def connect(self, eventQueue):
        if not isinstance(eventQueue, deque):
            raise TypeError('Event queue must be a deque.')
        self._evQueue = eventQueue

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

    def _edit_dist_step(lev, i, j, c1, c2):
        """from NLTK 2.0
        """
        a = lev[i - 1][j] + 1  # skipping s1[i]
        b = lev[i - 1][j - 1] + (c1 != c2)  # matching s1[i] with s2[j]
        c = lev[i][j - 1] + 1  # skipping s2[j]
        lev[i][j] = min(a, b, c)  # pick the cheapest

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
        lev = _edit_dist_init(len1 + 1, len2 + 1)

        # iterate over the array
        for i in range(len1):
            for j in range(len2):
                _edit_dist_step(lev, i + 1, j + 1, s1[i], s2[j])

        return lev[len1][len2]
