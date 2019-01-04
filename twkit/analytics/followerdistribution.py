#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Compute the distribution of creation dates for all followers of a
given user (this has been used in newspaper articles referring to
bought followings).
"""

import sys
import twitter
import optparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from twkit.utils import *


def creation_distribution(db, userids):
  creationdates = Counter() #defaultdict(Counter)
  for fid in userids:
    f = lookup_user(db, fid)
    if f is None or 'created_at' not in f: continue
    d = f['created_at'].replace(hour=0, minute=0, second=0, microsecond=0)
    creationdates[d] += 1
  return creationdates


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names.")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("--followers", action="store_true", dest="followers", default=False, help="Scan the followers of the given users instead.")
  parser.add_option("--common", action="store_true", dest="common", default=False, help="Scan the followers of the given users and print the common to all.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  db, api = init_state(False, ignore_api=True)
  userlist = [x.lower().replace("@", "") for x in args]
  creationdates = Counter()
  commonusers = None

  if options.followers:
    for user in userlist:
      uname = None if options.ids else user
      uid = long(user) if options.ids else None
      u = lookup_user(db, uid, uname)
      if verbose(): sys.stderr.write("{} followers\n".format(u['screen_name_lower']))
      userids = set(get_followers(db, u['id']))
      if options.common:
        if commonusers:
          commonusers = commonusers & userids
        else:
          commonusers = userids
      else:
        creationdates += creation_distribution(db, userids)
  else:
    users = [lookup_user(db, long(user) if options.ids else None, None if options.ids else user) for user in userlist]
    userids = [u['id'] for u in users if u is not None and 'id' in u]
    #print userids
    creationdates = creation_distribution(db, userids)

  if options.common:
    for uid in commonusers:
      print uid
  else:
    print u'Date,Count'
    d = min(creationdates)
    end = max(creationdates)
    while d < end:
      cnt = creationdates[d]
      print u'{},'.format(d.date()),
      print u'{}'.format(cnt)
      d += timedelta(days=1)
