pymediabot
==========

Console tool for organizing your movies, tvshows and anime. Aiming for simplistic usage and the results of filebot, but written in python.

So far, only Movies are supported.

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
