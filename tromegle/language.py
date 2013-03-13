#!/usr/bin/env python
# from string import punctuation, whitespace
# from itertools import groupby, tee, izip
import re
from functools import wraps
import Levenshtein as strndist
import unicodedata


def normalize_unicode_(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        args_normed = []
        for a in args:
            if isinstance(a, unicode):
                a = unicodedata.normalize('NFD', a)
            args_normed.append(a)

        kwargs_normed = {}
        for k, v in kwargs.items():
            if isinstance(k, unicode):
                k = unicodedata.normalize(a, 'NFD')
            if isinstance(v, unicode):
                v = unicodedata.normalize(v, 'NFD')
            kwargs_normed[k] = v
        return func(*args, **kwargs)
    return wrapper


def mapCapitals(phrase):
    """Return a tuple of indexes for which str.islower is False

    phrase : str
        Phrase to search for capital letters

    return : tuple
        Indexes of capital letters
    """
    return tuple(i for i, boolval in enumerate(map(str.islower, phrase))
                 if not boolval and phrase[i].isalpha())


def fuzzyCaps(n_token, o_token):
    """Attempt to infer capitalization of a transformed token based on heuristic analysis
    of its original form.

    n_token : str
        New (transformed) token

    o_token : str
        Original token

    return : str
        Best-guess capitalized token
    """
    if o_token == n_token:
        return n_token

    if o_token.istitle():
        return n_token.title()

    if o_token.islower():
        return n_token.lower()

    if o_token.isupper():
        return n_token.upper()

    return n_token.lower()


class Tokenizer(object):
    _other = '\s+|\w+|[^\s\w]+'

    def __init__(self, stop_words=set(), case_sensitive=False):
        self.case_sensitive = case_sensitive

        self.stop_words = stop_words
        stop_words = '|'.join(re.escape(x) + r'\b' for x in stop_words)
        self.token_regex = stop_words + '|' + self._other if stop_words else self._other

    def __call__(self, phrase, case_sensitive_override=None):
        case_sensitive = case_sensitive_override if (case_sensitive_override is not None) else self.case_sensitive
        flag = 0 if case_sensitive else re.IGNORECASE

        return re.findall(self.token_regex, phrase, flag)


# def tokenize(phrase, stop_words=set()):
#     """Parse a string into words (strings separated by whitespace.

#     All punctuation characters and typographical symbols are treated as
#     an individual word.

#     phrase : str
#         Phrase to serparate into words.

#     return : list
#         List of words.
#     """
#     stop_words = '|'.join(re.escape(x) + r'\b' for x in stop_words)
#     other = '\s+|\w+|[^\s\w]+'
#     regex = stop_words + '|' + other if stop_words else other
#     return re.findall(regex, phrase, re.IGNORECASE)


# #   NEED TO OPTIMIZE:  looks like exponential time
# def tokenize(phrase, stop_words=None):
#     """Parse a string into words (strings separated by whitespace.

#     All punctuation characters and typographical symbols are treated as
#     an individual word.

#     phrase : str
#         Phrase to serparate into words.

#     return : list
#         List of words.
#     """
#     separators = dict.fromkeys(whitespace + punctuation, True)
#     tokens = [''.join(g) for _, g in groupby(phrase, separators.get)]

#     if stop_words:
#         assert isinstance(stop_words, set), 'stop_words must be a set'
#         window = 2  # Iterating over single tokens is useless
#         while window <= len(tokens):
#             # "sliding window" over token list
#             iters = tee(tokens, window)
#             for i, offset in izip(iters, xrange(window)):
#                 for _ in xrange(offset):
#                     next(i, None)

#             # Join each window and check if it's in `stop_words`
#             for offset, tkgrp in enumerate(izip(*iters)):
#                 tk = ''.join(tkgrp)
#                 if tk in stop_words:
#                     pre = tokens[0: offset]
#                     post = tokens[offset + window + 1::]
#                     tokens = pre + [tk] + post
#                     window = 1  # will be incremented after breaking from loop
#                     break

#             window += 1

#     return tokens


def isSymbol(char):
    """Determine if character is a non-numerical, non-alphabetical symbol.

    char : str
        String of length 1

    return : bool
        True if symbol
    """
    assert len(char) == 1, 'char must be of length 1'
    return not char.isalpha and not char.isdigit and not char.isspace


class SubstitutionMap(dict):
    """String replacement with fuzzy matching and formatting inference.

    Fuzzy matching uses an edit distance metric (Levenshtein distance by default)
    to determine if a string comparison is a match.  If either the input token or
    the tranlation (output) candidate is of length-1, the algorithm requires an
    exact (case-insensitive) match.  All string comparison is case-insensitive by
    default.

    In addition to the kwarg parameters accepted by dict, SubstitutionMap
    accepts the following kwarg params:

    edit_fn : function or callable object
        function to calculate edit distance.  By default, Levenshtein
        distance is used.

    dist : int or float
        Maximum edit distance for fuzzy string matching.  The exact type
        for this parameter will depend on the edit_fn being used.  The
        default edit_fn uses an int.

        Defaults to 0 (exact match)

    case_sensitive : bool
        If True, string comparisons are case-sensitive.
        Defaults to False.
    """
    def __init__(self, *args, **kwargs):
        # edit distance function
        self.edit_fn = kwargs.get('edit_fn') or strndist.distance

        # max levenshtein distance
        self.dist = kwargs.get('dist') or 0

        # case sensitivity
        self.case_sensitive = kwargs.get('case_sensitive') or False

        self.update(*args, **kwargs)
        self._convert_to_unicode()

    def __call__(self, tokens):
        return self.translate(tokens)

    def _convert_to_unicode(self):
        for key in self:
            value = self.pop(key)

            if isinstance(key, str):
                key = unicode(key)
            if isinstance(value, str):
                value = unicode(value)

            self[key] = value

    def translate(self, tokens):
        """Translate tokens based on contents of the SubstitutionMap.

        tokens : sequence
            Sequence of tokens to be matched and translated.
        """
        out_tokens = []
        for token in tokens:
            for orig, replace in self.iteritems():
                if self.match(orig, token):
                    token = fuzzyCaps(replace, token)
                    break  # avoid re-translating the modified token

            out_tokens.append(token)

        return ''.join(out_tokens)

    @normalize_unicode_
    def match(self, s1, s2):
        # use exact matching for length-1 tokens (both original and replacement)
        if len(s1) == 1 or len(s2) == 1:
            dist = 0
        else:
            dist = self.dist

        if not self.case_sensitive:
            s1, s2 = s1.lower(), s2.lower()

        return self.edit_fn(s1, s2) <= dist
