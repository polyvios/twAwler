#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

# crawl all users that follow the given user(s), add to db

import sys
import twitter
import optparse
from datetime import datetime, timedelta
from twkit.utils import *

def addfriends(db, api, uid, force=False, updateusers=True):
  last = db.lastscan.find_one({'id': uid, 'action': 'friends'})
  now = datetime.utcnow()
  if not force and last != None and last['date'] + timedelta(days=100) > now:
    print "already scanned during last 100 days"
    return
  nextc = -1
  friends = [0]
  while len(friends):
    try:
      nextc, prevc, friends = api.GetFriendsPaged(user_id=uid, cursor=nextc, skip_status=True)
      print u'.',
      sys.stdout.flush()
      for u in friends:
        db.follow.insert_one({'id': uid, 'follows': u.id, 'date': now})
        if updateusers: add_user(db, api, u)
    except twitter.TwitterError as e:
      if handle_twitter_error(db, api, e, uid, 'friends/list', None):
        print u'got exception, retrying'
        continue
      return
    except:
      print u'other exception: {}'.format(sys.exc_info())
      return
  db.lastscan.update_one(
    {'id': uid, 'action': 'friends'},
    {'$set': {'date': now}},
    upsert=True)
  print u'done'


def addfriendids(db, api, uid, wait=False, addusers=False):
  last = db.lastscan.find_one({'id': uid, 'action': 'friends'})
  now = datetime.utcnow()
  if last != None and last['date'] + timedelta(days=100) > now:
    print "already scanned during last 100 days"
    return
  try:
    cursor = api.GetFriendIDs(user_id=uid)
  except twitter.TwitterError as e:
    if handle_twitter_error(db, api, e, uid, 'friends/list' if wait else None, None):
      addfriendids(db, api, uid, wait, addusers)
    return
  except:
    return
  print u'got {}'.format(len(cursor)),
  sys.stdout.flush()
  for userid in cursor:
    db.follow.insert_one({'id': uid, 'follows': userid, 'date': now})
    if addusers:
      follow_user(db, api, uid=userid, wait=True)
  db.lastscan.update_one(
    {'id': uid, 'action': 'friends'},
    {'$set': {'date': now}},
    upsert=True)
  print u'done'


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-a", "--addusers", action="store_true", dest="addusers", default=False, help="Add all followers to tracked users")
  parser.add_option("--updateusers", action="store_true", dest="updateusers", default=False, help="Update user info (for --full scan)")
  parser.add_option("--all", action="store_true", dest="all", default=False, help="Scan all tracked users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names")
  parser.add_option("--full", action="store_true", dest="full", default=False, help="Populate users into user table immediately")
  parser.add_option("-f", "--force", action="store_true", dest="force", default=False, help="Do not check for staleness")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  db, api = init_state()

  if options.all:
    options.ids = True
    userlist = [x['id'] for x in db.following.find().sort('id', 1 if options.full else -1)]
  else:
    userlist = [x.lower().replace("@", "") for x in args]
  for user in userlist:
    uname = None if options.ids else user
    uid = long(user) if options.ids else None
    u = lookup_user(db, uid, uname)
    print "Get {} friends".format(u.get('screen_name_lower', user)),
    sys.stdout.flush()
    if is_ignored(db, u['id']):
      print "skip ignored user", uname, uid
      continue
    if options.full:
      addfriends(db, api, u['id'], force=options.force, updateusers=options.updateusers)
    else:
      addfriendids(db, api, u['id'], wait=True, addusers=options.addusers)

