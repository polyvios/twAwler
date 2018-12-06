#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Find reply-threads or quote-threads and print their length.
"""

import optparse
from twkit.utils import *
from progress.bar import Bar

def explore_thread(db, twid, depth=0):
  found = False
  for tw in db.tweets.find({'in_reply_to_status_id': twid}):
    found = True
    explore_thread(db, tw['id'], depth+1)
    print "{} {}".format(tw['id'], twid)
  #if not found:
    #if depth: print u"tweet {} at depth {}".format(twid, depth)

def explore_quote_thread(db, twid, depth=0):
  found = False
  for tw in db.tweets.find({'quoted_status_id': twid}):
    found = True
    explore_quote_thread(db, tw['id'], depth+1)
    print "{} {}".format(tw['id'], twid)
  #if not found:
    #if depth: print u"tweet {} at depth {}".format(twid, depth)

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is ids, not usernames")
  parser.add_option("--tweet", action="store_true", dest="tweet", default=False, help="Input is tweet id.")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="make noise.")
  parser.add_option("--greeks", action="store_true", dest="greeks", default=False, help="Consider all Greeks.")
  parser.add_option("--quotes", action="store_true", dest="quotes", default=False, help="Consider quotes, not replies.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, _ = init_state(use_cache=False, ignore_api=True)
  userlist = [x.lower().replace("@", "") for x in args]
  sys.setrecursionlimit(10000000)

  if options.greeks:
    options.ids = True
    userlist = [x['id'] for x in db.greeks.find()]

  if verbose():
    userlist = Bar("Loading:", max=db.greeks.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(userlist)
    
  for user in userlist:
    if options.tweet:
      if options.quotes:
        explore_quote_thread(db, long(user))
      else:
        explore_thread(db, long(user))
      continue
    uid = long(user) if options.ids else None
    uname = None if options.ids else user
    u = lookup_user(db, uid, uname)

    for tw in db.tweets.find({'user.id': u['id']}).batch_size(10):
      if 'text' not in tw: continue
      if options.quotes:
        explore_quote_thread(db, tw['id'])
      else:
        explore_thread(db, tw['id'])
