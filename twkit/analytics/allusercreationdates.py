#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Computes a distribution of account creation times for given users, saved
as CSV.
"""

import optparse
from progress.bar import Bar
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <user> [<user> ...]')
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is ids, not usernames")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state(use_cache=False, ignore_api=True)

  #todo: add an --all flag for this line
  #cursor = db.users.find({'screen_name_lower': {'$gt': ''}})
  cursor = (i.replace("@", "") for i in args)
  if options.ids:
    cursor = [int(i) for i in cursor]
  maxc = len(cursor)
  cursor = (lookup_user(db, i) for i in cursor)
  dates = defaultdict(lambda: Counter())
  for user in Bar("Users: ", max=maxc, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(cursor):
    if 'created_at' not in user: continue
    d = user['created_at'].date()
    dates[d][user['id']] = 1
  mindate = min(dates.keys())
  maxdate = max(dates.keys())
  d = mindate
  while d < maxdate:
    print("{},{}".format(d.isoformat(), len(dates[d])))
    d += timedelta(days=1)
