#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Adds a user to the set of tracked users.
"""

import sys
import optparse
from twkit.utils import *
from twkit.crawler.fillfollow import add100_id

if __name__ == "__main__":
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <user> [<user> ...]')
  parser.add_option("--refollow", action="store_true", dest="refollow", default=False, help="Re-follow ignored users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is ids, not usernames")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  (options, args) = parser.parse_args()

  if len(args) == 0:
    parser.print_help()
    sys.exit(1)

  verbose(options.verbose)
  db, api = init_state(use_cache=False)
  userlist = [x.lower().replace("@", "") for x in args]

  if options.ids and len(args) > 100:
    idlist = []
    for idstr in args:
      userid = long(idstr)
      if not can_follow(db, userid, options.refollow): continue
      idlist.append(userid)
      if len(idlist) > 99:
        addedlist = add100_id(db, api, idlist)
        idlist = []
        for u in addedlist:
          add_to_followed(db, u['id'], u['screen_name_lower'], u.get('protected', False))
    if len(idlist):
      addedlist = add100_id(db, api, idlist)
      for u in addedlist:
        add_to_followed(db, u['id'], u['screen_name_lower'], u.get('protected', False))

  else:
    for user in userlist:
      if options.ids:
        follow_user(db, api, uid=long(user), wait=True, refollow=options.refollow)
      else:
        follow_user(db, api, uname=user, wait=True, refollow=options.refollow)
