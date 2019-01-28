#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Computes the per-user tweet rate, as used by the crawler to prioritize crawling.
"""

import sys
import optparse
import pymongo
from progress.bar import Bar
from datetime import datetime, timedelta
from twkit.utils import *

now = datetime.now()
lastmonth = now - timedelta(days=60)

def process(db, i):
  userid = i['_id']
  earliest = i['earliest']
  latest = i['latest']
  if latest is None: latest = datetime.utcnow()
  if earliest is None: earliest = latest
  count = i['count']
  u = get_tracked(db, userid)
  if u == None: return
  username = u['screen_name_lower']
  if is_ignored(db, userid):
    print "found ignored followed", userid, username
    return
  if is_dead(db, userid):
    print "found dead followed", userid, username
    return
  cdata = db.crawlerdata.find_one({'id' : userid})
  if cdata: latest = max(latest, cdata.get('latest', 0))
  lid = i['lastid']
  fid = i['firstid']
  db.crawlerdata.update_one({'id' : userid}, {'$set' : {'latest' : latest, 'earliest': earliest, 'lastid' : lid, 'firstid' : fid}}, upsert=True)
  delta = latest - earliest
  #f = count / (delta.days+1)
  f = count * 3600.0 / (delta.total_seconds()+1)
  d = datetime.utcnow() - latest
  #e = d.days * f
  e = d.total_seconds() * f / 3600
  #print f, "tweets per hour", long(d.total_seconds()/3600), "hours since latest", e, "expected for", username, count, "tweets in", str(delta.total_seconds/3600), "days"
  db.frequences.delete_one({'id': u['id']})
  db.frequences.insert({
    'id': u['id'],
    'screen_name_lower': u['screen_name_lower'],
    'twph': long(f),
    'hours': long(d.total_seconds()/3600),
    'expected': long(e),
    'seentw': count,
    'seenhr': long(delta.total_seconds()/3600)
  })
 

def recompute_user_time_bounds(db, u):
  c = db.tweets.aggregate([
    {'$match': {'created_at': {'$gt': lastmonth}, 'user.id': u['id']}},
    {'$group':
      { '_id' : '$user.id',
        'earliest' : { '$min' : '$created_at' },
        'latest'   : { '$max' : '$created_at' },
        'lastid'   : { '$max' : '$id' },
        'firstid'  : { '$min' : '$id' },
        'count'    : { '$sum' : 1 }
      }
    }
  ])
  for i in c:
    process(db, i)


def compute_user_freq(db, u, dolastyear=True):
    username = u['screen_name_lower']
    userid = u['id']
    if is_ignored(db, userid):
      print "oops, found followed user in ignored", username
    cdata = db.crawlerdata.find_one({'id' : userid})
    if cdata is None or cdata.get('latest') is None:
      print "Missing late:", username
      return False
    if cdata is None or cdata.get('earliest') is None:
      print "Missing early:", username
      db.crawlerdata.update_one({'id' : userid}, {'$set' : {'earliest': datetime.utcnow()}}, upsert=True)
      return False
    latest = cdata['latest']
    earliest = cdata['earliest']
    delta = latest - earliest
    if latest < earliest:
      if verbose(): print "Recompute broken:", username, latest, earliest
      recompute_user_time_bounds(db, u)
      return False
    if dolastyear:
      count = db.tweets.count({'created_at': {'$gt': lastmonth}, 'user.id': userid})
    else:
      count = db.tweets.count({'user.id': userid})
    f = count * 3600.0 / (delta.total_seconds()+1)
    #d = datetime.utcnow() - latest
    #e = d.total_seconds() * f / 3600
    u['tweets_per_hour'] = f
    u['first_tweet_at'] = earliest
    u['last_tweet_at'] = latest
    u['total_hours'] = delta.total_seconds()/3600
    u['seen_tweets'] = count
    return True

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, _ = init_state(use_cache=False, ignore_api=True)
  db.frequences.drop()
  db.frequences.create_index([('id', pymongo.ASCENDING)], unique=True)
  db.frequences.create_index([('expected', pymongo.DESCENDING)])
  db.frequences.create_index([('hours', pymongo.DESCENDING)])

  userlist = db.following.find().batch_size(10) 
  if verbose():
    userlist = Bar("Loading:", max=db.following.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(userlist)
  for u in userlist:
    if not compute_user_freq(db, u): continue
    count = u['seen_tweets']
    f = u['tweets_per_hour']
    d = datetime.utcnow() - u['last_tweet_at']
    e = d.total_seconds() * f / 3600
    try:
      db.frequences.insert({
        'id': u['id'],
        'screen_name_lower': u['screen_name_lower'],
        'twph': long(f),
        'hours': long(d.total_seconds()/3600),
        'expected': long(e),
        'seentw': u['seen_tweets'],
        'seenhr': long(u['total_hours'])
      })
    except:
      if verbose():
        print "ignoring exception for {}: {}".format(u['id'], sys.exc_info())
      pass
 
    #print "{} tweets per hour {} hours since latest {} expected for {} {} tweets in {} hours".format(
    #  long(f),
    #  long(d.total_seconds()/3600),
    #  long(e),
    #  u['screen_name_lower'],
    #  u['seen_tweets'],
    #  long(u['total_hours']))
