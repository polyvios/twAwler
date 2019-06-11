#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Create a file (default follow.txt) with all follow edges, encoded as
<Src-Id Dest-Id> pairs.
"""

import sys
import optparse
import dateutil.parser
from progress.bar import Bar
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek")
  parser.add_option("-o", "--output", action="store", dest="filename", default='follow.txt', help="Output file")
  parser.add_option("-b", "--before", action="store", dest="before", default=False, help="Before given date.")
  parser.add_option("-a", "--after", action="store", dest="after", default=False, help="After given date.")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, _ = init_state(use_cache=False, ignore_api=True)

  criteria = {}
  if options.before:
    criteria['$lte'] = dateutil.parser.parse(options.before)
  if options.after:
    criteria['$gt'] = dateutil.parser.parse(options.after)

  num = db.follow.count()
  if options.before or options.after:
    edges = db.follow.find({'date': criteria}, {'id':1, 'date':1, 'follows': 1})
    #edges = db.follow.aggregate([ { '$sort': { 'id' : 1} }, { '$match' : { 'date' : criteria } } ], hint='id_1_date_1_follows_1')
  else:
    edges = db.follow.find({}, {'id':1, 'follows':1}).sort('id', 1)
  if verbose():
    edges = Bar("Processing:", max=num, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(edges)
  outf = open(options.filename, "w")
  for e in edges:
    src = e['id']
    dst = e['follows']
    if options.greek and not is_greek(db, src) and not is_greek(db, dst) and get_tracked(db, src) is None and get_tracked(db, dst) is None: continue
    outf.write('{} {}\n'.format(src, dst))

