#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
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
import atexit
import pprint
import config
from calendar import timegm
from time import gmtime

#class _MyPrettyPrinter(pprint.PrettyPrinter):
#  """
#  Helper class used to format utf-8 text (esp containing greek posts).
#  """
#  def format(self, object, context, maxlevels, level):
#    if isinstance(object, str):
#      return (object.encode('utf8'), True, False)
#    if isinstance(object, bytes):
#      return (object.decode('utf8'), True, False)
#    return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)

#gprint = _MyPrettyPrinter(width=500).pprint
_cache = None
verbose_state = False

def get_cache():
  return _cache

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


def printout_limits(db, api):
  """
    Gets latest available rate limits from the api object, if one
    exists and is initialized, and copies them into the database.
    This is used by the web dashboard to monitor the progress of the
    crawler.
  """
  if api is None: return
  if api.rate_limit is None: return
  for d in api.rate_limit.resources:
    for r in api.rate_limit.resources[d]:
      l = api.rate_limit.get_limit(r)
      db.lastlimits.update({'resource': r}, {
        '$set': {
          'resource': r,
          'limit': l
        }
      },  upsert=True)


def init_state(use_cache=False, ignore_api=False):
  """
  Call this function to initialize connections to the DB and to Twitter. This is probably bad design and these two connections should be initialized separately, but oh well.

  use_cache: Set to true to preload set collections (dead, suspended, followed, greek, etc) into python dicts. May take a while, may not pay off. Only use for full scans, basically, if ever.
  ignore_api: Set to true if you don't want to connect to twitter.
  returns a tuple of the two connections: first is DB, second is twitter api
  """
  global _cache
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
    ignored = set()
    cemetery = set()
    suspended = set()
    protected = set()
    greek = set()
    for i in db.following.find():
      names[i['id']] = i
      ids[i['screen_name_lower']] = i
    for i in db.ignored.find():
      ignored.add(i['id'])
    for i in db.cemetery.find():
      cemetery.add(int(i['id']))
    for i in db.suspended.find():
      suspended.add(int(i['id']))
    for i in db.protected.find():
      protected.add(int(i['id']))
    for i in db.greeks.find():
      greek.add(int(i['id']))
    _cache = {
      'names': names,
      'ids': ids,
      'ign': ignored,
      'dead': cemetery,
      'susp': suspended,
      'prot': protected,
      'gr': greek }
  atexit.register(printout_limits, db, api)
  return db, api


def look_for_mentioned_id(db, userid):
  """
  Helper function aimed to mine deleted or missing user IDs from
  crawled data.  Looks for any mentions of the given ID, and if they
  contain a full user object, inserts it into the users collection for
  the next lookup to find.  This is aimed to be used internally.
  """
  for mention in db.tweets.find({'user_mentions' : { '$elemMatch' : {u'id': userid}}}).limit(3):
    #sys.stdout.flush()
    username = None
    for i in mention['user_mentions']:
      if i['id'] == userid:
        username = i['screen_name']
        break
    if username == None: continue
    u = db.users.find_one({'id': userid})
    if u != None: continue
    if verbose():
      print("not found in users, adding")
      if is_ignored(db, userid):
        print("is ignored, adding anyway")
      sys.stdout.flush()
    try:
      if db.users.count({'screen_name_lower': username.lower()}) > 0:
        db.users.update_one({'id':userid}, {'$set': {'id':userid, 'screen_name': username}}, upsert=True)
      else:
        db.users.update_one({'id':userid, 'screen_name_lower': username}, {'$set': {'id':userid, 'screen_name': username, 'screen_name_lower': username.lower()}}, upsert=True)
      if verbose():
        print("keyname of mentioned user {}/{} inserted into users".format(userid, username))
        sys.stdout.flush()
    except Exception as e:
      sys.stderr.write(u"cannot insert user found in mentions: {}\n".format(e))
      sys.stderr.flush()
      pass
  return


