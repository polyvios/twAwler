#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Compute which users (out of all vectorized) have most activity between 19:00 and 07:00 (17:00-05:00 gmt)
retry: use max_daily_intervals.
"""

import sys
import optparse
import csv
from twkit import *
from twkit.utils import *

fieldnames = [
  'id',
  'screen_name',
  'is_nightowl',
  'night_tweets',
  'day_tweets',
  'max_daily_interval',
  'avg_max_daily_interval',
  'min_max_daily_interval',
  'median_max_daily_interval',
  'stdev_max_daily_interval'
 ]

hours = [0, 1, 2, 3, 4, 5, 18, 19, 20, 21, 22, 23]

def save_owls(db, filename, greek_only):
  with open(filename, 'w') as csvfile:
    vectorwriter = csv.DictWriter(csvfile,
      fieldnames=fieldnames,
      restval='',
      quoting=csv.QUOTE_MINIMAL)

    vectorwriter.writeheader()
    uservectors = db.uservectors.find({},
      { 'id': 1,
        'screen_name': 1,
        'tweets_per_hour_of_day': 1,
        'max_daily_interval': 1
      })
    for v in uservectors:
      flr = {}
      flr['id'] = v['id']
      if greek_only and not is_greek(db, v['id']):
        continue
      flr['screen_name'] = v['screen_name']
      night_tweets = sum(d['count'] for d in v['tweets_per_hour_of_day'] if d['hour'] in hours)
      day_tweets = sum(d['count'] for d in v['tweets_per_hour_of_day'] if d['hour'] not in hours)
      flr['night_tweets'] = night_tweets
      flr['day_tweets'] = day_tweets
      flr['is_nightowl'] = night_tweets > day_tweets
      flr['max_daily_interval'] = v['max_daily_interval']['max']
      flr['avg_max_daily_interval'] = v['max_daily_interval']['avg']
      flr['min_max_daily_interval'] = v['max_daily_interval']['min']
      flr['median_max_daily_interval'] = v['max_daily_interval']['med']
      flr['stdev_max_daily_interval'] = v['max_daily_interval']['std']
      vectorwriter.writerow(flr)


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("-o", "--output", action="store", dest="filename", default="nightowls.csv", help="Output file")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids.")
  parser.add_option("--greek", action="store_true", dest="greek", default=False, help="Ignore any users not marked as greek")
  (options, args) = parser.parse_args()
  db, _ = init_state(use_cache=False, ignore_api=True)
  verbose(options.verbose)

  save_owls(db, 'nightowls.csv', options.greek)

