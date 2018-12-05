#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import re
import sys
import optparse
from progress.bar import Bar
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek")
  parser.add_option("-o", "--output", action="store", dest="filename", default='avatars.txt', help="Output file")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, _ = init_state(use_cache=True, ignore_api=True)

  num = db.images.count()
  edges = db.images.find({}).sort('screen_name', 1)
  if verbose():
    edges = Bar("Processing:", max=num, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(edges)
  outf = open(options.filename, "w")
  edgecnt = set()
  lastuser = ''
  lastimage = ''
  for e in edges:
    src = e['screen_name']
    dst = e['image']
    if src == lastuser and dst == lastimage: continue
    if src != lastuser:
      for im in edgecnt:
        outf.write('{} {}\n'.format(lastuser, im))
      edgecnt = set()
      srcu = lookup_user(db, uname=src)
      if srcu is None:
        #nameregex = re.compile(r'^{}$'.format(src.lower()), re.IGNORECASE)
        for x in db.users.find({'screen_name': src}).collation({'locale': 'en', 'strength': 1}).limit(1):
          srcu = x
        if srcu is None:
          print "Unknown user:", src
    lastuser = src
    lastimage = dst
    if options.greek and srcu and not is_greek(db, srcu['id']) and get_tracked(db, srcu['id']) is None: continue
    edgecnt.add(dst)
