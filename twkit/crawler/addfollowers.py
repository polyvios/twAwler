#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Crawl all followers of the given user(s) and insert them into the
follow relation.  Depending on the crawled endpoint, this may also
populate the 'users' collection with user information.
"""

import sys
import twitter
import optparse
from datetime import datetime, timedelta
from twkit.utils import *

def addfollowers(db, api, uid, force=False):
  """
  Crawl followers using the followers/list api endpoint and populate
  the follow colloection.  Since this endpoint returns user
  objects, we also add them into the database users collection.
  """
  last = db.lastscan.find_one({'id': uid, 'action': 'followers'})
  now = datetime.utcnow()
  if not force and last != None and last['date'] + timedelta(days=config.follow_scan_days) > now:
    print("already scanned during last {} days".format(config.follow_scan_days))
    return
  nextc = -1
  followers = [0]
  while len(followers):
    try:
      nextc, prevc, followers = api.GetFollowersPaged(user_id=uid, cursor=nextc, skip_status=True)
      print(u'.', end='')
      sys.stdout.flush()
      for u in followers:
        db.follow.insert_one({'id': u.id, 'follows': uid, 'date': now})
        add_user(db, api, u)
    except twitter.TwitterError as e:
      if handle_twitter_error(db, api, e, uid, 'followers/list', None):
        print(u'got exception, retrying')
        continue
      return
    except:
      print(u'other exception: {}'.format(sys.exc_info()))
      return
  db.lastscan.update_one(
    {'id': uid, 'action': 'followers'},
    {'$set': {'date': now}},
    upsert=True)
  print(u'done')


def addfollowerids(db, api, uid, wait=False, addusers=False):
  """
  Crawls the followers/ids endpoint and updates the follow collection.
  Does not get user objects. If you want user objects after the follow
  relation is somewhat populated use the fillfollow.py module.
  """
  last = db.lastscan.find_one({'id': uid, 'action': 'followers'})
  now = datetime.utcnow()
  if last != None and last['date'] + timedelta(days=config.follow_scan_days) > now:
    print("already scanned during last {} days".format(config.follow_scan_days))
    return
  try:
    cursor = api.GetFollowerIDs(user_id=uid)
  except twitter.TwitterError as e:
    if handle_twitter_error(db, api, e, uid, 'followers/ids' if wait else None, None):
      addfollowerids(db, api, uid, wait, addusers)
    return
  except:
    return
  print(u'got {}'.format(len(cursor)), end='')
  sys.stdout.flush()
  for userid in cursor:
    db.follow.insert_one({'id': userid, 'follows': uid, 'date': now})
    if addusers:
      follow_user(db, api, uid=userid, wait=True)
  db.lastscan.update_one(
    {'id': uid, 'action': 'followers'},
    {'$set': {'date': now}},
    upsert=True)
  print(u'done')


if __name__ == '__main__':
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <user> [<user> ...]')
  parser.add_option("-a", "--addusers", action="store_true", dest="addusers", default=False, help="Add all followers to tracked users")
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
    uid = int(user) if options.ids else None
    u = lookup_user(db, uid, uname)
    uid = u['id']
    print("Get {} followers".format(u.get('screen_name_lower', user)), end='')
    sys.stdout.flush()
    if is_ignored(db, uid) and not options.force:
      print("skip ignored user", uname, uid)
      continue
    # omit users with very few tweets in the db
    if u.get('statuses_count', 0) < 10 and u.get('followers_count', 0) < 10 and u.get('friends_count', 0) < 10:
      print("skip inactive user {}/{}".format(uid, id_to_userstr(db,uid)))
      continue
    if options.full:
      addfollowers(db, api, u['id'], force = options.force)
    else:
      addfollowerids(db, api, u['id'], wait=True, addusers=options.addusers)

