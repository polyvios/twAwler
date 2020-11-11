#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################


''' 
This tool fills truncated tweets by crawling twitter for the full
version.
Truncated tweets sometimes exist in in json-imported data or
web-scraped data from external datasets).
'''


import sys
import tweepy
from twkit.utils import *
import twitter
import optparse
from progress.bar import Bar
import config



def add1(db, api, tw):
  try:
    tweet = api.GetStatus(tw['id'])
    j2 = pack_tweet(db, tweet)
    db.tweets.delete_one({'id': j2['id']})
    db.tweets.insert_one(j2)
  except twitter.TwitterError as e:
    if isinstance(e.message, list):
      m = e.message[0]
      if 'code' in m and m['code'] in [ 144, 34 ]:
        print("found deleted!")
        db.tweets.update_one({'id': tw['id']}, {'$set': {'deleted': True}})
    handle_twitter_error(db, api, e, tw['user']['id'], 'statuses/show/:id', None)
  return


def add100(db, api, twitterapi, idlist):
  if verbose(): print('another {}'.format(len(idlist)))
  try:
    tweets = api.statuses_lookup(id_=idlist, trim_user=True)
  except tweepy.error.RateLimitError:
    x = twitterapi.CheckRateLimit('/statuses/lookup').reset
    if verbose(): print("rate limit, wait {} seconds".format(x))
    time.sleep(x)
    add100(db, api, twitterapi, idlist)
    return
  except tweepy.error.TweepError as e:
    if verbose(): print('other error {}'.format(str(e)))
    time.sleep(2)
    return
  bulk = db.tweets.initialize_unordered_bulk_op()
  for tweet in tweets:
    j1 = tweet._json
    tw = twitter.Status.NewFromJsonDict(j1)
    j2 = pack_tweet(db, tw)
    bulk.find({'id': tw.id}).update({'$unset': {'deleted':1, 'truncated':1}})
    bulk.find({'id': tw.id}).upsert().update({'$set': j2})
    idlist.remove(tw.id)
  for i in idlist:
    if verbose():
      print('tweet {} not found'.format(i))
    bulk.find({'id':i}).upsert().update({'$set': {'deleted': True}})
  sys.stdout.flush()
  bulk.execute()
  return idlist


def repopulate(db, api, twitterapi, uid=None, skip=False):
  cont=True
  while(cont):
    idlist = []
    cont = False
    if uid is None:
      q = db.tweets.find({'lang': config.lang, 'truncated': True, 'deleted': None}).batch_size(20)
      #q = db.tweets.find({'text': {'$regex': 'http'}, 'urls': {'$exists': 0}}).limit(100)
    else:
      q = db.tweets.find({'user.id': uid, 'truncated': True, 'deleted': None}).batch_size(2000)
      #q = db.tweets.find({'user.id': uid, 'text': {'$regex': 'http'}, 'deleted': None, 'urls': {'$exists': 0}}).limit(100)
    if skip:
      q = q.skip(2000)
    if verbose():
      q = Bar("Processing:", max=db.tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(q)
    for tw in q:
      i = tw['id']
      if is_suspended(db, tw['user']['id']):
        if verbose(): print("ignore suspended")
        continue
      if is_protected(db, tw['user']['id']):
        #print("ignore protected")
        continue
      if is_dead(db, tw['user']['id']):
        #print("ignore dead")
        continue
      print(tw['text'])
      #idlist.append(i)
      add1(db, twitterapi, tw)
      cont = True


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('-a', '--all', action='store_true', dest='all', default=False, help='Try all users')
  parser.add_option('-s', '--skip', action='store_true', dest='skip', default=False, help='Skip 1000 tweets in search. For use with second parallel crawler.')
  parser.add_option('--id', action='store_true', dest='ids', default=False, help='Input is user id.')
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='Make noise.')
  (options, args) = parser.parse_args()

  auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
  auth.set_access_token(config.access_token, config.access_token_secret)
  api = tweepy.API(auth)
  verbose(options.verbose)
  db, twitterapi = init_state(use_cache=True, ignore_api=False)
  if options.all:
    repopulate(db, api, twitterapi, None, options.skip)
  else:
    for userstr in args:
      u = lookup_user(db, uid=int(userstr)) if options.ids else lookup_user(db, uname=userstr)
      if u is None:
        print("unknown user", userstr)
        continue
      uid = u['id']
      if verbose(): print('repopulate id {}'.format(uid))
      repopulate(db, api, twitterapi, uid, options.skip)