def id_to_userstr(db, uid):
  """
  Translate a user id :uid: to the corresponding lowercase screen name
  if it exists and is current, otherwise the last known screen name,
  otherwise a string of the form "unknown(id)"
  """
  u = get_tracked(db, uid=uid)
  if u is None:
    u = lookup_user(db, uid)
  if u and 'screen_name_lower' in u:
    userstr = u['screen_name_lower']
  else:
    if u and 'screen_name' in u:
      userstr = u['screen_name']
    else:
      # for speed, lookup but still return unknown.
      # at least next time it'll be fixed
      look_for_mentioned_id(db, uid)
      userstr = u'unknownid({})'.format(uid)
  return userstr


def pack_tweet(db, s):
  """
  Function that gets a string representation of a tweet :s:, or a
  dictionary, or a json object, and packs it into the representation
  used by our mongo tweets collection.  If the tweet contains URLs,
  they will be inserted into the shorturl collection. Datetimes are
  all UTC-tz-converted into mongo dates.
  """
  j = json.loads(str(s))
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
  """
  Returns an iterable containing all friend ids for the user with the
  given uid.  If :timestamp: is used, it's a dictiorary containing
  criteria on the "date" field.
  """
  criteria = { 'id': uid }
  if timestamp: criteria['date'] = timestamp
  friends = db.follow.aggregate(
    [ { '$match': criteria },
      { '$group': { '_id': '$follows'} }
    ], allowDiskUse=True)
  return (x['_id'] for x in friends)
  #return db.follow.find({'id': uid}).distinct('follows')

def get_tracked(db, uid=None, uname=None):
  """
  Looks up given id or username into the set of tracked users. If a
  user is found, the user info is returned.

  Note: this function does not return a full user object, but rather
  user information in the :following: collection. If you need a full
  user object, use :lookup_user: instead.
  """
  global _cache
  if _cache:
    return _cache['names'].get(uid, None) if uid else _cache['ids'].get(uname, None)
  u = db.following.find_one({'id': uid})
  if u or uname is None: return u
  u = db.following.find_one({'screen_name_lower': uname.lower()})
  return u

def lookup_user(db, uid = None, uname = None, ret_all = False):
  """
  Look up a user ID or name into the collection of user objects. Can
  return only the latest hit, or all user objects that match,
  depending on the value of the :ret_all: parameter.  Returns only
  latest user object that matches by default.
  """
  #u = get_tracked(db, uid, uname)
  #if u: return [u] if ret_all else u
  u = None
  if uid != None:
    u = [x for x in db.users.find({'id': uid, 'screen_name_lower': {'$gt': ''}}).sort('timestamp_at', -1)]
    if len(u) == 0:
      u = [x for x in db.users.find({'id': uid}).sort('timestamp_at', -1)]
  if (u is None) and (uname is not None):
    if uname[0] == '@': uname = uname[1:]
    u = [x for x in db.users.find({'screen_name_lower': uname.lower()}).sort('timestamp_at', -1)]
  if u == None or len(u) == 0: return [] if ret_all else None
  if ret_all: return u
  return u[0]


def is_ignored(db, uid):
  """
  Check whether a user id belongs to the set of ignored (definitely
  not greek) users.  Returns true/false.
  """
  global _cache
  if _cache: return uid in _cache['ign']
  u = db.ignored.find_one({'id': uid})
  return u != None


def is_dead(db, uid):
  """
  Check whether a user id has been found to have been deleted by the
  crawler.  Returns true/false.  For now, the crawler does not track
  whether a deleted user is permanently deleted (expiration period has
  passed) or is "freshly" deleted.

  Note: a user may be marked as deleted on occasion when twitter api
  returns the wrong kind of error message.  Dead users may need to be
  verified.  Sometimes dead users are later found to be alive or
  reactivated.
  """
  global _cache
  if _cache: return uid in _cache['dead']
  u = db.cemetery.find_one({'id': uid})
  return u != None


def is_greek(db, uid):
  """
  Checks whether the given user ID is in the set of greek-speaking
  users. Criteria for greek-speaking are currently external (look into
  bash scripts calling the crawler) and marked by "setgreek" utility.
  """
  global _cache
  if _cache: return uid in _cache['gr']
  u = db.greeks.find_one({'id': uid})
  return u != None


