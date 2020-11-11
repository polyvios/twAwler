#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Command-line tool that scans the user data collection for duplicates.
Will ignore timestamp, number of posted tweets and favorites, so that
it avoids keeping full user objects for these counters.
"""

import optparse
from progress.bar import Bar
from datetime import datetime,timedelta
from twkit.utils import *

if __name__ == '__main__':
  db, api = init_state()
  cursor = db.users.find({'screen_name_lower': {'$gt': ''}})
  for user in Bar("Users: ", max=cursor.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(cursor):
    del user['_id']
    if 'timestamp_at' in user: del user['timestamp_at']
    if 'statuses_count' in user: del user['statuses_count']
    if 'favourites_count' in user: del user['favourites_count']
    cursor = db.users.find({'screen_name_lower': user['screen_name_lower']}).skip(1)
    for user2 in cursor:
      if user2['id'] != user['id']: print(" user {} and {} have same screen name but different ids".format(user['id'], user2['id']))
      db.users.update_one(user2, {'$unset': {'screen_name_lower':1}})
  count = 0
  cursor = db.users.find({'screen_name_lower': {'$gt': ''}})
  for user in Bar("Users: ", max=cursor.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(cursor):
    del user['_id']
    if 'timestamp_at' in user: del user['timestamp_at']
    if 'statuses_count' in user: del user['statuses_count']
    if 'favourites_count' in user: del user['favourites_count']
    user['screen_name_lower'] = None
    cursor = db.users.find(user).skip(1)
    del user['screen_name_lower']
    for user2 in cursor:
      inner_id = user2['_id']
      del user2['_id']
      if 'timestamp_at' in user2: del user2['timestamp_at']
      if 'statuses_count' in user2: del user2['statuses_count']
      if 'favourites_count' in user2: del user2['favourites_count']
      if user == user2:
        print(" Delete {} {}".format(user2['screen_name'], user2['id']))
        db.users.delete_one({'_id' : inner_id})
        count += 1
