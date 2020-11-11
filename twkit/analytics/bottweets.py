#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2017-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Reads and outputs the tweets in the collection created by 'findcommontweets.py'
If you need to rebuild that collection, use 'findcommontweets.py' first
"""

import sys
import optparse
import itertools
from collections import Counter, defaultdict
from datetime import datetime,timedelta
from progress.bar import Bar
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("-o", "--output", action="store", dest="filename", default='botnets.dot', help="Output file.")
  parser.add_option('-a', '--after', action='store', dest='after', default=False, help='Start on given date.')
  parser.add_option('-b', '--before', action='store', dest='before', default=False, help='End on given date, inclusive.')
  parser.add_option('-u', '--users', action='store_true', dest='users', default=False, help='Also output user id.')
  (options, args) = parser.parse_args()
  db, _ = init_state(use_cache=False, ignore_api=True)
  verbose(options.verbose)

  criteria = defaultdict(lambda:{})

  if options.after: criteria['event_start'].update({'$gte': dateutil.parser.parse(options.after)})
  if options.before: criteria['event_start'].update({'$lte': dateutil.parser.parse(options.before)})

  botsfound = db.botsperweek.find(dict(criteria))
  if verbose():
    botsfound = Bar("Loading:", max=botsfound.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(botsfound)
  for v in botsfound:
    for tid in v['tweet_ids']:
      tw = db.tweets.find_one({'id': tid})
      if options.users:
        print(u'{} {}'.format(tw['user']['id'], tw['source']).encode('utf-8'))
      else:
        print(u'{}'.format(tw['source']).encode('utf-8'))
