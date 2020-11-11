#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Count and print out the greek tweet count and the total tweet count
(and ratio) for each followed non-greek user.
"""

import optparse
from progress.bar import Bar
from collections import Counter
from datetime import datetime, timedelta
from twkit.utils import *


def count_tweets(db):
  cursor = db.tweets.aggregate([
    {'$match': {'retweeted_status': None}},
    {'$group': {'_id': '$user.id', 'count': {'$sum': 1}}}
  ])
  counter = Counter()
  for c in cursor:
    whoid = c['_id']
    cnt = c['count']
    if get_tracked(db, whoid) == None: continue
    if is_greek(db, whoid): continue
    counter[whoid] = cnt
  return counter


def count_gr_tweets(db):
  cursor = db.tweets.aggregate([
    {'$match': {'lang': config.lang, 'retweeted_status': None}},
    {'$group': {'_id': '$user.id', 'count': {'$sum': 1}}}
  ])
  elcounter = Counter()
  for c in cursor:
    whoid = c['_id']
    cnt = c['count']
    if get_tracked(db, whoid) == None: continue
    if is_greek(db, whoid): continue
    elcounter[whoid] = cnt
  return elcounter


if __name__ == '__main__':
  start_time = datetime.utcnow()
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("--tracked", action="store_true", dest="tracked", default=False, help="Limit to tracked users.")
  parser.add_option("-f", "--filter", action="store_true", dest="filter", default=False, help="Only print info for accounts with enough data.")
  parser.add_option("--force", action="store_true", dest="force", default=False, help="Compute anyway.")
  parser.add_option("-u", "--user", action="store_true", dest="user", default=False, help="Only print info for given accounts.")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Users given as IDs.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  db, _ = init_state(use_cache=False, ignore_api=True)
  if options.user:
    userlist = []
    for uname in args:
      if options.tracked:
        u = get_tracked(db, int(uname), None) if options.ids else get_tracked(db, None, uname)
      else:
        u = lookup_user(db, int(uname), None) if options.ids else lookup_user(db, None, uname)
      if u is None:
        if verbose():
          sys.stderr.write(u'user {} missing\n'.format(uname))
      else:
        userlist.append(u)
    if verbose():
      userlist = Bar("Loading:", max=len(userlist), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(userlist)
  else:
    userlist = db.following.find().batch_size(10)
    if verbose():
      userlist = Bar("Loading:", max=db.following.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(userlist)
  for u in userlist:
    if u is None:
      sys.stderr.write(u'impossible\n')
      continue
    uid = u['id']
    if not options.force and is_greek(db, uid):
      #if verbose(): sys.stderr.write(u'{}/{} already greek, skip\n'.format(id_to_userstr(db, uid), uid))
      continue
    #counter = db.tweets.find({'user.id': uid, 'retweeted_status': None}).count()
    counter = db.tweets.find({'user.id': uid, 'lang': {'$exists': 1}}).count()
    if counter < 100 and options.filter:
      if verbose(): sys.stderr.write(u'{} has less than 100 tweets, skip\r'.format(id_to_userstr(db, uid)))
      continue
    #elcounter = db.tweets.find({'user.id': uid, 'lang': config.lang, 'retweeted_status': None}).count()
    elcounter = db.tweets.find({'user.id': uid, 'lang': config.lang}).count()
    print(u'{} {} {} {} {} '.format(
      uid, id_to_userstr(db, uid),
      elcounter, counter, 1.0*elcounter/max(counter,1)
    ).encode('utf-8'), end='')
    us = lookup_user(db, uid=uid)
    print(u'{} {} {}'.format(us.get('name',"").replace('\n', ' '),
      us.get('location', '').replace('\n', ' ').replace('\r', ' '),
      us.get('description', '').replace('\n', ' ').replace('\r', ' ')
    ).encode('utf-8'))

  if options.user:
    pass
  else:
    update_crawlertimes(db, "greek-tweets", start_time)
