#!/usr/bin/env python
import tromegle.language as language
from tromegle.event import spell_


ts_dict = {'m': 'f', 'male': 'female', 'guy': 'girl'}
ts_map = language.SubstitutionMap(ts_dict, dist=1)
ts_stop = set(["I'm"])
ts_tokenizer = language.Tokenizer(stop_words=ts_stop)


@spell_
def sex_change(t, ev):
    if t.isMessage(ev):
        new_msg = ts_map(ts_tokenizer(ev.data))
        if t.msg_contents_modified(new_msg, ev.data):
            ev = t.modifyMessage(ev, new_msg)

    return ev
