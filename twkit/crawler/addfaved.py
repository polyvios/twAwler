#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Scan a given user's last 200 favorite tweets and add all their authors
to be crawled.
"""

import sys
import optparse
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <user> [<user> ...]')
  parser.add_option("--refollow", action="store_true", dest="refollow", default=False, help="Re-follow ignored users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is ids, not usernames")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  (options, args) = parser.parse_args()

  if len(args) == 0:
    parser.print_help()
    sys.exit(1)

  verbose(options.verbose)
  db, api = init_state()
  userlist = [x.lower().replace("@", "") for x in args]

  for user in userlist:
    uid = long(user) if options.ids else None
    username = None if options.ids else user
    for tw in api.GetFavorites(user_id=uid, screen_name=username, count=200):
      j = pack_tweet(db, tw)
      try:
        db.tweets.insert_one(j)
      except:
        pass
      userid = tw.user.id
      follow_user(db, api, userid)

