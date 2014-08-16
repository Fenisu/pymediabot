#!/usr/bin/python
import sys
import os

import keyfiles
import guessit
import tmdbsimple
from pytvdbapi import api as tvdbapi

IMDBURL = 'www.imdb.com/title/'
LANG = 'en'
MOVIE = False
TVS = False
TVSM = False


def main(path, verbose):
    '''
    It will either find the IMDB ID in a nfo file or it will
    guess the title from the file/directory name. Then it will
    retrieve the info from tmdb or search and retrieve the info
    from the first match respectively.
    '''
    if verbose:
        print "+ Guessing name."
    guessed = guesspath(path, verbose)
    if guessed['type'] == 'episode':
#        TVS = True
        if 'episodeList' in guessed:
            TVSM = len(guessed['episodeList'])
        else:
            TVSM = False
        MOVIE = False
    elif guessed['type'] == 'video':
        MOVIE = True
    else:
        print "Could not guess if Movie or TV Show"
        sys.exit()

    try:
        if verbose:
            print "+ Searching for nfo file."
        nfofile = searchnfo(path, verbose)
        if verbose:
            print "+ Parsing file."
        imdbid = parsenfo(nfofile, verbose)
        if MOVIE:
            if verbose:
                print "+ Calling tmdbget for %s." % imdbid
            media = tmdbget(imdbid)
            if verbose:
                print "+ Movie fetched."
        else:
            if verbose:
                print "+ Calling tvdbget for %s." % imdbid
            media = tvdbget(imdbid, guessed['season'],
                            guessed['episodeNumber'], TVSM, verbose)
            if verbose:
                print "+ TV Show fetched."
    except:
        if verbose:
            print "+ Fallback: Guessed name."
        if MOVIE:
            if verbose:
                print "+ Calling tmdbsearch with %s." % guessed['title']
            media = tmdbsearch(guessed['title'], verbose)
            if verbose:
                print "+ Movie fetched."
        else:
            if verbose:
                print "+ Calling tvdbsearch with %s." % guessed['series']
            media = tvdbsearch(
                guessed['series'], guessed['season'],
                guessed['episodeNumber'], TVSM, verbose)
            if verbose:
                print "+ TV Show fetched."
    return media


def searchnfo(path, verbose):
    '''
    This will search for a nfo file
    '''
    if os.path.isdir(path):
        for f in os.listdir(path):
            if f.lower().endswith('.nfo'):
                if verbose:
                    print "+ NFO Found."
                return os.path.join(path, f)
    if verbose:
        print "+ NFO NOT Found."


def parsenfo(file, verbose):
    '''
    This will search for the imdbid in a nfo file.
    '''
    with open(file) as fo:
            for line in fo:
                if IMDBURL in line:
                    pos = line.find(IMDBURL)
                    start = pos + len(IMDBURL)
                    end = start + 9
                    imdbid = line[start:end]
                    if verbose:
                        print "+ IMDB ID Found."
                    return imdbid
    if verbose:
        print "+ IMDB ID NOT Found."


def guesspath(path, verbose):
    '''
    guessit version 0.5.4 needs file extension to guess.
    Newly guessit version 0.7.1 can accept directory names.
    '''
    guess = guessit.guess_video_info(path)

    if verbose:
        if guess['type'] == 'video':
            try:
                print "+ Guess: %s (%s)." % \
                    (guess['title'], guess['year'])
            except:
                print "+ Guess: %s." % guess['title']

        else:
            print "+ Guess: %s." % guess['series']

        print "+ Guess: %s." % guess['type']
    return guess


def tmdbget(imdbid):
    '''
    tmdbget is a simple get from the TMDB with the known imdbid
    '''
    tmdbsimple.API_KEY = keyfiles.TMDBKEY
    tmdbmovie = tmdbsimple.Movies(imdbid)
    result = tmdbmovie.info()
    return result


def tmdbsearch(title, verbose):
    '''
    tmdbsearch will search the TMDB after the title and return
    the info found from the first match. A second call to tmdb
    is necessary because the search call will only return some
    of the info expected.
    '''
    tmdbsimple.API_KEY = keyfiles.TMDBKEY
    search = tmdbsimple.Search()
    search.movie(query='%s' % title)  # response = search..
    results = search.results  # Match first result
    if verbose:
        print "+ Found %d results." % len(results)
        resultsnames = []
        for m in results:
            resultsnames.append(m['title'])
        if len(resultsnames) >= 3:
            print "+   %s...." % ' * '.join(resultsnames[0:3])
        else:
            print "+   %s." % ' * '.join(resultsnames)

    result = tmdbsimple.Movies(results[0]['id']).info()
    return result


def createtvs(show, season, episode, TVSM, verbose):
    '''
    createtvs will transform a Show object inherited from the
    pytvdbapi library to a dict.
    '''
    tvsepisode = {
        'tvsname': '%s' % show.SeriesName,
        'season': '%s' % season,
        'episode': '%s' % episode,
        'episodename': '%s' % show[season][episode].EpisodeName
    }

    if TVSM:
        if verbose:
            print "+ Multi-episode found: %s episodes" % TVSM
        tvsepisode['multi'] = '%s' % TVSM
        for epiloop in xrange(TVSM - 1):
            episode = episode + epiloop + 1
            tvsepisode['episode%s' % (epiloop + 1)] = episode
            tvsepisode['episode%sname' % (epiloop + 1)] = \
                show[season][episode].EpisodeName
    if verbose:
        print "+ Episode dictionary: %s" % tvsepisode
    return tvsepisode


def tvdbget(imdbid, season, episode, TVSM, verbose):
    '''
    tvdbget is a simple get from the TVDB with the known imdbid
    '''
    tvdb = tvdbapi.TVDB(keyfiles.TVDBKEY)
    result = tvdb.get_series(imdbid, LANG, 'imdb')
    return createtvs(result, season, episode, TVSM, verbose)


def tvdbsearch(title, season, episode, TVSM, verbose):
    '''
    tvdbsearch will search the TVDB after the title and return
    the info found from the first match.
    '''
    tvdb = tvdbapi.TVDB(keyfiles.TVDBKEY)
    results = tvdb.search('%s' % title, LANG)  # Match first result
    if verbose:
        print "+ Found %d results." % len(results)
        resultsnames = []
        for tvs in results:
            resultsnames.append(tvs.SeriesName)
        if len(resultsnames) >= 3:
            print "+   %s...." % ' * '.join(resultsnames[0:3])
        else:
            print "+   %s." % ' * '.join(resultsnames)

    result = results[0]
    return createtvs(result, season, episode, TVSM, verbose)

if __name__ == "__main__":
    media = main(sys.argv[1], True)
    try:
        print "Movie: %s (%s)\nRuntime: %s min\nIMDB ID: %s\nPlot: %s" % \
            (media['title'], media['release_date'][0:4],
                media['runtime'], media['imdb_id'], media['overview'])
    except:
        print "Show %s" % (media['tvsname'])
