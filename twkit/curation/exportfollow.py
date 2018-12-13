#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Create a file (default follow.txt) with all follow edges, encoded as
<Src-Id Dest-Id> pairs.
"""

import sys
import optparse
from progress.bar import Bar
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek")
  parser.add_option("-o", "--output", action="store", dest="filename", default='follow.txt', help="Output file")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, _ = init_state(use_cache=True, ignore_api=True)

  num = db.follow.count()
  edges = db.follow.find({}, {'id':1, 'follows':1}).sort('id', 1)
  if verbose():
    edges = Bar("Processing:", max=num, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(edges)
  outf = open(options.filename, "w")
  for e in edges:
    src = e['id']
    dst = e['follows']
    if options.greek and not is_greek(db, src) and not is_greek(db, dst) and get_tracked(db, src) is None and get_tracked(db, dst) is None: continue
    outf.write('{} {}\n'.format(src, dst))

