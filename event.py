#!/usr/bin/env python
from collections import namedtuple, deque

Event = namedtuple('OmegleEvent', ['id', 'type', 'data'])


def spell(fn):
    """Spell decorator
    """
    if fn is not None:
        return fn
    else:
        def throwNone(out, ev):
            return None


class Transmogrifier(object):
    def __init__(self, spells=None):
        self.purge(spells)
        self.push = self._spells.append

    def __call__(self, events):
        """Cast all spells for each event in an iterable of events.
        """
        for ev in events:
            for spell in self._spells:
                ev = spell(self, ev)
            if ev:  # Functions may return None in order to "blackhole" an event
                self.output(ev)

    def purge(self, spells=None):
        if spells:
            self._spells = [s for s in spells]
        else:
            self._spells = []

    def connect(self, eventQueue):
        if not isinstance(eventQueue, deque):
            raise TypeError('Event queue must be a deque.')
        self._evQueue = eventQueue
        self.output = self._evQueue.append
