#!/usr/bin/env python
from string import punctuation, whitespace
from itertools import groupby


def mapCapitals(phrase):
    """Return a tuple of indexes for which str.islower is False

    phrase : str
        Phrase to search for capital letters

    return : tuple
        Indexes of capital letters
    """
    return tuple(char for char in map(str.islower, tuple(phrase)) if not char)


def tokenize(phrase, sepcat=True):
    """Parse a string into words (strings separated by whitespace.

    All punctuation characters and typographical symbols are treated as
    an individual word.

    phrase : str
        Phrase to serparate into words.

    sepcat : bool
        Separator concatination.
        If true, adjacent separators will be concatenated into a single token.

    return : list
        List of words.
    """
    separators = dict.fromkeys(whitespace + punctuation, True)
    return [''.join(g) for _, g in groupby(phrase, separators.get)]


def isSymbol(char):
    """Determine if character is a non-numerical, non-alphabetical symbol.

    char : str
        String of length 1

    return : bool
        True if symbol
    """
    assert len(char) == 1, 'char must be of length 1'
    return not char.isalpha and not char.isdigit and not char.isspace


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
