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
import optparse
from datetime import datetime, timedelta
from progress.bar import Bar
from twkit.utils import *

if __name__ == "__main__":
  parser = optparse.OptionParser()
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  db, _ = init_state(use_cache=False, ignore_api=True)
  start_time = datetime.utcnow()
  ignored = db.ignored.find()
  if verbose():
      ignored = Bar("Processing:", max=db.ignored.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(ignored)

  for u in ignored:
    cursor = db.tweets.aggregate([
      { '$match': { 'user.id': u['id'] } },
      { '$group': {'_id': '$user.id', 'count': {'$sum': 1}}}
    ], allowDiskUse=True)
    for c in cursor:
      whoid = c['_id']
      cnt = c['count']
      if not is_ignored(db, whoid):
        print "Impossible! {} - {}/{}".format(u['id'], whoid, id_to_userstr(db, whoid))
        continue
      if is_protected(db, whoid):
        print "{}/{} is both protected and ignored".format(whoid, id_to_userstr(db, whoid))
      u = lookup_user(db, whoid)
      print "{} {}/{}".format(cnt, id_to_userstr(db, whoid), whoid)
      sys.stdout.flush()
  update_crawlertimes(db, "ignored", start_time)

  #for u in db.following.find():
  #  name = u['screen_name_lower']
  #  cursor = tweets.aggregate([
  #    {'$match': {'user.id' : u['id']}},
  #    {'$group': {'_id': '$user.id', 'count': {'$sum': 1}}}
  #  ])
  #  for c in cursor:
  #    cnt = c['count']
  #    print cnt, name
