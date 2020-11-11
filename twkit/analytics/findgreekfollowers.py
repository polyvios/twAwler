#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
scans all greek users and finds non-greek followed accounts, ranked by
greek followers
"""


import optparse
from collections import Counter, defaultdict
from progress.bar import Bar
import numpy as np
from twkit.utils import *

def aggregate_scan_greeks_followers():
  follow = db.greeks.aggregate([
    {'$limit': 10000 },
    {'$lookup': { 'from': 'follow', 'localField': 'id', 'foreignField': 'follows', 'as': 'follower'}},
    {'$unwind': '$follower'},
    {'$lookup': { 'from': 'greeks', 'localField': 'follower.id', 'foreignField': 'id', 'as': 'grfollower'}},
    {'$match': {'grfollower': []} },
    {'$project': {'id': '$id', 'follower': '$follower.id'}},
    {'$group': {'_id': '$follower', 'count': {'$sum':1}}}
  ], allowDiskUse=True)
  #follow = db.follow.find({}, {'id':1, 'follows':1}).sort([('id', 1), ('follows', 1)])
  if verbose():
    #follow = Bar("Loading:", max=db.follow.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(follow)
    follow = Bar("Loading:", max=db.follow.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(follow)
  nongrfollowers = Counter()
  for f in follow:
    nongrfollowers[f['_id']] = f['count']
  return nongrfollowers

def full_scan_greeks_followers():
  greeks = db.greeks.find().limit(10000)
  size = db.greeks.count()
  if verbose():
    greeks = Bar("Loading:", max=size, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(greeks)
  greeks = frozenset(x['id'] for x in greeks)
  followers = Counter()
  for uid in Bar(max=size).iter(greeks):
    fo = frozenset(get_followers(db, uid))
    followers += Counter(fo - greeks)
  return followers

def scan_greeks_followers():
  followers = Counter()
  greeks = db.greeks.find().batch_size(1).limit(10000)
  if verbose():
    greeks = Bar("Loading:", max=db.greeks.count(), suffix='%(index)d/%(max)d - %(eta_td)s').iter(greeks)
  for g in greeks:
    uid = g['id']
    for f in get_followers(db, uid):
      if is_greek(db, f): continue
      followers[f] += 1
  return followers

def iter_scan_greeks_followers(followable):
  greeks = db.greeks.find()
  size = db.greeks.count()
  if verbose():
    greeks = Bar("Loading greeks: ", max=size, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(greeks)
  greeks = frozenset(x['id'] for x in greeks)
  ignored = db.ignored.find()
  if verbose():
    ignored = Bar("Loading ignored:", max=db.ignored.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(ignored)
  ignored = frozenset(x['id'] for x in ignored)
  seen = set()
  for uid in (Bar("Processing gr:  ", max=size).iter(greeks) if verbose() else greeks):
    fo = frozenset(get_followers(db, uid)) - greeks - seen - ignored
    for f in (Bar("Processing fo:  ", max=len(fo)).iter(fo) if verbose() else fo):
      if followable:
        if is_protected(db, f): continue
        if is_dead(db, f): continue
        if is_ignored(db, f): continue
        if get_tracked(db, f) is not None: continue
      fu = lookup_user(db, f)
      friends = frozenset(get_friends(db, f))
      greekfriends = friends & greeks
      grfr = len(greekfriends)
      fr = len(friends)
      frc = -1
      if fu is not None and 'friends_count' in fu:
        frc = fu['friends_count']
      ratio = 1.0 * grfr / fr
      ratioc = 1.0 * grfr / frc
      print(u'{} {} {} {} {} {}'.format(grfr, fr, ratio, frc, ratioc, f))
    seen |= fo

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("--followable", action="store_true", dest="followable", default=False, help="Don't count protected/dead/ignored users.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, api = init_state(use_cache=False, ignore_api=True)
  if verbose():
    print(u'{} {} {} {} {} {}'.format('grfr', 'fr-seen', 'ratio', 'fr-tw', 'ratio-tw', 'friend-id'))
  iter_scan_greeks_followers(options.followable)
  #if verbose(): print("Aggregation starting")
  #follow = db.follow.aggregate([
  #  { '$group': { '_id': { 'id': '$id', 'follows': '$follows' } } }
  #], allowDiskUse=True)
  #followers = scan_greeks_followers()
  #followers = full_scan_greeks_followers()
  #for u, cnt in followers.most_common():
    #print(u'{} {}'.format(cnt, u))


