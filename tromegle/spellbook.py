#!/usr/bin/env python
import tromegle.language
from tromegle.event import spell


ts_dict = {'m': 'f', 'male': 'female', 'guy': 'girl',
           'f': 'm', 'female': 'male', 'girl': 'guy'}
ts_map = tromegle.language.SubstitutionMap(ts_dict, dist=1)
ts_stop = set(["I'm", "i'm"])
ts_tokenizer = tromegle.language.Tokenizer(stop_words=ts_stop)


@spell
def sex_change(t, ev, levdist=2):
    if t.isMessage(ev):
        new_msg = ts_map(ts_tokenizer(ev.data))
        if t.msg_contents_modified(new_msg, ev.data):
            ev = t.modifyMessage(ev, new_msg)

    return ev
