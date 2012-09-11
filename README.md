Tromegle:  Troll Strangers!
========
Tromegle started as a project through which to learn about HTTP requests and asynchronous I/O.  The idea was
to learn how to use urllib(2) and later Twisted while having a bit of fun at the expense of a few [Omegle](http://omegle.com) users, or "strangers".
It has since evolved into an unofficial API, complete with a simple client class.

###Trolling is a Art!
The nonstandard functionality of Tromegle is centered around a relatively simple [man-in-the-middle attack](http://en.wikipedia.org/wiki/Man-in-the-middle_attack).

The power of Tromegle lies in the Transmogrifier class, which allows for the conditional modification or injection of AJAX events
and, by extension, user messages.  In plain English, this means **you can modify the message a user sends to another**
as well as pass messages that only one user will see!

###Trolling gently
Sometimes it's just fun to evesdrop; internet users are often funny despite themselves.  Tromegle gives you the
tools to either observe or record conversations, or relevant portions thereof.

Getting Tromegle
========
###Installing through pip

As of right now, the easiest way to obtain Tromegle is through pip.  Make sure pip is installed prior to running:

```pip install tromegle``` as root.


### Installing through Git

```git clone https://github.com/louist87/tromegle.git```

The package can then be installed withe the following commands:
```
cd tromegle
sudo python setup.py install
```

Dependencies
========
Tromegle requires that you have the latest version of [Twisted](http://twistedmatrix.com/) installed.

Canonical installation instructions can be found on the above website, but the following installation steps
should work.

###Ubuntu (or other Debian-based distro)

```sudo apt-get install python-twisted```

###Windows

Download the installer from [here][download]

###Any OS with pip installed (Mac/Win/*nix)

```pip install Twisted```

###OSX

I don't own an Apple computer (too rich for my blood), but I understand that [OSX has shipped with Twisted pre-installed-ish since 2007][osx].
So, there's a good chance that this code works with zero setup - woohoo! If you happen to have an OSX box, please give it a shot
and let me know how it goes. Thanks!

If you have trouble with the OSX version of Twisted, try [downloading the tarball][download] and installing it to a different `PYTHONPATH` than the default.

[download]: http://twistedmatrix.com/trac/wiki/Downloads
[osx]: http://twistedmatrix.com/trac/wiki/FrequentlyAskedQuestions#WhyamIgettingImportErrorsforTwistedsubpackagesonOSX10.5

Using Tromegle
========
So far, the MiddleMan class is the only attack that is working.  More work will follow, including documentation.

```python

import tromegle

m = tromegle.MiddleMan()
tromegle.reactor.run()
```
