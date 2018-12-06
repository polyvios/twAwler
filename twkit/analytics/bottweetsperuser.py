#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

#reads the collection created by findcommontweets.py
# if you need to rebuild that collection, use findcommontweets first

import sys
import optparse
import itertools
from collections import Counter, defaultdict
from datetime import datetime,timedelta
from pprint import pprint
from progress.bar import Bar
from twkit.utils import init_state, lookup_user, is_greek, is_ignored, get_tracked, is_suspended, id_to_userstr

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("-o", "--output", action="store", dest="filename", default='botnets.dot', help="Output file.")
  parser.add_option('-a', '--after', action='store', dest='after', default=False, help='Start on given date.')
  parser.add_option('-b', '--before', action='store', dest='before', default=False, help='End on given date, inclusive.')
  parser.add_option('-n', '--number', action='store', dest='number', type='int', default=1, help='Only count users with more than N concurrent events.')
  (options, args) = parser.parse_args()
  db, api = init_state(use_cache=False, ignore_api=True)

  verbose(options.verbose)
  graph = Counter()
  criteria = defaultdict(lambda:{})

  if options.after: criteria['event_start'].update({'$gte': dateutil.parser.parse(options.after)})
  if options.before: criteria['event_start'].update({'$lte': dateutil.parser.parse(options.before)})
  if options.number: criteria['same_found'].update({'$gte': int(options.number)})

  botsfound = db.botsperweek.find(dict(criteria))
  if verbose():
    botsfound = Bar("Loading:", max=botsfound.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(botsfound)

  usertweets = defaultdict(lambda:[])
  for v in botsfound:
    for t in v['tweet_ids']:
      tw = db.tweets.find_one({'id': t}, {'user.id':1})
      usertweets[tw['user']['id']].append(t)

  with open(options.filename, "w") as f:
    f.write("user_id, copied_tweets\n")
    for uid in usertweets:
      f.write(u'{} {}\n'.format(uid, len(set(usertweets[uid]))))

