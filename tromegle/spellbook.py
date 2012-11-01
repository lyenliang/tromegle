#!/usr/bin/env python
from tromegle.event import spell, Transmogrifier


@spell
def sex_change(t, ev, levdist=2):
    if Transmogrifier.isMessage(ev):
        msg = ev.data
        new_msg = []

            # flip single-letters

            # transform "male" into "female" & vice-versa

            # flip f->m && m->f in xx/yy/zz format

            # flip f->m && m->f in xx/yy format (ex:  m27 or 27m)

        # Modify message
        new_msg = ' '.join([w for w in new_msg])
        ev = Transmogrifier.modifyMessage(ev, new_msg)

    return ev
