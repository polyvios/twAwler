#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Load all tweets allowed starting from the first seen tweet of the
given user and going backwards. Once twitter answers with zero, it
means its limit is reached, so this account is marked as not having
any older tweets that are reachable via the API.
"""

import sys
import time
import twitter
import optparse
from datetime import datetime
from pymongo.errors import BulkWriteError
from twkit.utils import *

def load_past(db, api, u, max_req=-1):
  uid = u['id']
  uname = u['screen_name_lower']
  cdata = db.crawlerdata.find_one({ 'id' : uid })
  if cdata != None and cdata.get('reached', False):
    return
  if cdata == None or cdata.get('firstid') == None:
    fidval = db.tweets.aggregate([
      {'$match':{'user.id': uid}},
      { '$group':
        { '_id' : 'user.id',
          'fst': { '$min' : '$id'}
        }
      }])
    flist = list(fidval)
    if fidval != None and len(flist) != 0:
      minid = flist[0]['fst'] - 1
    else:
      minid = None
    #db.crawlerdata.update_one({'id': uid}, {'$set': {'firstid': minid}})
  else:
    minid = cdata['firstid'] - 1
  earliestdate = cdata.get('earliest') if cdata else datetime.utcnow()
  count = 0
  flag = is_greek(db, uid)
  posts = []
  print "Past {:<20}".format(uname),
  sys.stdout.flush()
  while max_req != 0:
    max_req -= 1
    try:
      posts = api.GetUserTimeline(user_id=uid,
        trim_user=True,
        max_id=minid,
        count=200)
      print ".",
      sys.stdout.flush()
    except twitter.TwitterError as e:
      print "exception for", uname, e, uid,
      repeatf = lambda x: load_past(db, api, u, max_req)
      handle_twitter_error(db, api, e, uid, 'statuses/user_timeline', repeatf)
      print ""
      return
    except:
      print "some other error, retrying",sys.exc_info()[0],
      sys.stdout.flush()
      time.sleep(1)
      continue
    if len(posts) == 0:
      db.crawlerdata.update_one(
        {'id': uid},
        {'$set': {'id': uid, 'reached': True}},
        upsert = True)
      break
    if minid == None:
      db.crawlerdata.update_one(
        { 'id': uid },
        { '$set': { 'id': uid, 'lastid': posts[0].id, 'latest': datetime.utcnow()} },
        upsert=True)
    d = None
    bulk = db.tweets.initialize_unordered_bulk_op()
    for s in posts:
      count += 1
      if s.lang == config.lang: flag = True
      j = pack_tweet(db, s)
      d = j['created_at']
      try:
        bulk.insert(j)
      except:
        print "some issue", j, sys.exc_info()[0]
        sys.stdout.flush()
        pass
      if minid == None or earliestdate == None or s.id < minid:
        minid = s.id - 1
        earliestdate = d
    try:
      bulk.execute()
    except BulkWriteError as bwe:
      print(bwe.message),
      sys.stdout.flush()
      continue
    if minid != None:
      db.crawlerdata.update_one(
        {'id': uid},
        {'$set': {'id': uid, 'firstid': minid}},
        upsert = True)
    if earliestdate != None:
      db.crawlerdata.update_one(
        {'id': uid},
        {'$set': {'id': uid, 'earliest': earliestdate}},
        upsert = True)

  if(count > 0):
    print "Found", count, "tweets" if flag else "NON-GR tweets"
  else:
    print "no tweets found"
  sys.stdout.flush()
  if minid != None:
    db.crawlerdata.update_one(
      {'id': uid},
      {'$set': {'id': uid, 'firstid': minid}},
      upsert = True)
  if earliestdate != None:
    db.crawlerdata.update_one(
      {'id': uid},
      {'$set': {'id': uid, 'earliest': earliestdate}},
      upsert = True)
  else:
    db.crawlerdata.update_one(
      {'id': uid},
      {'$set': {'id': uid, 'crawlerdata': datetime.utcnow()}},
      upsert = True)
  return

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is ids, not usernames")
  parser.add_option("-a", "--all", action="store_true", dest="all", default=False, help="Try all users")
  parser.add_option("-q", "--quiet", action="store_false", dest="verbose", default=True, help="Silence")
  parser.add_option("--crawl-req", action="store", dest="req", type='int', default=-1, help="How many requests per account (use for missing-late accounts only)")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, api = init_state(use_cache=False)
  if options.all:
    for user in db.following.find():
      load_past(db, api, user, max_req=options.req)
  else:
    userlist = [x.lower().replace("@", "") for x in args]
    for user in userlist:
      uid = long(user) if options.ids else None
      uname = None if options.ids else user
      x = get_tracked(db, uid=uid, uname=uname)
      if x:
        load_past(db, api, x, max_req=options.req)
      else:
        if verbose(): print "Unknown user", uname, uid, x, "first add user for tracking. Abort."
        sys.stdout.flush()

