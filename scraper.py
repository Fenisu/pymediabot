#!/usr/bin/python
import sys
import os
import logging as log

import keyfiles
#import guessit
import tmdbsimple
from pytvdbapi import api as tvdbapi

IMDBURL = 'www.imdb.com/title/'
LANG = 'en'


def tmdbsearch(title):
    """tmdbsearch will search the TMDB after the title and return
    the info found from the first match. A second call to tmdb
    is necessary because the search call will only return some
    of the info expected.

    :param title: the title to search for.
    :type title: string from guessit
    :return: found TMDB movie with its info
    :rtype: dict of TMDB

    """
    tmdbsimple.API_KEY = keyfiles.TMDBKEY
    search = tmdbsimple.Search()
    search.movie(query='%s' % title)  # response = search..
    results = search.results  # Match first result
    log.debug("Found %d results." % len(results))
    results_names = []
    for movie in results:
        results_names.append(movie['title'])
    if len(results_names) >= 3:
        log.info(" %s...." % ' * '.join(results_names[0:3]))
    else:
        log.info(" %s." % ' * '.join(results_names))
    result = tmdbsimple.Movies(results[0]['id']).info()
    return result


def tmdbget(imdbid):
    """tmdbget is a simple get from the TMDB with the known imdbid

    :param imdbid: imdb ID to get the movie info
    :type imdbid: string
    :return: found TMDB movie with its info
    :rtype: dict of TMDB

    """
    tmdbsimple.API_KEY = keyfiles.TMDBKEY
    tmdbmovie = tmdbsimple.Movies(imdbid)
    result = tmdbmovie.info()
    return result


def createtvs(show, season, episode, TVSM):
    """createtvs will transform a Show object inherited from the
    pytvdbapi library to a dict.

    :param show: imdb ID to get the movie info
    :type imdbid: string
    :return: found TMDB movie with its info
    :rtype: dict of TMDB

    """
    tvsepisode = {
        'tvsname': '%s' % show.SeriesName,
        'season': '%s' % season,
        'episode': '%s' % episode,
        'episodename': '%s' % show[season][episode].EpisodeName
    }

    if TVSM:
        log.debug("Multi-episode found: %s episodes" % TVSM)
        tvsepisode['multi'] = '%s' % TVSM
        for epiloop in xrange(TVSM - 1):
            episode = episode + epiloop + 1
            tvsepisode['episode%s' % (epiloop + 1)] = episode
            tvsepisode['episode%sname' % (epiloop + 1)] = \
                show[season][episode].EpisodeName
    log.debug("Episode dictionary: %s" % tvsepisode)
    return tvsepisode


def tvdbsearch(title, season, episode, TVSM=False):
    """tvdbsearch will search the TVDB after the title and return
    the info found from the first match.

    :param title: the title to search for
    :type title: string from guessit
    :param season: the season of the episode
    :type season: integer from guessit
    :param episode: the episode number of the episode
    :type episode: integer from guessit
    :param TVSM: quantity of episodes on the same file
    :type TVSM: integer or boolean if default
    :return: found TVDB movie with its info
    :rtype: dict of TVDB

    """
    tvdb = tvdbapi.TVDB(keyfiles.TVDBKEY)
    results = tvdb.search('%s' % title, LANG)  # Match first result
    log.debug("Found %d results." % len(results))
    resultsnames = []
    for tvs in results:
        resultsnames.append(tvs.SeriesName)
    if len(resultsnames) >= 3:
        log.debug(" %s...." % ' * '.join(resultsnames[0:3]))
    else:
        log.debug(" %s." % ' * '.join(resultsnames))

    result = results[0]
    tvs = createtvs(result, season, episode, TVSM)
    return tvs


def tvdbget(imdbid, season, episode, TVSM=False):
    """tvdbget is a simple get from the TVDB with the known imdbid.

    :param imdbid: imdb ID to get the movie info
    :type imdbid: string
    :param season: the season of the episode
    :type season: integer from guessit
    :param episode: the episode number of the episode
    :type episode: integer from guessit
    :param TVSM: quantity of episodes on the same file
    :type TVSM: integer or boolean if default
    :return: found TVDB movie with its info
    :rtype: dict of TVDB

    """
    tvdb = tvdbapi.TVDB(keyfiles.TVDBKEY)
    result = tvdb.get_series(imdbid, LANG, 'imdb')
    tvs = createtvs(result, season, episode, TVSM)
    return tvs


def parsenfo(file):
    """This will search for the imdbid in a nfo file.

    :param file: the file.nfo
    :type file: string
    :return: the imdbid parsed from the file
    :rtype: string

    """
    with open(file) as fo:
            for line in fo:
                if IMDBURL in line:
                    pos = line.find(IMDBURL)
                    start = pos + len(IMDBURL)
                    end = start + 9
                    imdbid = line[start:end]
                    log.debug("IMDB ID Found.")
                    return imdbid
    log.debug("IMDB ID NOT Found.")


def searchnfo(path):
    """This will search for a nfo file

    :param path: the path of the directory
    :type path: string
    :return: the file.nfo found to be parsed
    :rtype: string

    """
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    for f in os.listdir(path):
        if f.lower().endswith('.nfo'):
            log.debug("NFO Found.")
            return os.path.join(path, f)
    log.debug("NFO NOT Found.")


def main(input_item):
    '''
    It will either find the IMDB ID in a nfo file or it will
    guess the title from the file/directory name. Then it will
    retrieve the info from tmdb or search and retrieve the info
    from the first match respectively.
    '''
    #guessed, MOVIE, TVSM = guesstype(path)
    try:
        log.debug("Searching for nfo file.")
        nfofile = searchnfo(input_item)
        log.debug("Parsing file.")
        imdbid = parsenfo(nfofile)
        if input_item['movie']:
            log.debug("Calling tmdbget for %s." % imdbid)
            media = tmdbget(imdbid)
            log.debug("Movie fetched.")
        else:
            log.debug("Calling tvdbget for %s." % imdbid)
            if 'TVSM' in input_item['guess']:
                media = tvdbget(imdbid, input_item['guess']['season'],
                                input_item['guess']['episodeNumber'],
                                input_item['guess']['TVSM'])
            else:
                media = tvdbget(imdbid, input_item['guess']['season'],
                                input_item['guess']['episodeNumber'])
            log.debug("TV Show fetched.")
    except:
        log.debug("Fallback: Guessed name.")
        if input_item['movie']:
            log.debug("Calling tmdbsearch with %s." %
                      input_item['guess']['title'])
            media = tmdbsearch(input_item['guess']['title'])
            log.debug("Movie fetched.")
        else:
            log.debug("Calling tvdbsearch with %s." %
                      input_item['guess']['series'])
            if 'TVSM' in input_item['guess']:
                media = tvdbsearch(
                    input_item['guess']['series'],
                    input_item['guess']['season'],
                    input_item['guess']['episodeNumber'],
                    input_item['guess']['TVSM'])
            else:
                media = tvdbsearch(
                    input_item['guess']['series'],
                    input_item['guess']['season'],
                    input_item['guess']['episodeNumber'])
            log.debug("TV Show fetched.")
    return media


if __name__ == "__main__":
    media = main(sys.argv[1], True)
    #try:
    #    print("Movie: %s (%s)\nRuntime: %s min\nIMDB ID: %s\nPlot: %s" %
    #          (media['title'], media['release_date'][0:4],
    #           media['runtime'], media['imdb_id'], media['overview']))
    #except:
    #    print("Show %s" % (media['tvsname']))
