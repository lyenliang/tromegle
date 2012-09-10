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
