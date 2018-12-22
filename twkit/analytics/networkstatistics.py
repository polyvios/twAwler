#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
compute statistics for the network formed by a given set of users
"""

import sys
import optparse
from datetime import datetime,timedelta
from twkit.utils import *
from collections import Counter, defaultdict
from progress.bar import Bar
import unicodecsv
import mmap
from igraph import *

## This function from https://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python
def mapcount(filename):
  f = open(filename, "r+")
  buf = mmap.mmap(f.fileno(), 0)
  lines = 0
  readline = buf.readline
  while readline():
    lines += 1
  return lines

def rawcount(filename):
  f = open(filename, 'rb')
  lines = 0
  buf_size = 1024 * 1024
  read_f = f.raw.read

  buf = read_f(buf_size)
  while buf:
      lines += buf.count(b'\n')
      buf = read_f(buf_size)

  return lines


graph = {}
if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek")
  (options, args) = parser.parse_args()
  db, api = init_state(False, False)
  verbose(options.verbose)

  if len(args) == 0:
    print "please give file of edges"

  #edges = set()
  #nodes = set()
  #weights = defaultdict(lambda:0)
  #print "count input"
  #lines = mapcount(args[0])
  #print "{} lines".format(lines)

  twitter_igraph = Graph.Read_Ncol(args[0], directed=True)

  print "loaded"
  print "density:"
  print (twitter_igraph.density())
  print "recirpocity:"
  print (twitter_igraph.reciprocity())
  #print "summary:"
  #print (twitter_igraph.summary())
  print "assortativity:"
  print (twitter_igraph.assortativity_degree())
  print "transitivity:"
  print (twitter_igraph.transitivity_undirected())

  print "radius:"
  print (twitter_igraph.radius())
  print "girth:"
  print (twitter_igraph.girth())
  print "diameter:"
  print (twitter_igraph.diameter())
  #print (twitter_igraph.alpha())
  #print (twitter_igraph.omega())
