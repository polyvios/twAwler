#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Checks if protected users are still protected.
Use flag --suspended to check if suspended users are still suspended, instead.
"""

import optparse
from progress.bar import Bar
from datetime import datetime, timedelta
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("--suspended", action="store_true", dest="suspended", default=False, help="Check suspended users instead")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  db, api = init_state()
  if options.suspended:
    userlist = db.suspended.find()
  else:
    userlist = db.protected.find()
  if verbose():
    userlist = Bar("Loading:", max=userlist.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(userlist)
  for user in userlist:
    uid = long(user['id'])
    if not options.suspended and is_protected(db, uid): continue
    if options.suspended and is_suspended(db, uid): continue
    follow_user(db, api, uid=uid, wait=True, refollow=True)