def suspend(db, uid):
  global _cache
  u = get_tracked(db, uid)
  if u:
    db.following.delete_one(u)
    if _cache:
      _cache['susp'].add(uid)
  try:
    if uid is not None:
      db.suspended.update_one({'id': uid}, {'$set': {'id': uid, 'last': datetime.utcnow()}}, upsert=True)
      u = lookup_user(db, uid)
      if u:
        db.users.update_one(u, {'$set': {'suspended': True}})
  except:
    print(u'cannot insert suspended', uid, sys.exc_info())
  pass


def is_suspended(db, uid):
  global _cache
  if _cache: return uid in _cache['susp']
  u = db.suspended.find_one({'id': uid})
  if u != None:
    now = datetime.utcnow()
    if 'last' not in u or u['last'] + timedelta(days=config.suspended_expiration_days) < now:
      print(u'User {} last seen suspended more than {} days ago, recheck'.format(uid, config.suspended_expiration_days))
      db.suspended.delete_one({'id': uid})
      return True # last time this is true
    return True
  return False


def protected(db, uid):
  global _cache
  db.protected.update_one(
    {'id' : uid},
    { '$set' : { 'protected' : datetime.utcnow(), 'id' : uid} },
    upsert=True)
  db.following.delete_one({'id': uid})
  if _cache:
    _cache['prot'].add(uid)


def is_protected(db, uid):
  """
  Returns true if the given user is protected.

  Warning: this function is not pure!
  If the protected user was seen to be protected more than [config.protected_expiration_days] days
  ago, they will be marked for re-checking at the first chance.
  """
  global _cache
  if _cache: return uid in _cache['prot']
  x = db.protected.find_one({'id': uid})
  if x != None:
    now = datetime.utcnow()
    if x['protected'] + timedelta(days=config.protected_expiration_days) < now:
      print(u'User {} last seen protected more than {} days ago, recheck'.format(uid, config.protected_expiration_days))
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
    print(u'user dead, skip', uid)
    return
  if is_ignored(db, uid):
    print(u'already ignored', uid)
    return
  db.ignored.insert_one({'id': uid})
  return

def bury_user(db, uid):
  global _cache
  if uid == None: return
  if is_dead(db, uid):
    print(u'already buried')
  else:
    db.cemetery.insert_one({'id': uid})
    if _cache:
      _cache['dead'].add(uid)
  if get_tracked(db, uid):
    db.following.delete_one({'id': uid})
  if is_ignored(db, uid):
    db.ignored.delete_one({'id': uid})
  for us in db.users.find({'id': uid}):
    if 'screen_name_lower' in us:
      db.cemetery.update_one({'id':uid}, {'$set':{'id':uid, 'screen_name_lower': us['screen_name_lower']}})
      print(us['screen_name_lower'], u'marked dead')

