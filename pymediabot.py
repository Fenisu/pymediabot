#!/usr/bin/python
# -*- coding: utf-8 -*-

'''

Dependencies:

- tmdbsimple
- guessit
- pytvdbapi

'''

import argparse

import re
import os
import shutil
import sys
import logging

import scraper
import guessit

log = logging.getLogger(__name__)
extensions = ['mkv', 'mp4', 'avi']


def exe_action(src, dst, action):
    """Applies the changes that are expected depending on the action.

    :param src: subtitle to download.
    :type src: string
    :param dst: destination where the input file is going to be placed at
    :type dst: string
    :param action: string containing what to do with the input
    :type action: string

    """
    if action == 'copy':
        log.debug("Copying.")
        shutil.copy(src, dst)
    elif action == 'move':
        log.debug("Moving.")
        shutil.move(src, dst)
    elif action == 'symlink':
        log.debug("Symlinking.")
        os.symlink(src, dst)
    elif action == 'hardlink':
        log.debug("Hardlinking.")
        os.link(src, dst)
    log.info("Done. ヾ(＠⌒ー⌒＠)ノ")


def exe_changes(src, dst, action, conflict):
    """Applies the changes that are expected depending on the action.

    :param src: subtitle to download.
    :type src: string
    :param dst: destination where the input file is going to be placed at
    :type dst: string
    :param action: string containing what to do with the input
    :type action: string
    """
    if action == 'test':
        log.debug("Test action:")
        log.info("TEST: %s ->  %s" % (src, dst))
    else:
        if os.path.exists(dst):
            log.debug("Destination exists.")
            if conflict == 'override':
                log.debug("Override ON.")
                exe_action(src, dst, action)
            elif conflict == 'auto':
                if os.stat(src).st_mtime > os.stat(dst).st_mtime:
                    log.debug("Override in auto mode, destination is older.")
                    exe_action(src, dst, action)
            else:
                log.error("FILE FOUND ON DESTINATION, OVERRIDE IS OFF")
                sys.exit()
        else:
            log.debug("Destination does not exist.")
            os.makedirs(os.path.dirname(dst))
            exe_action(src, dst, action)


def rename(set_argument, filename, media_info):
    """It replaces the "variables" set in:
    --set movieFormat (available: {n} {y} {fn} {ext})
    --set serieFormat (available: {n} {s} {e} {en} {fb} {ext})
    with those retrieved from TMDB and TVDB.

    :param set_argument: set argument parsed from main
    :type set_argument: string
    :param filename: name of the input file
    :type filename: string
    :param media_info: is the info retrieved from TMDB or TVDB
    :type media_info: dictionary

    """
    movieFormat = re.search('(?<=movieFormat=)"(.*?)"', set_argument).group(1)
    serieFormat = re.search('(?<=serieFormat=)"(.*?)"', set_argument).group(1)
    ext = filename[-3:]
    if 'episode' not in media_info:
        movieFormat = re.sub(
            r'{fn}', '%s' % os.path.basename(filename), movieFormat)
        movieFormat = re.sub(
            r'{n}', '%s' % media_info['title'], movieFormat)
        movieFormat = re.sub(
            r'{y}', '%s' % media_info['release_date'][0:4], movieFormat)
        movieFormat = re.sub(
            r'{ext}', '%s' % ext, movieFormat)
        return movieFormat
    else:
        serieFormat = re.sub(r'{fn}',
                             '%s' % os.path.basename(filename), serieFormat)
        serieFormat = re.sub(r'{n}',
                             '%s' % media_info['tvsname'], serieFormat)
        serieFormat = re.sub(r'{s}',
                             '%s' % media_info['season'], serieFormat)
        serieFormat = re.sub(r'{en}',
                             '%s' % media_info['episode'], serieFormat)
        serieFormat = re.sub(r'{e}',
                             '%s' % media_info['episodename'], serieFormat)
        serieFormat = re.sub(r'{ext}',
                             '%s' % ext, serieFormat)
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
            log.debug("Movie found: %s [%s bytes]" %
                      (os.path.basename(fpn), fpsize))
            movie_file = fpn
        else:
            log.debug("No movie found under: %s" % path)
            log.error("FILE BIGGER THAN 90% OF DIRECTORY'S SIZE NOT FOUND.")
            log.error("THE PROGRAM COULD NOT FIND ANY MOVIE FILE.")
            sys.exit()
    # If the input is a file, we guess it is the movie
    else:
        movie_file = path
        log.debug("The input was a movie.\n+ Movie found: %s [%s bytes]" %
                  (os.path.basename(movie_file), os.stat(movie_file).st_size))
    log.info("Input: %s" % os.path.basename(movie_file))
    return movie_file


def find_all_files(path, subtitles):
    """It will find all the video files, and if required the subtitles matching
    the video filename.
    """
    if os.path.isdir(path):
        log.debug("Walking through: %s" % path)
        videofiles = list()
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                guessing = guessit.guess_video_info(f)
                if guessing['container'] in extensions:
                    videofiles.append({'file': os.path.join(dirpath, f),
                                       'guess': guessing})
                    log.debug("Found: %s" % path)
        return videofiles
    else:
        log.debug("The input was a movie.\n+ Movie found: %s [%s bytes]" %
                  (os.path.basename(path), os.stat(path).st_size))
        log.info("Input: %s" % os.path.basename(path))
        return [path]


def parse_input():
    """Regular ArgumentParser"""
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
    parser.add_argument('-s', '--subtitle',
                        help='rename the subtitle found with the video file',
                        action='store_true')
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

    # Define logging verbosity
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    return args


def main():
    args = parse_input()
    log.info("INPUT: %s" % os.path.basename(args.PATH))

    media_files = find_all_files(args.PATH, True)  # True for subtitles, FIX
    for media_file in media_files:
        media_info = scraper.main(media_file)
    '''
    # Grab media info
    media_info = scraper.main(args.PATH)
    if 'episode' not in media_info:
        # Grab movie file and directory
        media_file = findfile(args.PATH)
        # Replace defined Format with real values
        dst = rename(args.set, media_file, media_info)
    elif 'episode' in media_info and not os.path.isdir(args.PATH):
        media_file = args.PATH
        # Replace defined Format with real values
        dst = rename(args.set, media_file, media_info)
    else:
        log.error("ERROR FINDING FILE.")

    # Update destination
    dst = os.path.join(args.output, dst)
    print(media_file)
    # Execute changes
    exe_changes(media_file, dst, args.action, args.conflict)
    '''


if __name__ == "__main__":
    main()
