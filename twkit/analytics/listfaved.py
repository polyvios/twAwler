#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
List all users favorited by the given user.
"""

import sys
import optparse
from collections import Counter
from twkit.utils import *
from twkit.analytics.stats import get_user_tweets, get_favorited

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names.")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("-l", "--list", action="store_true", dest="list", default=False, help="Simply list users.")
  parser.add_option("-c", "--common", action="store_true", dest="common", default=False, help="Find common users.")
  parser.add_option("-t", "--tweets", action="store_true", dest="tweets", default=False, help="List tweets faved by all given users.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  db, api = init_state(use_cache=False, ignore_api=True)

  #if not (options.list or options.common or options.tweets):
    #print("use at least one of -l -c -t")
    #sys.exit(1)

  userlist = [x.lower().replace("@", "") for x in args]
  peruser = {}
  perfaved = Counter()
  for user in userlist:
    uname = None if options.ids else user
    uid = int(user) if options.ids else None
    u = lookup_user(db, uid, uname)
    if u is None:
      if verbose(): sys.stderr.write(u'Unknown user {}\n'.format(user))
      continue
    uid = u['id']
    userstr = id_to_userstr(db, uid)
    if verbose(): sys.stderr.write(u'Faved by user {}/{}\n'.format(uid, userstr))
    favorited = get_favorited(db, uid)
    peruser[uid] = favorited
    perfaved += Counter({x:len(c) for x,c in favorited.items()})
    if options.list:
      for faved, cnt in favorited.items():
        if options.ids:
          print(u'{} {} {}'.format(uid, faved, len(cnt)))
        else:
          print(u'{} {} {}'.format(userstr, id_to_userstr(db, faved), len(cnt)))
        if options.tweets:
          for t in cnt:
            tw = db.tweets.find_one({'id':t})
            print(u'{}: {}: {}'.format(tw['id'], id_to_userstr(db, faved), tw.get('text', '<deleted>')))
  if options.common:
    common = None
    for uid in peruser:
      if common is None:
        common = set(peruser[uid].keys())
      else:
        common = common & set(peruser[uid].keys())
    for uid in common:
      if verbose():
        print(id_to_userstr(db, uid))
      else:
        print(uid)
    if options.tweets:
      for fid in common:
        print(u'{} favorited by:'.format(id_to_userstr(db, fid)))
        for uid in peruser:
          uname = id_to_userstr(db, uid)
          for twid in peruser[uid][fid]:
            tw = db.tweets.find_one({'id': twid})
            print(u'Tweet {} by {}: {}'.format(twid, uname, tw.get('text')))
            print(u'--')
        print(u'======')
  if not (options.list or options.common or options.tweets):
    for uid, cnt in perfaved.items():
      print(u'{} {}'.format(uid, cnt))


