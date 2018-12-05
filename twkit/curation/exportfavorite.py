#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import sys
import optparse
from collections import Counter
from progress.bar import Bar
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek")
  parser.add_option("-o", "--output", action="store", dest="filename", default='favorites.txt', help="Output file")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, _ = init_state(use_cache=True, ignore_api=True)

  num = db.favorites.count()
  edges = db.favorites.find({}, {'user_id':1, 'tweet_id':1}).sort('user_id', 1).batch_size(10)
  if verbose():
    edges = Bar("Processing:", max=num, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(edges)

  with open(options.filename, "w") as outf:
    trackeduser = 0
    usercnt = Counter()
    for e in edges:
      src = e['user_id']
      if src != trackeduser:
        if trackeduser != 0:
          if verbose():
            print "Done with {}, saving edges".format(id_to_userstr(db, trackeduser))
          greeku = is_greek(db, trackeduser) or (get_tracked(db, trackeduser) is not None)
          for u, c in usercnt.iteritems():
            if options.greek and not greeku and not is_greek(db, u) and get_tracked(db, u) is None: continue
            outf.write('{} {} {}\n'.format(trackeduser, u, c))
        usercnt.clear()
        trackeduser = src
      # count fav normally
      twid = e['tweet_id']
      tw = db.tweets.find_one({'id': twid}, {'user.id': 1})
      if tw is None: continue
      if 'user' not in tw: continue
      dst = tw['user']['id']
      usercnt[dst] += 1
    if trackeduser != 0:
      if verbose():
        print "done with {}, saving edges".format(id_to_userstr(db, trackeduser))
      greeku = is_greek(db, trackeduser) or (get_tracked(db, trackeduser) is not None)
      for u, c in usercnt.iteritems():
        if options.greek and not greeku and not is_greek(db, u) and get_tracked(db, u) is None: continue
        outf.write('{} {} {}\n'.format(trackeduser, u, c))

