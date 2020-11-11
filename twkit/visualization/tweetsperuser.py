#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
Tool for generating tweet distributions
Flag "--vectorized" works with uservectors only, subset of users, but faster
Otherwise, counts everything (may take a while)
'''

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
from progress.bar import Bar
from twkit.utils import *
import optparse

parser = optparse.OptionParser()
parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
parser.add_option('--vectorized', action='store_true', dest='vectorized', default=False, help='List only vectorized users.')
parser.add_option('-g', '--greek', action='store_true', dest='greek', default=False, help='List only greek users.')
(options, args) = parser.parse_args()

db,api = init_state(use_cache=False)

twittercounts = []
crawlercounts = []

if options.vectorized:
  vectors = db.uservectors.find({}, {'tweet_count': 1, 'seen_total': 1})
  if options.verbose:
    vectors = Bar("Processing:", max=vectors.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(vectors)
  for v in vectors:
    twittercounts.append(v['tweet_count'])
    crawlercounts.append(v['seen_total'])
elif options.greek:
  greeks = db.greeks.find().batch_size(1)
  if options.verbose:
    greeks = Bar("Processing:", max=greeks.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(greeks)
  for g in greeks:
    cursor = db.tweets.aggregate([
      { '$match': { 'user.id' : g['id'] } },
      { '$group':
        { '_id': '$user.id',
          'count': {'$sum': 1}
        }
      }],
      allowDiskUse=True
    )
    for c in cursor:
      who = c['_id']
      whou = lookup_user(db, who)
      if whou is None:
        print("missing user: {}".format(who))
        continue
      crawlercounts.append(c['count'])
      twittercounts.append(whou.get('statuses_count', 0))
else:
  cursor = db.tweets.aggregate([
    { '$match': { 'user.id' : {'$gt': 0} } },
    { '$group':
      { '_id': '$user.id',
        'count': {'$sum': 1}
      }
    }],
    allowDiskUse=True
  )
  if options.verbose:
    cursor = Bar("Processing:", suffix = '%(index)d/%(max)d - %(eta_td)s').iter(cursor)
  for c in cursor:
    who = c['_id']
    whou = lookup_user(db, who)
    if whou is None:
      print("missing user: {}".format(who))
      continue
    crawlercounts.append(c['count'])
    twittercounts.append(whou.get('statuses_count', 0))

with open("twittercounts.txt", "w") as f:
  for cnt in twittercounts:
    f.write("{}\n".format(cnt))

with open("crawlercounts.txt", "w") as f:
  for cnt in crawlercounts:
    f.write("{}\n".format(cnt))

sorted_tw = np.sort(twittercounts)
sorted_cr = np.sort(crawlercounts)
plt.xscale('log')
plt.yscale('log')
twyvals=np.arange(len(sorted_tw))/float(len(sorted_tw)-1)
cryvals=np.arange(len(sorted_cr))/float(len(sorted_cr)-1)
plt.plot(sorted_tw, 1-twyvals, label='twitter')
plt.plot(sorted_cr, 1-cryvals, label='crawled')
plt.xlabel('Tweets')
plt.ylabel('PMF')
plt.legend(loc=3)
plt.savefig('tweetsperuser.png', bbox_inches='tight', pad_inches=0)
