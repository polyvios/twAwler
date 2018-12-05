#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Gets all tweets of the given user starting from the latest tweet and going
backwards, either until Twitter doesn't give any more (3200 limit) or
until the last tweet seen is re-seen.
"""

import sys
import twitter
import pymongo
import optparse
from datetime import datetime
from pymongo.errors import BulkWriteError
from twkit.utils import *


def dumpall(db, api, uid, uname, max_req=-1):
  x = get_tracked(db, uid=uid, uname=uname)
  if x:
    uid = x['id']
    uname = x['screen_name_lower']
  else:
    if verbose(): print "Unknown user", uname, uid, x, "first add user for tracking. Abort."
    return
  add_id(db, api, uid, wait=False)
  cdata = db.crawlerdata.find_one({ 'id': uid })
  last = cdata['lastid']
  newlast = last
  maxid = None
  count = 0
  flag = is_greek(db, uid)
  posts = []
  print "Dump {:<20}".format(uname),
  while max_req != 0:
    sys.stdout.flush()
    max_req -= 1
    try:
      posts = api.GetUserTimeline(user_id=uid,
        trim_user=True,
        since_id=last-1 if last != None and last != 0 else None,
        max_id=maxid,
        count=200)
      print ".",
    except twitter.TwitterError as e:
      if verbose(): print "exception for", uname, e, uid,
      repeatf = lambda x: dumpall(db, api, uid, uname, max_req)
      handle_twitter_error(db, api, e, uid, 'statuses/user_timeline', repeatf)
      return
    except:
      if verbose(): print "some other error, retrying",sys.exc_info()[0],
      time.sleep(2)
      continue
    db.crawlerdata.update_one({'id': uid}, { '$set': {'id': uid, 'latest': datetime.utcnow() }}, upsert=True)
    if len(posts) <= 1: break
    bulk = db.tweets.initialize_unordered_bulk_op()
    for s in posts:
      if maxid == None or maxid > s.id:
        maxid = s.id -1
      if s.id == last:
        break
      count += 1
      if newlast < s.id:
        newlast = s.id
      if s.lang == config.lang: flag = True
      j = pack_tweet(db, s)
      try:
        bulk.insert(j)
      except:
        if verbose(): print "some issue", j, sys.exc_info()[0]
        pass
    try:
      bulk.execute()
    except BulkWriteError as bwe:
      if verbose(): print bwe.message,
      pass
    if maxid <= last: break
  if(count > 0):
    db.crawlerdata.update_one(
      {'id': uid},
      {'$set': {'lastid': newlast}}
    )
    print "Found", count, "tweets" if flag else "NON-GR tweets"
  else:
    print "no tweets found"
  sys.stdout.flush()
  return


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is ids, not usernames")
  parser.add_option("--crawl-expected", action="store", dest="expected", type='int', default=None, help="How many to crawl from the most expected to have written")
  parser.add_option("--crawl-late", action="store", dest="late", type='int', default=None, help="How many to crawl from the longest uncrawled")
  parser.add_option("--crawl-req", action="store", dest="req", type='int', default=None, help="How many requests per account (use for missing-late accounts only)")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="make noise.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, api = init_state()
  userlist = [x.lower().replace("@", "") for x in args]
  if options.expected:
    options.ids = True
    userlist = (x['id'] for x in db.frequences.find().sort('expected', pymongo.DESCENDING).limit(options.expected))
  elif options.late:
    options.ids = True
    userlist = (x['id'] for x in db.frequences.find().sort('hours', pymongo.DESCENDING).limit(options.late))
  for user in userlist:
    uid = long(user) if options.ids else None
    uname = None if options.ids else user
    r = db.frequences.delete_one({'id': uid})
    if r.deleted_count == 0 and (options.late or options.expected):
      if verbose: print "Missing from frequences, skip"
      continue
    if options.req:
      dumpall(db, api, uid, uname, max_req=options.req)
    else:
      dumpall(db, api, uid, uname)

