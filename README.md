pymediabot
==========

Console tool for organizing your movies, tvshows and anime. Aiming for simplistic usage and the results of filebot, but written in python.

So far, only _Movies_ are supported.

How to use it
-------------

You need a valid TMDB API KEY. Then you create a file called *keyfiles.py* with this text on it:

    TMDBKEY = 'KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK'
    
The point is to be as similar to filebot as possible, e.g.:

    python pymediabot.py --action copy --conflict skip --output /srv/Movies --set movieFormat="{n} ({y})/{fn}" /home/user/encode/file.mkv

For further information:

    python pymediabot.py -h


Dependencies
------------

    python-guessit
    tmdbsimple

Bugs
====
If you find any bug or want to request a new feature, please use
the [issue tracker](https://github.com/Fenisu/pymediabot/issues)
associated with the project.

Try to be as detailed as possible when filing a bug, preferably providing a
patch or a test case illustrating the issue.

Contact
=======
To get in contact with me, you can send me an email at
dreamtrick@gmail.com

License
=======
**pytvdbapi** is released under the [GPL 3](http://opensource.org/licenses/GPL-3.0) license. See the
LICENSE.txt file for more details.
