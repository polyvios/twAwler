#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Computes a distribution of account creation times for all users, saved
as CSV.
"""

import optparse
from progress.bar import Bar
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from twkit.utils import *

if __name__ == '__main__':
  db, api = init_state(use_cache=False, ignore_api=True)
  cursor = db.users.find({'screen_name_lower': {'$gt': ''}})
  dates = defaultdict(lambda: Counter())
  for user in Bar("Users: ", max=cursor.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(cursor):
    if 'created_at' not in user: continue
    d = user['created_at'].date()
    dates[d][user['id']] = 1
  mindate = min(dates.keys())
  maxdate = max(dates.keys())
  d = mindate
  while d < maxdate:
    print d.isoformat(), len(dates[d])
    d += timedelta(days=1)
