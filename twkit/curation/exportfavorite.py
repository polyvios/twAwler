#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import sys
import optparse
from collections import Counter, defaultdict
from progress.bar import Bar
from twkit.utils import *
import dateutil.parser

def scan_by_tweets(db, tweets):
  edgecnt = defaultdict(lambda: Counter())
  edges = ((x['user_id'], t['user']['id']) for t in tweets for x in db.favorites.find({'tweet_id': t['id']}, {'user_id':1, 'tweet_id':1}))
  if verbose():
    edges = Bar("Processing:", max=(len(tweets)*2), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(edges)
  for u1,u2 in edges:
    edgecnt[u1][u2] += 1
  return edgecnt
 
if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek")
  parser.add_option("-o", "--output", action="store", dest="filename", default='favorites.txt', help="Output file")
  parser.add_option("-b", "--before", action="store", dest="before", default=False, help="Before given date.")
  parser.add_option("-a", "--after", action="store", dest="after", default=False, help="After given date.")
  parser.add_option("-u", "--user", action="store_true", dest="user", default=False, help="Only scan given users -currently incompatible with before/after.")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names.")
  parser.add_option("--dot", action="store_true", dest="dot", default=False, help="Save in dot format.")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, _ = init_state(use_cache=False, ignore_api=True)

  criteria = {}
  if options.before:
    criteria['$lte'] = dateutil.parser.parse(options.before)
  if options.after:
    criteria['$gt'] = dateutil.parser.parse(options.after)

  #edges = db.favorites.find({}, {'user_id':1, 'tweet_id':1}).sort('user_id', 1).batch_size(10)
  if options.before or options.after:
    tweets = db.tweets.find({'created_at': criteria}, {'id': 1, 'user.id': 1})
    if verbose:
      tweets = Bar("Loading:", max=tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
    tweets = list(tweets)
    edgecnt = scan_by_tweets(db, tweets)
    save_edgelist(db, edgecnt, options.filename, weight=True)
  elif options.user: 
    uid = int(options.user) if options.ids else lookup_user(db, uname=options.user).get('id', -1)
    tweets = db.tweets.find({'user.id': uid}, {'id': 1, 'user.id': 1})
    tweets = list(tweets)
    edgecnt = scan_by_tweets(db, tweets)
    if options.dot:
      save_dot(db, edgecnt, options.filename, weight=True)
    else:
      save_edgelist(db, edgecnt, options.filename, weight=True)
  else:
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
              print("Done with {}, saving edges".format(id_to_userstr(db, trackeduser)))
            greeku = is_greek(db, trackeduser) or (get_tracked(db, trackeduser) is not None)
            for u, c in usercnt.items():
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
          print("done with {}, saving edges".format(id_to_userstr(db, trackeduser)))
        greeku = is_greek(db, trackeduser) or (get_tracked(db, trackeduser) is not None)
        for u, c in usercnt.items():
          if options.greek and not greeku and not is_greek(db, u) and get_tracked(db, u) is None: continue
          outf.write('{} {} {}\n'.format(trackeduser, u, c))