#@profile
def add_user(db, api, u):
  global _cache
  user = u.screen_name.lower()
  userid = u.id
  if is_dead(db, userid):
    if verbose(): print(user, userid, u'this id was dead! re-adding.')
    db.cemetery.delete_one({'id': userid})
  oldu = get_tracked(db, userid)
  if oldu:
    other = db.following.find_one({'screen_name_lower': user.lower()})
    if other is not None and other['id'] != userid:
      print(u'{} lost screen_name, refreshing'.format(other['id']))
      add_id(db, api, other['id'])
    try:
      db.following.update_one(oldu, {'$set': {'screen_name_lower': user.lower()}})
    except:
      print(u'Cannot insert user {} into db'.format(user))
      pass
  for us in db.users.find({'screen_name_lower': user}):
    #db.users.update(us, {'$unset': {'screen_name_lower': 1}}, multi = True)
    db.users.update_one(us, {'$unset': {'screen_name_lower': 1}})
    if us['id'] != userid:
      if verbose(): print(u'User {} has lost their screen_name {} to user {}, refreshing'.format(us['id'], user, userid))
      add_id(db, api, us['id'])
  #for us in db.users.find({'id': userid}):
  #db.users.update({'id': userid}, {'$unset': {'screen_name_lower': 1}}, multi = True)
  db.users.update_one({'id': userid}, {'$unset': {'screen_name_lower': 1}})
  u.status = None
  d = datetime.strptime(u.created_at, '%a %b %d %H:%M:%S +0000 %Y')
  j = json.loads(str(u))
  k = j.copy()
  if 'screen_name' in j:
    j['screen_name_lower'] = j['screen_name'].lower()
  else:
    if verbose(): print(u'found mysterious user')
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
  global _cache
  if str(e) == u'Not authorized.':
    if verbose(): print(u'{} invalid user detected, trying to resolve'.format(uid), end=' ')
    if uid: add_id(db, api, uid, force=True)
    return False
  if isinstance(e, list) and e[0] == 'json decoding':
    print(u'json error: maybe corrupt stream?')
    return True
  if isinstance(e.message, list):
    m = e.message[0]
    #if isinstance(e, twitter.error.TwitterError)
    if 'code' in m and m['code'] == 179 and uid:
      print(u'found protected user', uid)
      protected(db, uid)
      return False
    if 'code' in m and m['code'] == 88 and waitstr:
      if uid: print(u'rate error for', uid, u'wait')
      else: print(u'rate error, wait')
      try:
        time.sleep(api.GetSleepTime(waitstr))
      except:
        time.sleep(100)
      if waitfunc: waitfunc(True)
      return True
    if 'code' in m and m['code'] == 130:
      print(u'overcapacity error, wait')
      time.sleep(10)
      if waitfunc: waitfunc(True)
      return True
    if 'code' in m and m['code'] == 63:
      if uid: suspend(db, uid)
      print(uid, u'suspended')
      #suspend(db, uid)
      return False
    if 'code' in m and m['code'] == 50:
      if uid:
        bury_user(db, uid)
        print(uid, u'dead, buried')
      else:
        print(u'uname dead, unknown uid')
      return False
    if 'code' in m and m['code'] == 34 and uid:
      #bury_user(db, uid)
      print(uid, u'probably dead but not buried as this error is unreliable:', sys.exc_info())
      add_id(db, api, uid, wait=False, force=False)
      return False
  print(u'({},{}) could not handle:'.format(uid, waitstr), end='')
  print(e)
  return False


def lookup_user_or_add_if_missing(db, api, uname, wait=True, force=False):
  u = lookup_user(db, uname=uname)
  if u and not force: return u
  try:
    if verbose():
      print("Did not find {} locally, look up on twitter".format(uname))
    u = api.GetUser(screen_name=uname)
    add_user(db, api, u)
    return lookup_user(db, uname=uname)
  except twitter.error.TwitterError as e:
    repeatf = lambda x: lookup_user_or_add_if_missing(db, api, uname, wait=False, force=False)
    handle_twitter_error(db, api, e, None, 'users/show/:id' if wait else None, repeatf)
    return lookup_user(db, uname=uname)
  except:
    return None

def add_id(db, api, uid, wait=True, force=False):
  if verbose():
    if is_dead(db, uid): print(uid, u'dead, trying anyway')
    if is_protected(db, uid): print(uid, u'protected, trying anyway')
    if is_ignored(db, uid): print(uid, u'ignored still adding')
  x = get_tracked(db, uid)
  if verbose():
    if x: print(uid, u'already followed as', x['screen_name_lower'])
  existing = db.users.find_one({'id': uid, 'screen_name_lower' : {'$gt': ''}})
  if not force and existing and existing.get('timestamp_at', datetime.utcnow() - timedelta(days=config.user_expiration_days+1)) > datetime.utcnow() - timedelta(days=config.user_expiration_days):
    if verbose(): print(u'user info crawled less than 30 days ago, skip')
    return
  try:
    u = api.GetUser(user_id=uid)
    add_user(db, api, u)
  except twitter.TwitterError as e:
    handle_twitter_error(db, api, e, uid, 'users/show/:id' if wait else None, None)
    return
  except:
    print(u'some other error, skip user', uid, sys.exc_info())
    return
  if verbose(): print(u.screen_name.lower(), u'inserted')


def user_is_missing(db, uid):
  if is_dead(db, uid): return False
  if is_suspended(db, uid): return False
  u = db.users.find_one({'id': uid})
  if u is None: return True
  return False

