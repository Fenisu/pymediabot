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
import logging

import scraper

log = logging.getLogger(__name__)


def exeaction(moviefile, dst, NEWDIR, action):
    log.debug("Creating and renaming.")
    if NEWDIR:
        os.makedirs(os.path.dirname(dst))
    if action == 'copy':
        log.debug("Copying.")
        shutil.copy(moviefile, dst)
    elif action == 'move':
        log.debug("Moving.")
        shutil.move(moviefile, dst)
    elif action == 'symlink':
        log.debug("Symlinking.")
        os.symlink(moviefile, dst)
    elif action == 'hardlink':
        log.debug("Hardlinking.")
        os.link(moviefile, dst)
    log.info("Done. ヾ(＠⌒ー⌒＠)ノ")


def exechanges(src, moviefile, dst, NEWDIR, action, conflict):
    if action == 'test':
        log.debug("Test action:")
        log.info("TEST: %s ->  %s" % (moviefile, dst))
    else:
        if os.path.exists(dst):
            log.debug("Destination exists.")
            if conflict == 'override':
                log.debug("Override ON.")
                exeaction(src, moviefile, dst, NEWDIR, action)
            elif conflict == 'auto':
                if os.stat(src).st_mtime > os.stat(dst).st_mtime:
                    log.debug("Override in auto mode, destination is older.")
                    exeaction(src, moviefile, dst, NEWDIR, action)
            else:
                log.error("FILE FOUND ON DESTINATION, OVERRIDE IS OFF")
                sys.exit()
        else:
            log.debug("Destination does not exist.")
            exeaction(moviefile, dst, NEWDIR, action)


def rename(string, filename, info):
    '''
    Parse --set movieFormat
    Parse --set serieFormat
    '''
    movieFormat = re.search('(?<=movieFormat=)"(.*?)"', string).group(1)
    serieFormat = re.search('(?<=serieFormat=)"(.*?)"', string).group(1)
    ext = filename[-3:]
    if 'episode' not in info:
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


def findfile(path):
    '''
    This code is to find the movie file, guessing that the movie file
    inside a directory is bigger than 90\% of the total size of it.
    '''
    # If the input is a directory, find movie
    if os.path.isdir(path):
        log.debug("Searching for movie file in directory.")
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
            log.debug(
                "Movie found: %s [%s bytes]" %
                (os.path.basename(fpn), fpsize))
            moviefile = fpn
        else:
            log.debug("No movie found under: %s" % path)
            log.error("FILE BIGGER THAN 90% OF DIRECTORY'S SIZE NOT FOUND.")
            log.error("THE PROGRAM COULD NOT FIND ANY MOVIE FILE.")
            sys.exit()
    # If the input is a file, we guess it is the movie
    else:
        moviefile = path
        log.debug(
            "The input was a movie.\n+ Movie found: %s [%s bytes]" %
            (os.path.basename(moviefile), os.stat(moviefile).st_size))
    log.info("Input: %s" % os.path.basename(moviefile))
    return moviefile


def parseinput():
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
    parser.add_argument('-v', '--verbose',
                        help='increase output verbosity',
                        action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    return args


def main():
    args = parseinput()
    log.info("INPUT: %s" % os.path.basename(args.PATH))
    # Grab media info
    mediainfo = scraper.main(args.PATH)
    if 'episode' not in mediainfo:
        # Grab movie file and directory
        mediafile = findfile(args.PATH)
        # Replace defined Format with real values
        dst = rename(args.set, mediafile, mediainfo)
    elif 'episode' in mediainfo and not os.path.isdir(args.PATH):
        mediafile = args.PATH
        # Replace defined Format with real values
        dst = rename(args.set, mediafile, mediainfo)
    else:
        log.error("ERROR FINDING FILE.")
    # Check if format has an added directory
    if os.path.split(dst.rstrip(args.output))[0] == '':
        NEWDIR = False
    else:
        NEWDIR = True
        log.debug("+ New destination has added directories.")
    # Update destination
    dst = os.path.join(args.output, dst)
    # Execute changes
    exechanges(
        args.PATH, mediafile, dst, NEWDIR,
        args.action, args.conflict)


if __name__ == "__main__":
    main()
