#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
  run this file to create mention.txt graph (with weights)
  exportmention.py -v > me.out.txt

  the script generates mention.txt with "src dst w" mention lists
  "src dst w" means user #src mentioned #dst #w times, without it
  being a direct reply

  to fill in unknowns for next time then run
  cat me.out.txt |grep unknown | cut -f 2 -d\( | cut -f 1 -d\)| xargs bin/addid.py -v

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
  parser.add_option("-o", "--output", action="store", dest="filename", default='mention.txt', help="Output file")
  parser.add_option("-b", "--before", action="store", dest="before", default=False, help="Before given date.")
  parser.add_option("-a", "--after", action="store", dest="after", default=False, help="After given date.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, _ = init_state(use_cache=True, ignore_api=True)

  criteria = {}
  if options.before:
    criteria['$lte'] = dateutil.parser.parse(options.before)
  if options.after:
    criteria['$gt'] = dateutil.parser.parse(options.after)

  if verbose(): sys.stderr.write("initialize mention scan\n")
  sys.stderr.flush()
  #tweets = db.tweets.find({'user_mentions.id': {'$gt': 1}}, {'user.id': 1, 'in_reply_to_user_id': 1, 'user_mentions': 1}).sort('user.id', 1)
  if options.before or options.after:
    tweets = db.tweets.find(
      {'created_at': criteria},
      {'user_mentions':1, 'user.id': 1, 'id': 1}
    ).sort('user.id', 1)
  else:
    tweets = db.tweets.find(
      {},
      {'user_mentions':1, 'user.id': 1, 'id': 1}
    ).sort('user.id', 1)
  sys.stderr.write("counting\n")
  sys.stderr.flush()
  num = db.tweets.count()
  if verbose():
    sys.stderr.write("about to scan {} total tweets for mentions\n".format(num))
    sys.stderr.flush()
    tweets = Bar("Processing:", max=num, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  with open(options.filename, "w") as outf:
    trackeduser = 0
    usercnt = Counter()
    for t in tweets:
      # for every matching tweet, count that tweet.user.id mentioned all tweet.user_mentions.[id]
      if 'user_mentions' not in t: continue
      orig = t['user']['id']
      if orig != trackeduser:
        if trackeduser != 0:
          if verbose():
            print "done with {}, saving edges".format(id_to_userstr(db, trackeduser))
          greeku = is_greek(db, trackeduser) or (get_tracked(db, trackeduser) is not None)
          for u, c in usercnt.iteritems():
            if options.greek and not is_greek(db, u) and not greeku and get_tracked(db, u) is None: continue
            outf.write('{} {} {}\n'.format(trackeduser, u, c))
        usercnt.clear()
        trackeduser = orig
      for mentioned in t['user_mentions']:
        mentioned = mentioned['id']
        if mentioned == t.get('in_reply_to_user_id', 0): continue
        usercnt[mentioned] += 1
    if trackeduser != 0:
      if verbose():
        print "done with {}, saving edges".format(id_to_userstr(db, trackeduser))
      greeku = is_greek(db, trackeduser) or (get_tracked(db, trackeduser) is not None)
      for u, c in usercnt.iteritems():
        if options.greek and not is_greek(db, u) and not greeku and get_tracked(db, u) is None: continue
        outf.write('{} {} {}\n'.format(trackeduser, u, c))

