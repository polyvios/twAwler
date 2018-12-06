#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Count the number of unique users and report number of userinfo samples for each
"""

import optparse
from twkit.utils import *
from progress.bar import Bar
from collections import Counter

if __name__ == '__main__':
  db, api = init_state()
  totalusers = db.users.count()
  #users = db.users.find({}, {'id': 1})
  uniqusers = db.users.aggregate([
    #{ '$group': { '_id': '$id' } },
    #{ '$group': { '_id': 1, 'count': {'$sum': 1} } }
    { '$group': { '_id': '$id', 'count': {'$sum': 1} } }
  ], allowDiskUse=True)
  #totalu = db.follow.find({'id': }).count()
  cnt = Counter()
  #users = Bar("Counting:", max=totalusers, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(users)
  #for u in users:
  #  cnt[u['id']] += 1
  #print totalusers, "user instances"
  #print len(cnt), "unique users"
  for u in uniqusers:
    print u['_id'], u['count']
