#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2017-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Reads and outputs the collection created by 'findcommontweets.py'
If you need to rebuild that collection, use 'findcommontweets.py' first
"""

import sys
import optparse
import itertools
import dateutil.parser
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
  parser.add_option('-n', '--number', action='store', dest='number', type='int', default=None, help='Only include users with N or more concurrent events.')
  parser.add_option('-t', '--threshold', action='store', dest='threshold', type='float', default=None, help='Only include users with more than the given percentage of copied tweets.')
  (options, args) = parser.parse_args()
  db, api = init_state(use_cache=False, ignore_api=True)

  verbose(options.verbose)

  graph = Counter()
  copiedtweets = defaultdict(lambda:[])
  criteria = defaultdict(lambda:{})

  if options.after: criteria['event_start'].update({'$gte': dateutil.parser.parse(options.after)})
  if options.before: criteria['event_start'].update({'$lte': dateutil.parser.parse(options.before)})

  botsfound = db.botsperweek.find(dict(criteria))
  if verbose():
    botsfound = Bar("Loading:", max=botsfound.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(botsfound)
  for v in botsfound:
    #for dest in v['user_ids']:
    users = v['user_ids']
    for tid in v['tweet_ids']:
      tw = db.tweets.find_one({'id': tid})
      if tw is None:
        print(u'OOPS: tweet missing: {}'.format(tid))
        continue
      dest = tw['user']['id']
      graph[(v['user_id'], dest)] += 1
      copiedtweets[dest].append(tid)
      if dest in users:
        users.remove(dest)
      else:
        print(u'tweet {} copier {} not found in users'.format(tid, dest))
    if len(users):
      for u in users:
        print(u'user listed without related tweet: {}'.format(id_to_userstr(db, u)))

  #if options.number:
    #everyone = set(u for e,w in graph.items() for u in e if w >= options.number)
  #else:
  everyone = set(u for e in graph.keys() for u in e)

  filtered = []
  with open(options.filename, "w") as f:
    # opening
    f.write("digraph {\n")
    # write vertices
    for uid in everyone:
      count =  db.tweets.count( {'user.id': uid, 'created_at': criteria['event_start'] })
      copied = len(set(copiedtweets[uid]))
      percentage = 100.0 * copied / count
      if options.threshold is not None and options.threshold > percentage:
        continue
      filtered.append(uid)
      f.write(u'  "{}" [screen_name="{}",seen_tweets={},copied_tweets={},percent={},shape="box",greek="{}",ignored="{}",tracked="{}",suspended="{}"];\n'.format(
        uid,
        id_to_userstr(db, uid),
        count,
        copied,
        percentage,
        is_greek(db, uid),
        is_ignored(db, uid),
        get_tracked(db, uid) != None,
        is_suspended(db, uid)
      ))
    # write edges
    filtered = set(filtered)
    for e in graph:
      (u1, u2) = e
      if u1 not in filtered and u2 not in filtered: continue
      f.write(u'  "{}" -> "{}" [weight={}];\n'.format(u1, u2, graph[e]))
    #closing
    f.write("}\n")


