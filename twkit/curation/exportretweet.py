#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
  run this file to create retweet.txt graph (with weights)
  exportmention.py -v > re.out.txt

  the script generates retweet.txt with "src dst w" edge list
  "src dst w" means user #src retweeted user #dst #w times

  to fill in unknowns for next time then run
  cat re.out.txt |grep unknown | cut -f 2 -d\( | cut -f 1 -d\)| xargs bin/addid.py -v

  to process the graph: use visualization/graphfigures.py
'''


import sys
import optparse
from collections import Counter
from progress.bar import Bar
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek")
  parser.add_option("-o", "--output", action="store", dest="filename", default='retweet.txt', help="Output file")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, _ = init_state(use_cache=True, ignore_api=True)

  print "initialize"
  num = db.tweets.count()
  print "about to scan {} total tweets for RTs".format(num)
  tweets = db.tweets.find({'retweeted_status.user.id': {'$gt': 1}}, {'retweeted_status.user.id':1, 'user.id':1}).sort('retweeted_status.user.id', 1)
  if verbose():
    print "starting scan"
    tweets = Bar("Processing:", max=num, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  with open(options.filename, "w") as outf:
    trackeduser = 0
    usercnt = Counter()
    for t in tweets:
      orig = t['retweeted_status']['user']['id']
      rter = t['user']['id']
      if orig != trackeduser:
        if trackeduser != 0:
          if verbose():
            print "done with {}, saving edges".format(id_to_userstr(db, trackeduser))
          greeku = is_greek(db, trackeduser) or (get_tracked(db, trackeduser) is not None)
          for u, c in usercnt.iteritems():
            if options.greek and not is_greek(db, u) and not greeku and get_tracked(db, u) is None: continue
            outf.write('{} {} {}\n'.format(u, trackeduser, c))
        usercnt.clear()
        trackeduser = orig
      usercnt[rter] += 1
    if trackeduser != 0:
      if verbose():
        print "done with {}, saving edges".format(id_to_userstr(db, trackeduser))
      greeku = is_greek(db, trackeduser) or (get_tracked(db, trackeduser) is not None)
      for u, c in usercnt.iteritems():
        if options.greek and not is_greek(db, u) and not greeku and get_tracked(db, u) is None: continue
        outf.write('{} {} {}\n'.format(u, trackeduser, c))
 
