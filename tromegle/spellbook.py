#!/usr/bin/env python
import tromegle.language
from tromegle.event import spell, Transmogrifier


mfdict = {'m': 'f',
           'male': 'female',
           'guy': 'girl'}


@spell
def sex_change(t, ev, levdist=2):
    if Transmogrifier.isMessage(ev):
        msg = tromegle.language.tokenize(ev.data)

# TODO:  levenshtein distance
        # iterate over words, flipping all matches
        new_msg = map(tromegle.language.fuzzyCaps,
                      (mfdict.get(token, token) for token in msg),
                      msg)

        ev = Transmogrifier.modifyMessage(ev, new_msg)

    return ev
