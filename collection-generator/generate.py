#!/usr/bin/env python

from __future__ import print_function

from argparse import ArgumentParser
from os import makedirs as _makedirs
from os.path import abspath, dirname, join, splitext
import random
import shutil

import string
import unicodedata

from mutagen import easyid3

# goals:
# - generate a large collection from a template file

# generated collections should be deterministic
# - hypothesis: the number of items matters more for our performance testing
#   than the size of the files


validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def clean_filename(filename):
    if not isinstance(filename, unicode):
        filename = unicode(filename)
    cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
    return ''.join(c for c in cleanedFilename if c in validFilenameChars)

def makedirs(d):
    try:
        return _makedirs(d)
    except OSError:
        pass

class RandomContext(object):
    def __init__(self, rnd, minctx, maxctx):
        self.rnd = rnd
        self.minctx = minctx
        self.maxctx = maxctx
        
        self.idx = -1
        self.iters = -1
        
    def next(self):
        
        self.idx += 1
        
        if self.idx <= self.iters:
            return False
        else:
            self.idx = 1
            self.iters = self.rnd.randint(self.minctx, self.maxctx)
            return True

class CollectionGenerator(object):
    '''
        Generates a large collection of music files from a template
    '''
    
    # TODO: unicode and weird latin characters
    alphabet = string.digits + string.ascii_letters + string.punctuation
    alpha_len = len(alphabet) - 1
    
    albums_per_artist = (1, 10)
    songs_per_album = (1, 24)
    
    artistlen = (3, 16)
    albumlen = (3, 16)
    titlelen = (3, 16)
    
    def __init__(self, seed, outdir):
        self.idx = 0
        self.random = random.Random(seed)
        self.outdir = outdir
        
        self.artists = 0
        self.albums = 0
        self.titles = 0
    
    def generate(self, count, tmpl):
        
        ext = splitext(tmpl)[1]
        
        artist_ctx = RandomContext(self.random, *self.albums_per_artist)
        album_ctx = RandomContext(self.random, *self.songs_per_album)
    
        # collection structure
        #
        # root
        #     /artist
        #        /album
        #          /00 - songname.xx
        #
        
        artist = ''
        album = ''
        
        artist_dir = None
        album_dir = None
        
        for i in xrange(count):
            
            if album_ctx.next():
                self.albums += 1
                
                if artist_ctx.next():
                    self.artists += 1
                    artist = self._random_string(*self.artistlen)
                    artist_dir = join(self.outdir, clean_filename(artist))
                
                album = self._random_string(*self.albumlen)
                album_dir = join(artist_dir, clean_filename(album))
                makedirs(album_dir)
            
            title = self._random_string(*self.titlelen)
            fname = clean_filename('%d - %s%s' % (album_ctx.idx, title, ext))
            
            self.titles += 1
            dst = join(album_dir, fname)
            
            self._write_file(tmpl, dst, dict(
                artist=artist,
                album=album,
                title=title,
            ))
    
    def _random_string(self, minn, maxn):
        n = self.random.randint(minn, maxn)
        s = [self.alphabet[self.random.randint(0, self.alpha_len)] for _ in xrange(n)]
        return ''.join(s)
    
    def _write_file(self, tmpl, dst, attrs):
        shutil.copy(tmpl, dst)
        
        # TODO: other formats
        e = easyid3.EasyID3(dst)
        for k, v in attrs.items():
            e[k] = v


if __name__ == '__main__':
    
    # default template file
    def_tmpl = abspath(join(dirname(__file__), '..', 'click.mp3'))
    
    parser = ArgumentParser()
    parser.add_argument('-c', '--count', type=int, default=1000,
                        help='Number of files to generate')
    parser.add_argument('outdir',
                        help='Output directory')
    #parser.add_argument('-f', '--force', type=bool, default=False,
    #                    help='Overwrite files if they previously exist')
    parser.add_argument('--seed', type=int, default=None)
    
    args = parser.parse_args()
    
    gen = CollectionGenerator(args.seed, args.outdir)
    gen.generate(args.count, def_tmpl)
    
    print('Artists: %d\nAlbums: %d\nTracks: %d\n' % (gen.artists, gen.albums, gen.titles))
    