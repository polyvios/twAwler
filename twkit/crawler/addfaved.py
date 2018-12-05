#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
Scan a given user's last 200 favorite tweets and add all their authors
to be crawled.
'''

import sys
import optparse
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--refollow", action="store_true", dest="refollow", default=False, help="Re-follow ignored users")
  (options, args) = parser.parse_args()
  if len(args) < 1:
    parser.print_help()
    sys.exit(1)
  db, api = init_state()
  userlist = [x.lower().replace("@", "") for x in args]
  for username in userlist:
    for tw in api.GetFavorites(screen_name=username, count=200):
      j = pack_tweet(db, tw)
      try:
        db.tweets.insert_one(j)
      except:
        pass
      userid = tw.user.id
      follow_user(db, api, userid)

