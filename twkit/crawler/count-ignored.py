#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Count how many tweets are in the DB per ignored user.
"""

import sys
from twkit.utils import *

if __name__ == "__main__":
  db, _ = init_state(use_cache=False, ignore_api=True)
  cursor = db.tweets.aggregate([
    {'$group': {'_id': '$user.id', 'count': {'$sum': 1}}}
  ], allowDiskUse=True)
  for c in cursor:
    whoid = c['_id']
    cnt = c['count']
    if not is_ignored(db, whoid): continue
    if is_protected(db, whoid):
      print whoid, "is both protected and ignored"
    u = lookup_user(db, whoid)
    print cnt, id_to_userstr(db, whoid), whoid
    sys.stdout.flush()

  #for u in db.following.find():
  #  name = u['screen_name_lower']
  #  cursor = tweets.aggregate([
  #    {'$match': {'user.id' : u['id']}},
  #    {'$group': {'_id': '$user.id', 'count': {'$sum': 1}}}
  #  ])
  #  for c in cursor:
  #    cnt = c['count']
  #    print cnt, name
