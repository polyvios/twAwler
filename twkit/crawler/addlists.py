#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Crawls and adds all lists of the given user(s) to db.
"""

import sys
import twitter
import optparse
from datetime import datetime, timedelta
import pprint
import json
from twkit.utils import *
from pymongo.errors import BulkWriteError

_generic_exception = False

def addlistmembers(db, api, list_id, slug):
  global _generic_exception
  last = db.lastscan.find_one({'list_id': list_id, 'action': 'listmembers'})
  now = datetime.utcnow()
  if last is not None and last['date'] + timedelta(days=60) > now:
    print u'already scanned during last 60 days'
    return
  try:
    cursor = api.GetListMembers(list_id, slug, skip_status=True, include_entities=False)
  except twitter.TwitterError as e:
    if handle_twitter_error(db, api, e, uid, 'lists/members', None):
      addlistmembers(db, api, list_id, slug)
    return
  except:
    e = sys.exc_info()
    if _generic_exception:
      sys.stderr.write(u'Got exception again, abort: {}'.format(e))
      raise 
    _generic_exception = True
    sys.stderr.write(u'Got an exception, sleep and retry once: {}'.format(sys.exc_info()))
    addlistmembers(db, api, list_id, slug)
    return
  print u'got {}'.format(len(cursor))
  now = datetime.utcnow()
  bulk = db.listmembers.initialize_unordered_bulk_op()
  if len(cursor):
    for u in cursor:
      if lookup_user(db, uid=u.id) is None:
        print 'unknown',
      print u' {} {}'.format(u.id, u.screen_name.lower())
      d = {'date': now, 'user_id': u.id, 'list_id': list_id}
      bulk.insert(d)
    try:
      bulk.execute()
    except BulkWriteError as bwe:
      if verbose(): print bwe.message,
      pass
  db.lastscan.update_one(
    {'list_id': list_id, 'action': 'listmembers'},
    {'$set': {'date': now}},
    upsert=True)


def addlistsubscriptions(db, api, uid, force):
  global _generic_exception
  last = db.lastscan.find_one({'id': uid, 'action': 'listsubscriptions'})
  now = datetime.utcnow()
  if not force and last is not None and last['date'] + timedelta(days=60) > now:
    print u'already scanned during last 60 days'
    return
  cursor=-1
  while cursor is not None:
    try:
      data = api.GetSubscriptions(user_id=uid, count=500, cursor=cursor, return_json=True)
      next_cursor = data.get('next_cursor', 0)
      previous_cursor = data.get('previous_cursor', 0)
      lists = data['lists'] #[twitter.List.NewFromJsonDict(x) for x in data['lists']]
      if next_cursor == 0 or next_cursor == previous_cursor:
        cursor = None 
      else:
        cursor = next_cursor
    except twitter.TwitterError as e:
      if handle_twitter_error(db, api, e, uid, 'lists/subscriptions', None):
        continue
      pprint.pprint(e)
      return
    except:
      e = sys.exc_info()
      if _generic_exception:
        sys.stderr.write(u'Got exception again, abort: {}'.format(e))
        raise 
      _generic_exception = True
      sys.stderr.write(u'Got an exception, sleep and retry once: {}'.format(sys.exc_info()))
      addlistsubscriptions(db, api, uid, force)
      return
    print u'got {} lists'.format(len(lists))
    if len(lists) == 0: continue
    bulk = db.listsubscribers.initialize_unordered_bulk_op()
    for l in lists:
      #l = json.loads(unicode(l))
      l['owner_id'] = l['user']['id']
      print l['full_name']
      k = l.copy()
      l['date'] = now
      db.lists.update_one(k, {'$set': l}, upsert=True)
      addlistmembers(db, api, l['id'], l['slug'])
      d = {'date': now, 'user_id': uid, 'list_id': l['id']}
      bulk.insert(d)
    try:
      bulk.execute()
    except BulkWriteError as bwe:
      if verbose(): print bwe.message,
      pass
  db.lastscan.update_one(
    {'id': uid, 'action': 'listsubscriptions'},
    {'$set': {'date': now}},
    upsert=True)


def addlistmemberships(db, api, uid, force):
  global _generic_exception
  last = db.lastscan.find_one({'id': uid, 'action': 'listmemberships'})
  now = datetime.utcnow()
  if not force and last is not None and last['date'] + timedelta(days=60) > now:
    print u'already scanned during last 60 days'
    return
  cursor=-1
  while cursor is not None:
    try:
      data = api.GetMemberships(user_id=uid, count=500, cursor=cursor, return_json=True)
      next_cursor = data.get('next_cursor', 0)
      previous_cursor = data.get('previous_cursor', 0)
      lists = data['lists'] #[twitter.List.NewFromJsonDict(x) for x in data['lists']]
      if next_cursor == 0 or next_cursor == previous_cursor:
        cursor = None
      else:
        cursor = next_cursor
    except twitter.TwitterError as e:
      if handle_twitter_error(db, api, e, uid, 'lists/memberships', None):
        continue
      pprint.pprint(e)
      return
    except:
      e = sys.exc_info()
      if _generic_exception:
        sys.stderr.write(u'Got exception again, abort: {}'.format(e))
        raise 
      _generic_exception = True
      sys.stderr.write(u'Got an exception, sleep and retry once: {}'.format(sys.exc_info()))
      addlistmemberships(db, api, uid, force)
      return
    print u'got {} lists'.format(len(lists))
    for l in lists:
      #l = json.loads(unicode(l))
      l['owner_id'] = l['user']['id']
      print l['full_name']
      k = l.copy()
      l['date'] = now
      db.lists.update_one(k, {'$set': l}, upsert=True)
      addlistmembers(db, api, l['id'], l['slug'])
  db.lastscan.update_one(
    {'id': uid, 'action': 'listmemberships'},
    {'$set': {'date': now}},
    upsert=True)

def addlists(db, api, uid, force):
  global _generic_exception
  last = db.lastscan.find_one({'id': uid, 'action': 'lists'})
  now = datetime.utcnow()
  if not force and last is not None and last['date'] + timedelta(days=60) > now:
    print u'already scanned during last 60 days'
    return
  try:
    cursor = api.GetLists(user_id=uid)
  except twitter.TwitterError as e:
    if handle_twitter_error(db, api, e, uid, 'lists/ownerships', None):
      addlists(db, api, uid, force)
    return
  except:
    e = sys.exc_info()
    if _generic_exception:
      sys.stderr.write(u'Got exception again, abort: {}'.format(e))
      raise 
    _generic_exception = True
    sys.stderr.write(u'Got an exception, sleep and retry once: {}'.format(sys.exc_info()))
    addlists(db, api, uid, force)
    return
  print u'got {} lists'.format(len(cursor))
  for l in cursor:
    l = json.loads(unicode(l))
    l['owner_id'] = l['user']['id']
    print l['full_name']
    k = l.copy()
    l['date'] = now
    db.lists.update_one(k, {'$set': l}, upsert=True)
    addlistmembers(db, api, l['id'], l['slug'])
  db.lastscan.update_one(
    {'id': uid, 'action': 'lists'},
    {'$set': {'date': now}},
    upsert=True)

if __name__ == '__main__':
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <user> [<user> ...]')
  parser.add_option("--all", action="store_true", dest="all", default=False, help="Scan all tracked users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names")
  parser.add_option("--lists", action="store_true", dest="lists", default=False, help="Get all lists of given user.")
  parser.add_option("--memberships", action="store_true", dest="memberships", default=False, help="Get all list memberships of given user.")
  parser.add_option("--subscriptions", action="store_true", dest="subscriptions", default=False, help="Get all list subscriptions of given user.")
  parser.add_option("--lid", action="store_true", dest="lid", default=False, help="Input is not users, it's list IDs.")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("-f", "--force", action="store_true", dest="force", default=False, help="Scan anyway")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state()

  if options.lid:
    for lid in args:
      lid = long(lid)
      addlistmembers(db, api, lid, None)
    sys.exit(0)

  if options.all:
    options.ids = True
    userlist = [x['id'] for x in db.following.find().sort('id', 1 if options.lists else -1)]
  else:
    userlist = [x.lower().replace("@", "") for x in args]

  for user in userlist:
    uname = None if options.ids else user
    uid = long(user) if options.ids else None
    u = lookup_user(db, uid, uname)
    if 'listed_count' not in u:
      if verbose(): print "skipping {} lists, zero counted in user info".format(id_to_userstr(db, u['id']))
      continue
    print "getting {} ({}) lists".format(u.get('screen_name_lower'), user)
    if is_ignored(db, u['id']):
      if verbose(): print "skip ignored user", uname, uid
      continue
    if options.memberships:
      addlistmemberships(db, api, u['id'], options.force)
    if options.subscriptions:
      addlistsubscriptions(db, api, u['id'], options.force)
    if options.lists:
      addlists(db, api, u['id'], options.force)
    if not options.lists and not options.memberships and not options.subscriptions:
      print "pick one of possible crawl sources. abort."
      sys.exit(1)
