#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import sys
import optparse
from twkit.utils import *

"""
Remove the user from the tracked user set and add them to the ignored
set.
"""

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is ids, not usernames")
  (options, args) = parser.parse_args()

  db, api = init_state()
  userlist = [x.lower().replace("@", "") for x in args]
  for user in userlist:
    uid = int(user) if options.ids else None
    uname = None if options.ids else user
    u = get_tracked(db, uid=uid, uname=uname)
    if u:
      db.following.delete_one(u)
      db.greeks.delete_one({'id': u['id']})
      db.frequences.delete_one({'id': u['id']})
      ignore_user(db, u['id'])
      print("stopped following, ignoring", u)
    else:
      u = lookup_user(db, uid, uname)
      print("user not tracked, ignoring anyway", uid, uname, u['screen_name'])
      ignore_user(db, u['id'])
