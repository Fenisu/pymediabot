#!/usr/bin/python
# -*- coding: utf-8 -*-

'''

Dependencies:

- tmdbsimple
- pytvdbapi

'''

import argparse

import re
import os
import shutil
import sys

import scraper


def exechanges(src, moviefile, dst, NEWDIR, action, conflict, verbose):
    if os.path.exists(dst):
        if verbose:
            print "+ Destination exists."
        if conflict == 'override':
            if verbose:
                print "+ Override ON."
            exeaction(src, moviefile, dst, NEWDIR, action, verbose)
        elif conflict == 'auto':
            if os.stat(src).st_mtime > os.stat(dst).st_mtime:
                if verbose:
                    print "+ Auto ON, destination is older."
                exeaction(src, moviefile, dst, NEWDIR, action, verbose)
        else:
            print "- FILE FOUND ON DESTINATION, OVERRIDE IS OFF"
            sys.exit()
    else:
        if verbose:
            print "+ Destination does not exist."
        exeaction(src, moviefile, dst, NEWDIR, action, verbose)


def exeaction(src, moviefile, dst, NEWDIR, action, verbose):
    if action == 'test':
        if verbose:
            print "+ Test action:"
        print("mv %s ->  %s" % (src, dst))
    else:
        if verbose:
            print "+ Creating and renaming."
        if NEWDIR:
            os.makedirs(os.path.dirname(dst))
    if action == 'copy':
        if verbose:
            print "+ Copying."
        shutil.copy(moviefile, dst)
    elif action == 'move':
        if verbose:
            print "+ Moving."
        shutil.move(moviefile, dst)
    elif action == 'symlink':
        if verbose:
            print "+ Symlinking."
        os.symlink(moviefile, dst)
    elif action == 'hardlink':
        if verbose:
            print "+ Hardlinking."
        os.link(moviefile, dst)
    print "- Done. ヾ(＠⌒ー⌒＠)ノ"


def rename(string, filename, info, verbose):
    '''
    Parse --set movieFormat
    Parse --set serieFormat
    '''
    movieFormat = re.search('(?<=movieFormat=)"(.*?)"', string).group(1)
    serieFormat = re.search('(?<=serieFormat=)"(.*?)"', string).group(1)
    #animeFormat = re.search('(?<=animeFormat=)"(.*?)"', string).group(1)
    ext = filename[-3:]
    if 'episode' not in info:
        #if verbose:
        #    movieFormat = re.sub(r'{fn}', 'Filename.ext', movieFormat)
        #    movieFormat = re.sub(r'{n}', 'Movie', movieFormat)
        #    movieFormat = re.sub(r'{y}', 'Year', movieFormat)
        #    movieFormat = re.sub(r'{ext}', 'ext', movieFormat)
        #    print "+ movieFormat: %s" % movieFormat

        movieFormat = re.sub(
            r'{fn}', '%s' % os.path.basename(filename), movieFormat)
        movieFormat = re.sub(
            r'{n}', '%s' % info['title'], movieFormat)
        movieFormat = re.sub(
            r'{y}', '%s' % info['release_date'][0:4], movieFormat)
        movieFormat = re.sub(
            r'{ext}', '%s' % ext, movieFormat)
        return movieFormat
    else:
        # if verbose add print
        serieFormat = re.sub(
            r'{fn}', '%s' % os.path.basename(filename), serieFormat)
        serieFormat = re.sub(
            r'{n}', '%s' % info['tvsname'], serieFormat)
        serieFormat = re.sub(
            r'{s}', '%s' % info['season'], serieFormat)
        serieFormat = re.sub(
            r'{en}', '%s' % info['episode'], serieFormat)
        serieFormat = re.sub(
            r'{e}', '%s' % info['episodename'], serieFormat)
        serieFormat = re.sub(
            r'{ext}', '%s' % ext, serieFormat)
        return serieFormat


