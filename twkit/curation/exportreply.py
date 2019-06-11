#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
  run this file to create reply.txt graph (with weights)
  exportreply.py -v > re.out.txt

  the script generates reply.txt with "src dst w" mention lists
  "src dst w" means user #src directly replied to user #dst #w times

  to fill in unknowns for next time then run
  cat re.out.txt |grep unknown | cut -f 2 -d\( | cut -f 1 -d\)| xargs bin/addid.py -v

  to process the graph, use visualization/graphfigures.py
'''

import sys
import optparse
import dateutil.parser
from datetime import datetime
from collections import Counter
from progress.bar import Bar
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek")
  parser.add_option("-o", "--output", action="store", dest="filename", default='reply.txt', help="Output file")
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

  if verbose():
    sys.stderr.write("initialize reply scan\n")
    sys.stderr.flush()
  if options.before or options.after:
    tweets = db.tweets.find({'in_reply_to_user_id': {'$gt': 1}, 'created_at': criteria}, {'in_reply_to_user_id':1, 'user': 1}).sort('in_reply_to_user_id', 1)
  else:
    tweets = db.tweets.find({'in_reply_to_user_id': {'$gt': 1}}, {'in_reply_to_user_id':1, 'user': 1}).sort('in_reply_to_user_id', 1)
  num = db.tweets.count()
  if verbose():
    sys.stderr.write("starting scan\n")
    sys.stderr.flush()
    tweets = Bar("Processing:", max=num, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  with open(options.filename, "w") as outf:
    trackeduser = 0
    usercnt = Counter()
    for t in tweets:
      orig = t['in_reply_to_user_id']
      answer = t['user']['id']
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
      usercnt[answer] += 1
    if trackeduser != 0:
      if verbose():
        print "done with {}, saving edges".format(id_to_userstr(db, trackeduser))
      greeku = is_greek(db, trackeduser) or (get_tracked(db, trackeduser) is not None)
      for u, c in usercnt.iteritems():
        if options.greek and not is_greek(db, u) and not greeku and get_tracked(db, u) is None: continue
        outf.write('{} {} {}\n'.format(u, trackeduser, c))
 
