#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import sys
import tweepy
import twitter
from progress.bar import Bar
import optparse
from datetime import datetime
from twkit.utils import *
from pymongo.errors import CursorNotFound
import config

def add100(db, api, twitterapi, idlist):
  print('another {}'.format(len(idlist)))
  try:
    tweets = api.statuses_lookup(id_=idlist, trim_user=True)
  except tweepy.error.RateLimitError:
    sleeptime = -1
    until = datetime.fromtimestamp(twitterapi.CheckRateLimit('/statuses/lookup').reset)
    sleeptime = (until - datetime.now()).total_seconds()
    #sleeptime = twitterapi.GetSleepTime('/statuses/lookup')
    print("rate limit, wait", sleeptime)
    if sleeptime > 0:
      time.sleep(int(sleeptime)+1)
      return add100(db, api, twitterapi, idlist )
    return []
  except tweepy.error.TweepError as e:
    print('other error {}'.format(str(e)))
    time.sleep(2)
    return []
  bulk = db.tweets.initialize_unordered_bulk_op()
  for tweet in tweets:
    j1 = tweet._json
    tw = twitter.Status.NewFromJsonDict(j1)
    j2 = pack_tweet(db, tw)
    bulk.find({'id': tw.id}).update({'$unset': {'deleted':1}})
    bulk.find({'id': tw.id}).upsert().update({'$set': j2})
    idlist.remove(tw.id)
  for i in idlist:
    print('tweet {} not found'.format(i))
    bulk.find({'id':i}).upsert().update({'$set': {'deleted': True}})
  sys.stdout.flush()
  bulk.execute()
  return idlist


def repopulate(db, api, twitterapi, uid=None, skip=False):
  idlist = []
  if uid is None:
    tweets = db.tweets.find({'retweeted_status.id': {'$gt': 0}, 'user_mentions': None, 'deleted': None}).batch_size(200)
    #tweets = db.tweets.find({'urls': {'$type': 2}, 'deleted': None, '$where': '(this.urls[0].length > 30)'})
    #tweets = db.tweets.find({'text': {'$regex': 'http'}, 'urls': {'$exists': 0}}).limit(100)
  else:
    #tweets = db.tweets.find({'user.id': uid, 'text': None, 'deleted': None})
    tweets = db.tweets.find({'user.id': uid, 'retweeted_status.id': {'$gt': 0}, 'user_mentions': None, 'deleted': None})
    #tweets = db.tweets.find({'user.id': uid, 'text': {'$regex': 'http'}, 'deleted': None, 'urls': {'$exists': 0}}).limit(100)
  #print("found {}".format(tweets.count()))
  if skip:
    tweets = tweets.skip(2000)
  if verbose():
    tweets = Bar("Processing:", suffix = '%(index)d/%(max)d - %(eta_td)s', term_width=40).iter(tweets)
  for tw in tweets:
    i = tw['id']
    idlist.append(i)
    if len(idlist) == 100:
      add100(db, api, twitterapi, idlist)
      idlist = []
  if len(idlist):
    add100(db, api, twitterapi, idlist)
  #bulk = db.tweets.initialize_unordered_bulk_op()
  #for i in idlist:
    #bulk.find({'id': i}).update({'$unset': {'retweeted_status.urls':1}})
  #try:
    #bulk.execute()
  #except:
    #pass

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('-a', '--all', action='store_true', dest='all', default=False, help='Try all users')
  parser.add_option('-s', '--skip', action='store_true', dest='skip', default=False, help='Skip 1000 tweets in search. For use with second parallel crawler.')
  parser.add_option('--id', action='store_true', dest='ids', default=False, help='Input is user id.')
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  (options, args) = parser.parse_args()

  auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
  auth.set_access_token(config.access_token, config.access_token_secret)
  api = tweepy.API(auth)

  verbose(options.verbose)
  db, twitterapi = init_state(use_cache=False)
  if options.all:
    while True:
      try:
        repopulate(db, api, twitterapi, None, options.skip)
        break
      except CursorNotFound:
        continue
  else:
    for userstr in args:
      u = lookup_user(db, uid=int(userstr)) if options.ids else lookup_user(db, uname=userstr)
      if u is None:
        print("unknown user", userstr)
        continue
      uid = u['id']
      if verbose(): print('repopulate id {}'.format(uid))
      repopulate(db, api, twitterapi, uid, options.skip)