def findfile(path, tvs, verbose):
    '''
    This code is to find the movie file, guessing that the movie file
    inside a directory is bigger than 90\% of the total size of it.
    '''
    # If the input is a directory, find movie
    if os.path.isdir(path) and not tvs:
        if verbose:
            print "+ Searching for movie file in directory."
        total_size = 0
        fpsizen = 0
        # Loop to add size of any file inside the directory
        # while saving the biggest file
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                fpsize = os.stat(fp).st_size
                if fpsizen < fpsize:
                    fpsizen = fpsize
                    fpn = fp
                total_size += fpsize
        # Check if the biggest file is bigger than 90%
        if fpsizen > (total_size * 0.9):
            if verbose:
                print "+ Movie found: %s [%s bytes]" % \
                    (os.path.basename(fpn), fpsize)
            moviefile = fpn
        else:
            if verbose:
                print "+ No movie found under: %s" % path
            print "- FILE BIGGER THAN 90% OF THE SIZE OF DIRECTORY NOT FOUND"
            print "- THE PROGRAM COULD NOT FIND ANY MOVIE FILE"
            sys.exit()
    # If the path is the directory with tvs episodes on it
    elif os.path.isdir(path) and tvs:
        pass
    # If the input is a file, we guess it is the movie
    else:
        moviefile = path
        if verbose:
            print "+ The input was a movie.\n+ Movie found: %s [%s bytes]" % \
                (os.path.basename(moviefile),
                    os.stat(moviefile).st_size)
    print "- Input: %s" % os.path.basename(moviefile)
    return moviefile


def main():
    parser = argparse.ArgumentParser(
        description='Console tool for organizing your movies, \
        tvshows and anime. Aiming for simplistic usage and the results of \
        filebot, but written in python.',
        epilog='Report du bugs to https://github.com/Fenisu/pymediabot\
        General help using GNU software: <http://www.gnu.org/gethelp/>.')
    parser.add_argument('PATH', help='input path')
    parser.add_argument('-o', '--output',
                        help='output path (default: ~/Videos)',
                        default='~/Videos')
    parser.add_argument('--action',
                        help='rename action: move, copy, symlink, hardlink, \
                    test (default: test)',
                        default='test')
    parser.add_argument('--conflict',
                        help='handle override: auto, skip, override \
                    (default: skip)',
                        default='skip')
    parser.add_argument('--set',
                        help='set movieFormat, serieFormat, animeFormat \
                    (default movieFormat="{n} ({y})/{fn}" \
                    serieFormat="{n}/Season {s}/{n} - S{s}E{en} - {e}.{ext})',
                        default='movieFormat="{n} ({y})/{fn}" \
                    serieFormat="{n}/Season {s}/{n} - S{s}E{en} - {e}.{ext}"')
                        #animeFormat="{n}/{n} - {en} - {e}.{ext}"
    parser.add_argument('-v', '--verbose',
                        help='increase output verbosity',
                        action='store_true')
    args = parser.parse_args()

    # Grab media info
    mediainfo = scraper.main(args.PATH, args.verbose)
    if 'episode' not in mediainfo:
        # Grab movie file and directory
        mediafile = findfile(args.PATH, False, args.verbose)
        # Replace defined Format with real values
        dst = rename(args.set, mediafile, mediainfo, args.verbose)
    elif 'episode' in mediainfo and not os.path.isdir(args.PATH):
        mediafile = args.PATH
        # Replace defined Format with real values
        dst = rename(args.set, mediafile, mediainfo, args.verbose)
    else:
        print "- ERROR FINDING FILE."
    # Check if format has an added directory
    print dst
    if os.path.split(dst.rstrip(args.output))[0] == '':
        NEWDIR = False
    else:
        NEWDIR = True
        if args.verbose:
            print "+ New destination has added directories."
    # Update destination
    dst = os.path.join(args.output, dst)
    # Execute changes
    exechanges(
        args.PATH, mediafile, dst, NEWDIR,
        args.action, args.conflict, args.verbose)


if __name__ == "__main__":
    main()
