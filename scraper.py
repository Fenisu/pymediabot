#!/usr/bin/python
import sys, os

import keyfiles
import guessit, tmdbsimple

IMDBURL = 'www.imdb.com/title/'	

def main(path,verbose):
	'''
	It will either find the IMDB ID in a nfo file or it will 
	guess the title from the file/directory name. Then it will
	retrieve the info from tmdb or search and retrieve the info 
	from the first match respectively.
	'''
	try:
		if verbose: print "+ Searching for nfo file."
		nfofile = searchnfo(path,verbose)
		if verbose: print "+ Parsing file."
		imdbid = parsenfo(nfofile, verbose)
		if verbose: print "+ Calling tmdbget for &s." % imdbid
		movie = tmdbget(imdbid)
		if verbose: print "+ Movie fetched."
	except:
		if verbose: print "+ Fallback: Guessing name."
		guessmovie = guesspath(path, verbose)
		if verbose: print "+ Calling tmdbsearch with %s." % guessmovie['title']
		movie = tmdbsearch(guessmovie['title'], verbose)
		if verbose: print "+ Movie fetched."
	return movie

def searchnfo(path, verbose):
    '''
    This will search for a nfo file
    '''
    if os.path.isdir(path):
        for f in os.listdir(path):
    		if f.lower().endswith('.nfo'):
    			if verbose: print "+ NFO Found."
    			return os.path.join(path,f)
    if verbose: print "+ NFO NOT Found." 

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
	                if verbose: print "+ IMDB ID Found." 
	                return imdbid
	if verbose: print "+ IMDB ID NOT Found." 

def guesspath(path, verbose):
    '''
    guessit version 0.5.4 needs file extension to guess. 
    Newly guessit version 0.7.1 can accept directory names.
    '''
    guess = guessit.guess_video_info(path)

    if verbose: 
    	try:
    		print "+ Guess: %s (%s)." % (guess['title'], 
    									guess['year'])
    	except:
    		print "+ Guess: %s." % guess['title']
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
	response = search.movie(query='%s' % title)
	results = search.results # Match first result
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

if __name__ == "__main__":
	movie = main(sys.argv[1],True)
	print "Movie: %s (%s)\nRuntime: %s min\nIMDB ID: %s\nPlot: %s" % (movie['title'], 
		movie['release_date'][0:4], movie['runtime'], 
		movie['imdb_id'], movie['overview'])