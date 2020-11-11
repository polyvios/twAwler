#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Checks if protected users are still protected.
Use flag --suspended to check if suspended users are still suspended, instead.
"""

import optparse
import time
from progress.bar import Bar
from datetime import datetime, timedelta
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("--suspended", action="store_true", dest="suspended", default=False, help="Check suspended users instead")
  parser.add_option("--stopafter", action="store", type="int", dest="stopafter", default=None, help="Scan the given number of users")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  db, api = init_state()
  if options.suspended:
    userlist = db.suspended.find()
  else:
    userlist = db.protected.find()

  if options.stopafter:
    current = 0

  if verbose():
    userlist = Bar("Loading:", max=userlist.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(userlist)

  api.InitializeRateLimit()
  resource = u'/users/show/:id'

  for user in userlist:
    uid = int(user['id'])
    if not options.suspended and is_protected(db, uid): continue
    if options.suspended and is_suspended(db, uid): continue
    l = api.rate_limit.get_limit(resource)
    if l.remaining < l.limit:
      left = l.reset - timegm(gmtime())
      sec = left - l.remaining
      if l.remaining > 5 and sec > 2 and left > l.remaining:
        print("sleeping {} secs".format(sec))
        time.sleep(sec)
    follow_user(db, api, uid=uid, wait=True, refollow=True)
    if options.stopafter:
      current += 1
      if current == options.stopafter: break