def get_if_missing(db, api, uid):
  x = user_is_missing(db, uid)
  if x:
    print(u'unknown {}'.format(uid), end='')
    add_id(db, api, uid)
    u = lookup_user(db, uid)
    if u is not None:
      print(u'{}'.format(u.get('screen_name_lower', 'not found')))


def add100_id(db, api, idlist):
  while True:
    addedlist = []
    if verbose(): print('another {}'.format(len(idlist)))
    try:
      users = api.UsersLookup(user_id=idlist)
    except twitter.error.TwitterError as e:
      handle_twitter_error(db, api, e, None, '/users/lookup', None)
      if verbose():
        print('error, retrying one-by-one')
      map(lambda i: get_if_missing(db, api, i), idlist)
      return []
    except:
      print(u'got other exception: {}. retrying.'.format(sys.exc_info()[0]))
      continue
    for u in users:
      #u1 = user._json
      #u = twitter.User.NewFromJsonDict(u1)
      j = add_user(db, api, u)
      addedlist.append(j)
      idlist.remove(u.id)
    for i in idlist:
      if verbose():
        print(u'user {} not found, marking dead'.format(i))
      bury_user(db, i)
    return addedlist


'''
  adds user uid to the followed users
'''
def add_to_followed(db, uid, uname, protect):
  if is_dead(db, uid):
    if verbose(): print(uname, uid, u'this id was dead! re-adding.')
    db.cemetery.delete_one({'id': uid})
  if protect:
    print(u'WARNING: protected user', uname, uid, u'aborting')
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
  print(u'added {} / {}'.format(uname, uid))
  return


def can_follow(db, uid, refollow):
  if get_tracked(db, uid=uid):
    if verbose(): print(uid, u'already tracked, skip')
    return False
  if not refollow and is_dead(db, uid):
    if verbose(): print(uid, u'dead, skip')
    return False
  if is_ignored(db, uid):
    if refollow:
      if verbose(): print(uid, u're-following')
      db.ignored.delete_one({'id': uid})
    else:
      if verbose(): print(uid, u'ignored, skip')
      return False
  if is_suspended(db, uid):
    if verbose(): print(uid, u'was last seen suspended, refresh userid manually')
    return False
  if is_protected(db, uid):
    if verbose(): print(uid, u'was protected less than {} days ago, skip'.format(config.protected_expiration_days))
    return False
  return True

def follow_user(db, api, uid=None, uname=None, wait=False, refollow=False):
  global _cache
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
  except twitter.error.TwitterError as e:
    repeatf = lambda x: follow_user(db, api, uid if uname==None else None, uname, False, refollow)
    handle_twitter_error(db, api, e, uid, 'users/show/:id', repeatf)
    return
  except:
    print(u'unknown exception ({}, {}): {}'.format(uid, uname, sys.exc_info()[0]))
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
  if last != None and last['date'] + timedelta(days=config.recent_scan_days) > now:
    return last['date']
  return None


def update_crawlertimes(db, title, start_time):
  end_time = datetime.utcnow()
  db.crawlertimes.update({'date': start_time, 'title': title},
    {'$set': {
      'date': start_time,
      'title': title,
      'seconds': (end_time - start_time).total_seconds()
    }}, upsert=True)

def save_dot(db, graph, filename, weight=False):
  with open(filename, 'w') as dotfile:
    dotfile.write("digraph {\n")
    for uid in graph:
      n1 = id_to_userstr(db, uid)
      for i in graph[uid]:
        n2 = id_to_userstr(db, i)
        if weight:
          dotfile.write(u'"{}/{}" -> "{}/{}" [weight={}];\n'.format(uid, n1, i, n2, graph[uid][i]))
        else:
          dotfile.write(u'"{}/{}" -> "{}/{}";\n'.format(uid, n1, i, n2))
    dotfile.write("}")
  return

def save_edgelist(db, graph, filename, weight=False):
  with open(filename, 'w') as txtfile:
    for uid1 in graph:
      for uid2 in graph[uid1]:
        if weight:
          txtfile.write(u'{} {} {}\n'.format(uid1, uid2, graph[uid1][uid2]))
        else:
          txtfile.write(u'{} {}\n'.format(uid1, uid2))
  return



