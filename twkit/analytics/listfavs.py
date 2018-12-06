#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
List all favoriters of the given user's tweets.
"""

import sys
import optparse
from twkit.utils import *
from twkit.analytics.stats import get_favoriters

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names.")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("--all", action="store_true", dest="all", default=False, help="Get favoriters of all tracked users.")
  parser.add_option("-l", "--list", action="store_true", dest="list", default=False, help="Simply list users.")
  parser.add_option("-c", "--common", action="store_true", dest="common", default=False, help="Find common users.")
  parser.add_option("-t", "--tweets", action="store_true", dest="tweets", default=False, help="List tweets faved by common.")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state(use_cache=False, ignore_api=True)

  if not (options.list or options.common or options.tweets):
    print "use at least one of -l -c -t"
    sys.exit(1)

  if options.all:
    userlist = set(u['id'] for u in db.following.find())
    userlist = userlist | set(u['id'] for u in db.greeks.find())
    options.ids = True
  else:
    userlist = [x.lower().replace("@", "") for x in args]
  peruser = {}
  for user in userlist:
    uname = None if options.ids else user
    uid = long(user) if options.ids else None
    u = lookup_user(db, uid, uname)
    if u is None:
      if verbose(): sys.stderr.write(u'Unknown user {}\n'.format(user))
      continue
    uid = u['id']
    userstr = id_to_userstr(db, uid)
    if verbose(): sys.stderr.write(u'Fav graph for user {}/{}\n'.format(uid, userstr))
    favoriters = get_favoriters(db, uid)
    if options.list:
      for faver, cnt in favoriters.iteritems():
        if options.ids:
          print u'{} {} {}'.format(faver, uid, len(cnt))
        else:
          print u'{} {} {}'.format(id_to_userstr(db, faver), userstr, len(cnt))
    peruser[uid] = favoriters
  if options.common:
    common = None
    for uid in peruser:
      if common is None:
        common = set(peruser[uid].keys())
      else:
        common = common & set(peruser[uid].keys())
    for uid in common:
      if verbose():
        print id_to_userstr(db, uid)
      else:
        print uid
    if options.tweets:
      for fid in common:
        print u'{} has favorited:'.format(id_to_userstr(db, fid))
        for uid in peruser:
          uname = id_to_userstr(db, uid)
          for twid in peruser[uid][fid]:
            tw = db.tweets.find_one({'id': twid})
            print u'Tweet {} by {}: {}'.format(twid, uname, tw.get('text')).encode('utf-8')
            print u'--'




