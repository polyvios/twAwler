#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Utility functions used by twAwler
"""

import sys
import os
import time
import json
import twitter
from datetime import datetime, timedelta
from pymongo import MongoClient
from sets import Set
import atexit
import pprint
import config

class _MyPrettyPrinter(pprint.PrettyPrinter):
  def format(self, object, context, maxlevels, level):
    if isinstance(object, unicode):
      return (object.encode('utf8'), True, False)
    return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)

gprint = _MyPrettyPrinter(width=500).pprint
cache = None
verbose_state = False

def verbose(new_state=None):
  """
  Getter/setter for verbosity.
  Call verbose(true) to set.
  Call verbose() to read.
  """
  global verbose_state
  if new_state is not None:
    verbose_state = new_state
  return verbose_state


def tuple_add(t1, t2):
  """
  Add two tupples, elementwise.
  """
  return tuple(map(sum, zip(t1, t2)))


def init_state(use_cache=False, ignore_api=False):
  """
  Call this function to initialize connections to the DB and to Twitter. This is probably bad design and these two connections should be initialized separately, but oh well.

  use_cache: Set to true to preload set collections (dead, suspended, followed, greek, etc) into python dicts. May take a while, may not pay off. Only use for full scans, basically, if ever.
  ignore_api: Set to true if you don't want to connect to twitter.
  returns a tuple of the two connections: first is DB, second is twitter api
  """
  global cache
  hostname = os.environ.get('MONGO')
  if hostname:
    client = MongoClient(hostname)
  else:
    client = MongoClient()
  atexit.register(lambda: client.close())
  db = client[config.mongo]
  if ignore_api:
    api = None
  else:
    api = twitter.Api(consumer_key=config.consumer_key,
                      consumer_secret=config.consumer_secret,
                      access_token_key=config.access_token,
                      access_token_secret=config.access_token_secret,
                      sleep_on_rate_limit=True,
                      tweet_mode='extended')
  if use_cache:
    names = {}
    ids = {}
    ignored = Set()
    cemetery = Set()
    suspended = Set()
    protected = Set()
    greek = Set()
    for i in db.following.find():
      names[i['id']] = i
      ids[i['screen_name_lower']] = i
    for i in db.ignored.find():
      ignored.add(i['id'])
    for i in db.cemetery.find():
      cemetery.add(long(i['id']))
    for i in db.suspended.find():
      suspended.add(long(i['id']))
    for i in db.protected.find():
      protected.add(long(i['id']))
    for i in db.greeks.find():
      greek.add(long(i['id']))
    cache = {
      'names': names,
      'ids': ids,
      'ign': ignored,
      'dead': cemetery,
      'susp': suspended,
      'prot': protected,
      'gr': greek }
  return db, api

def id_to_userstr(db, uid):
  """
  Translate a user id :uid: to the corresponding lowercase screen name
  if it exists and is current, otherwise the last known screen name,
  otherwise a string of the form "unknown(id)"
  """
  u = get_tracked(db, uid=uid)
  if u is None:
    u = lookup_user(db, uid)
  return u['screen_name_lower'] if u and 'screen_name_lower' in u else u['screen_name'] if u and 'screen_name' in u else 'unknownid({})'.format(uid)

def pack_tweet(db, s):
  """
  Function that gets a string representation of a tweet :s:, or a
  dictionary, or a json object, and packs it into the representation
  used by our mongo tweets collection.  If the tweet contains URLs,
  they will be inserted into the shorturl collection. Datetimes are
  all UTC-tz-converted into mongo dates.
  """
  j = json.loads(unicode(s))
  if j.get('urls'):
    for url in j['urls']:
      db.shorturl.update_one(
        {'shorturl': url['url']},
        {'$set': {'shorturl': url['url'], 'url': url['expanded_url']}},
        upsert=True)
    j['urls'] = [ x['url'] for x in j['urls'] ]
  d = datetime.strptime(j['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
  if 'full_text' in j:
    txt = j['full_text']
    del j['full_text']
    j['text'] = txt
  j['created_at'] = d
  if j.get('hashtags'):
    j['hashtags'] = [ x['text'] for x in j['hashtags'] ]
  if j.get('retweeted_status', None) != None:
    if j['retweeted_status'].get('urls'):
      for url in j['retweeted_status']['urls']:
        db.shorturl.update_one(
          {'shorturl': url['url']},
          {'$set': {'shorturl': url['url'], 'url': url['expanded_url']}},
          upsert=True)
      j['retweeted_status']['urls'] = [ x['url'] for x in j['retweeted_status']['urls'] ]
      j['retweeted_status']['created_at'] = datetime.strptime(j['retweeted_status']['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
    if j['retweeted_status'].get('hashtags'):
      j['retweeted_status']['hashtags'] = [ x['text'] for x in j['retweeted_status']['hashtags'] ]
    if 'full_text' in j['retweeted_status']:
      txt = j['retweeted_status']['full_text']
      del j['retweeted_status']['full_text']
      j['retweeted_status']['text'] = txt
  return j

def get_followers(db, uid, timestamp=None):
  """
  Returns an iterable containing all follower ids for the user with
  the given uid.  If :timestamp: is used, it's a dictiorary containing
  criteria on the "date" field.
  """
  criteria = { 'follows': uid }
  if timestamp: criteria['date'] = timestamp
  followers = db.follow.aggregate(
    [ { '$match': criteria },
      { '$group': { '_id': '$id'} }
    ], allowDiskUse=True)
  return (x['_id'] for x in followers)
  #return db.follow.find({'follows': uid}).distinct('id')
  #return frozenset(x['id'] for x in db.follow.find(criteria))

def get_friends(db, uid, timestamp=None):
  criteria = { 'id': uid }
  if timestamp: criteria['date'] = timestamp
  friends = db.follow.aggregate(
    [ { '$match': criteria },
      { '$group': { '_id': '$follows'} }
    ], allowDiskUse=True)
  return (x['_id'] for x in friends)
  #return db.follow.find({'id': uid}).distinct('follows')

def get_tracked(db, uid=None, uname=None):
  global cache
  if cache:
    return cache['names'].get(uid, None) if uid else cache['ids'].get(uname, None)
  u = db.following.find_one({'id': uid})
  if u: return u
  u = db.following.find_one({'screen_name_lower': uname})
  return u

def lookup_user(db, uid = None, uname = None, ret_all = False):
  #u = get_tracked(db, uid, uname)
  #if u: return [u] if ret_all else u
  u = None
  if uid != None:
    u = [x for x in db.users.find({'id': uid, 'screen_name_lower': {'$gt': ''}}).sort('timestamp_at', -1)]
    if len(u) == 0:
      u = [x for x in db.users.find({'id': uid}).sort('timestamp_at', -1)]
  if uname != None:
    if uname[0] == '@': uname = uname[1:]
    u = [x for x in db.users.find({'screen_name_lower': uname.lower()}).sort('timestamp_at', -1)]
  if u == None or len(u) == 0: return [] if ret_all else None
  if ret_all: return u
  return u[0]


def is_ignored(db, uid):
  global cache
  if cache: return uid in cache['ign']
  u = db.ignored.find_one({'id': uid})
  return u != None


def is_dead(db, uid):
  global cache
  if cache: return uid in cache['dead']
  u = db.cemetery.find_one({'id': uid})
  return u != None


def is_greek(db, uid):
  global cache
  if cache: return uid in cache['gr']
  u = db.greeks.find_one({'id': uid})
  return u != None


def suspend(db, uid):
  global cache
  u = get_tracked(db, uid)
  if u:
    db.following.delete_one(u)
    if cache:
      cache['susp'].add(uid)
  try:
    if uid is not None:
      db.suspended.update_one({'id': uid}, {'$set': {'id': uid, 'last': datetime.utcnow()}}, upsert=True)
      u = lookup_user(db, uid)
      if u:
        db.users.update_one(u, {'$set': {'suspended': True}})
  except:
    print u'cannot insert suspended', uid, sys.exc_info()
  pass


def is_suspended(db, uid):
  global cache
  if cache: return uid in cache['susp']
  u = db.suspended.find_one({'id': uid})
  if u != None:
    now = datetime.utcnow()
    if 'last' not in u or u['last'] + timedelta(days=30) < now:
      print u'User {} last seen suspended more than 30 days ago, recheck'.format(uid)
      db.suspended.delete_one({'id': uid})
      return False
    return True
  return False


def protected(db, uid):
  global cache
  db.protected.update_one(
    {'id' : uid},
    { '$set' : { 'protected' : datetime.utcnow(), 'id' : uid} },
    upsert=True)
  db.following.delete_one({'id': uid})
  if cache:
    cache['prot'].add(uid)


def is_protected(db, uid):
  """
  Returns true if the given user is protected.

  Warning: this function is not pure!
  If the protected user was seen to be protected more than 30 days
  ago, they will be marked for re-checking at the first chance.
  """
  global cache
  if cache: return uid in cache['prot']
  x = db.protected.find_one({'id': uid})
  if x != None:
    now = datetime.utcnow()
    if x['protected'] + timedelta(days=30) < now:
      print u'User {} last seen protected more than 30 days ago, recheck'.format(uid)
      db.protected.delete_one({'id': uid})
      return False
    return True
  return False


def ignore_user(db, uid):
  """
  Mark a given user as ignored.

  :uid:  User ID of the user to be marked.
  """
  if is_dead(db, uid):
    print u'user dead, skip', uid
    return
  if is_ignored(db, uid):
    print u'already ignored', uid
    return
  db.ignored.insert_one({'id': uid})
  return

def bury_user(db, uid):
  global cache
  if uid == None: return
  if is_dead(db, uid):
    print u'already buried'
  else:
    db.cemetery.insert_one({'id': uid})
    if cache:
      cache['dead'].add(uid)
  if get_tracked(db, uid):
    db.following.delete_one({'id': uid})
  if is_ignored(db, uid):
    db.ignored.delete_one({'id': uid})
  for us in db.users.find({'id': uid}):
    if 'screen_name_lower' in us:
      db.cemetery.update_one({'id':uid}, {'$set':{'id':uid, 'screen_name_lower': us['screen_name_lower']}})
      print us['screen_name_lower'], u'marked dead'

#@profile
def add_user(db, api, u):
  global cache
  user = u.screen_name.lower()
  userid = u.id
  if is_dead(db, userid):
    if verbose(): print user, userid, u'this id was dead! re-adding.'
    db.cemetery.delete_one({'id': userid})
  oldu = get_tracked(db, userid)
  if oldu:
    other = db.following.find_one({'screen_name_lower': user.lower()})
    if other is not None and other['id'] != userid:
      print u'{} lost screen_name, refreshing'.format(other['id'])
      add_id(db, api, other['id'])
    db.following.update_one(oldu, {'$set': {'screen_name_lower': user.lower()}})
  for us in db.users.find({'screen_name_lower': user}):
    #db.users.update(us, {'$unset': {'screen_name_lower': 1}}, multi = True)
    db.users.update_one(us, {'$unset': {'screen_name_lower': 1}})
    if us['id'] != userid:
      if verbose(): print u'User {} has lost their screen_name {} to user {}, refreshing'.format(us['id'], user, userid)
      add_id(db, api, us['id'])
  #for us in db.users.find({'id': userid}):
  #db.users.update({'id': userid}, {'$unset': {'screen_name_lower': 1}}, multi = True)
  db.users.update_one({'id': userid}, {'$unset': {'screen_name_lower': 1}})
  u.status = None
  d = datetime.strptime(u.created_at, '%a %b %d %H:%M:%S +0000 %Y')
  j = json.loads(unicode(u))
  k = j.copy()
  if 'screen_name' in j:
    j['screen_name_lower'] = j['screen_name'].lower()
  else:
    if verbose(): print u'found mysterious user'
    j['screen_name'] = u'{}'.format(j['id'])
    j['screen_name_lower'] = u'{}'.format(j['id'])
  j['created_at'] = d
  j['timestamp_at'] = datetime.utcnow()
  #gprint(j)
  db.users.update_one(k, {'$set': j}, upsert=True) #insert if not exact duplicate
  if u.protected:
    if verbose(): print(u'protected user {} {}'.format(u.screen_name.lower(), u.id))
    protected(db, u.id)
  return j


def handle_twitter_error(db, api, e, uid=None, waitstr=None, waitfunc=None):
  """ This function handles all kinds of twitter exceptions

    :waitstr:  the string representation of the twitter api endpoint
               involved, so that if there's rate limiting, the function
               can wait appropriately
    :waitfunc: function/lambda to be called after rate limiting is waited out
    :return:   indicates that the action should or should not be retried
    :rtype:    boolean
  """
  global cache
  if str(e) == u'Not authorized.':
    if verbose(): print u'{} invalid user detected, trying to resolve'.format(uid),
    if uid: add_id(db, api, uid, force=True)
    return False
  if e[0] == 'json decoding':
    print u'json error: maybe corrupt stream?'
    return True
  if isinstance(e.message, list):
    m = e.message[0]
    if 'code' in m and m['code'] == 179 and uid:
      print u'found protected user', uid
      protected(db, uid)
      return False
    if 'code' in m and m['code'] == 88 and waitstr:
      if uid: print u'rate error for', uid, u'wait'
      else: print u'rate error, wait'
      try:
        time.sleep(api.GetSleepTime(waitstr))
      except:
        time.sleep(100)
      if waitfunc: waitfunc(True)
      return True
    if 'code' in m and m['code'] == 130:
      print u'overcapacity error, wait'
      time.sleep(10)
      if waitfunc: waitfunc(True)
      return True
    if 'code' in m and m['code'] == 63:
      if uid: suspend(db, uid)
      print uid, u'suspended'
      #suspend(db, uid)
      return False
    if 'code' in m and m['code'] == 50 and uid:
      bury_user(db, uid)
      print uid, u'dead, buried'
      return False
    if 'code' in m and m['code'] == 34 and uid:
      #bury_user(db, uid)
      print uid, u'probably dead but not buried as this error is unreliable:', sys.exc_info()
      return False
  print u'({},{}) could not handle:'.format(uid, waitstr),
  gprint(e)
  return False


def add_id(db, api, uid, wait=True, force=False):
  if verbose():
    if is_dead(db, uid): print uid, u'dead, trying anyway'
    if is_protected(db, uid): print uid, u'protected, trying anyway'
    if is_ignored(db, uid): print uid, u'ignored still adding'
  x = get_tracked(db, uid)
  if verbose():
    if x: print uid, u'already followed as', x['screen_name_lower']
  existing = db.users.find_one({'id': uid, 'screen_name_lower' : {'$gt': ''}})
  if not force and existing and existing.get('timestamp_at', datetime.utcnow() - timedelta(days=45)) > datetime.utcnow() - timedelta(days=30):
    if verbose(): print u'user info crawled less than 30 days ago, skip'
    return
  try:
    u = api.GetUser(user_id=uid)
    add_user(db, api, u)
  except twitter.TwitterError as e:
    handle_twitter_error(db, api, e, uid, 'users/show/:id' if wait else None, None)
    return
  except:
    print u'some other error, skip user', uid, sys.exc_info()
    return
  if verbose(): print u.screen_name.lower(), u'inserted'


def user_is_missing(db, uid):
  if is_dead(db, uid): return False
  if is_suspended(db, uid): return False
  u = db.users.find_one({'id': uid})
  if u is None: return True
  return False
 
def get_if_missing(db, api, uid):
  x = user_is_missing(db, uid)
  if x:
    print u'unknown {}'.format(uid),
    add_id(db, api, uid)
    u = lookup_user(db, uid)
    if u is not None:
      print u'{}'.format(u.get('screen_name_lower', 'not found'))


def add100_id(db, api, idlist):
  addedlist = []
  if verbose(): print 'another {}'.format(len(idlist))
  try:
    users = api.UsersLookup(user_id=idlist)
  except twitter.TwitterError as e:
    handle_twitter_error(db, api, e, None, '/users/lookup', None)
    if verbose():
      print 'error, retrying one-by-one'
    map(lambda i: get_if_missing(db, api, i), idlist)
    return []
  for u in users:
    #u1 = user._json
    #u = twitter.User.NewFromJsonDict(u1)
    j = add_user(db, api, u)
    addedlist.append(j)
    idlist.remove(u.id)
  for i in idlist:
    if verbose():
      print u'user {} not found, marking dead'.format(i)
    bury_user(db, i)
  return addedlist


'''
  adds user u (as returned by twitter api, not json dictionary) to the
  followed users
'''
def add_to_followed(db, uid, uname, protect):
  if is_dead(db, uid):
    if verbose(): print uname, uid, u'this id was dead! re-adding.'
    db.cemetery.delete_one({'id': uid})
  if protect:
    print u'WARNING: protected user', uname, uid, u'aborting'
    protected(db, uid)
    return
  db.following.delete_many({'id': uid})
  db.following.insert_one({'id': uid, 'screen_name_lower': uname})
  lidval = db.tweets.aggregate(
    [ { '$match':{'user.id': uid}},
      { '$group': { '_id' : '$user.id', 'last': { '$max' : '$id'}}}
    ])
  lidlist = list(lidval)
  if len(lidlist) != 0:
    value = lidlist[0]['last']
  else:
    value = None
  db.crawlerdata.update_one(
    {'id' : uid},
    { '$set' : { 'id' : uid, 'lastid' : value } },
    upsert=True)
  print u'added {} / {}'.format(uname, uid)
  return


def can_follow(db, uid, refollow):
  if get_tracked(db, uid=uid):
    if verbose(): print uid, u'already tracked, skip'
    return False
  if not refollow and is_dead(db, uid):
    if verbose(): print uid, u'dead, skip'
    return False
  if is_ignored(db, uid):
    if refollow:
      if verbose(): print uid, u're-following'
      db.ignored.delete_one({'id': uid})
    else:
      if verbose(): print uid, u'ignored, skip'
      return False
  if is_suspended(db, uid):
    if verbose(): print uid, u'was last seen suspended, refresh userid manually'
    return False
  if is_protected(db, uid):
    if verbose(): print uid, u'was protected less than 30 days ago, skip'
    return False
  return True

def follow_user(db, api, uid=None, uname=None, wait=False, refollow=False):
  global cache
  if uname:
    x = lookup_user(db, uid, uname)
    if x: uid = x['id']
  if uid:
    if not can_follow(db, uid, refollow):
      return
  try:
    if uname:
      u = api.GetUser(screen_name=uname)
    else:
      u = api.GetUser(user_id=uid)
  except twitter.TwitterError as e:
    repeatf = lambda x: follow_user(db, api, uid if uname==None else None, uname, False, refollow)
    handle_twitter_error(db, api, e, uid, 'users/show/:id', repeatf)
    return
  except:
    print u'unknown exception ({}, {}): {}'.format(uid, uname, sys.exc_info()[0])
    return
    #raise
  #assert(uid == None or uid == u.id)
  add_user(db, api, u)
  uid = u.id
  uname = u.screen_name.lower()
  add_to_followed(db, uid, uname, u.protected)
  return



def is_recently_scanned(db, uid, scantype):
  now = datetime.utcnow()
  last = db.lastscan.find_one({'id': uid, 'action': scantype})
  if last != None and last['date'] + timedelta(days=30) > now:
    return last['date']
  return None

