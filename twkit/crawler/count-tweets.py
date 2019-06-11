#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Count how many tweets are in the DB per followed user.
"""

import optparse
from datetime import datetime
from twkit.utils import *

if __name__ == "__main__":
  start_time = datetime.utcnow()
  parser = optparse.OptionParser()
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  parser.add_option('-a', '--all', action='store_true', dest='all', default=False, help='List all.')
  (options, args) = parser.parse_args()

  db, _ = init_state(use_cache=False, ignore_api=True)
  cursor = db.tweets.aggregate(
    [{ '$group':
      { '_id': '$user.id',
        'count': {'$sum': 1}
      }
    }],
    allowDiskUse=True
  )
  for c in cursor:
    whoid = c['_id']
    cnt = c['count']
    if whoid is None: continue
    if options.all:
      u = lookup_user(db, whoid)
      if u is None:
        u = {}
    else:
      u = get_tracked(db, whoid)
      if u is None: continue 
    print cnt, u.get('screen_name_lower','<unknown>'), u.get('id', whoid), u.get('statuses_count')

  update_crawlertimes(db, "tweets", start_time)
