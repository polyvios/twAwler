#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Mark the given user as being a greek-speaker.
"""

import sys
import optparse
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is id, not username.")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state()

  if len(args) == 0:
    parser.print_help()
    sys.exit(1)

  userlist = [x.lower().replace("@", "") for x in args]
  for user in userlist:
    uid = long(user) if options.ids else None
    uname = None if options.ids else user
    u = get_tracked(db, uid, uname)
    if u is None:
      if verbose(): print "User not tracked, still marking",
      u = lookup_user(db, uid, uname)
    if u is None:
      print "Unknown user {} {} first add user for tracking".format(uid, uname)
      continue
    if is_greek(db, u['id']):
      if verbose(): print "{} already marked".format(user)
    elif is_ignored(db, u['id']):
      if verbose(): print "{} ignored".format(user)
    else:
      db.greeks.insert_one({'id': u['id']})
      for us in db.users.find({'id': u['id'], 'screen_name_lower': {'$gt': ''}}):
        db.greeks.update_one(
          {'id': u['id']},
          {'$set':{'id': u['id'], 'screen_name': us['screen_name_lower']}})
        print us['screen_name_lower'], "added to greek set"

