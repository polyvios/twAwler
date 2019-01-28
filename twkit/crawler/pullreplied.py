#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
This tool crawls the database for missing references to tweets via the
"reply to" field, and crawls the parent tweet in the thread.
'''

import optparse
import tweepy
import config
from progress.bar import Bar
from twkit.utils import *
from twkit.crawler.freq import *
from twkit.curation.repopulate import add100

def pull_favorited(db, api, twitterapi):
  favs = db.favorites.find({'pulled': None}).batch_size(100)
  idlist = []
  if verbose():
    favs = Bar("Processing:", max=favs.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(favs)
  for f in favs:
    twid = f['tweet_id']
    if db.tweets.find_one({'id': twid}) is not None:
      db.favorites.update(f, {'$set': {'pulled': True}})
      continue
    idlist.append(twid)
    if verbose(): print " ", twid
    if len(idlist) == 100:
      add100(db, api, twitterapi, idlist)
      idlist = []
  if len(idlist):
    add100(db, api, twitterapi, idlist)


def pull_replied(db, api, twitterapi):
  #TODO: refine this to not be a full scan. see $lookup.
  tweets = db.tweets.find(
    {'in_reply_to_status_id': {'$gt': 0}, 'reply_pulled': None},
    {'in_reply_to_status_id': 1, 'in_reply_to_user_id': 1}
  )
  if verbose():
    tweets = Bar("Processing:", max=tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  idlist = []
  for t in tweets:
    twid = t['in_reply_to_status_id']
    if twid is None:
      db.tweets.update(t, {'$unset': {'in_reply_to_status_id': 1}})
      print "point 1: this should never? be reached, i think"
      continue
    #if get_tracked(db, uid=t['user']['id']) is None or not is_greek(db, uid=t['user']['id']): continue
    orig = db.tweets.find_one({'id': twid})
    if orig:
      db.tweets.update(t, {'$set': {'reply_pulled': True}})
      if orig.get('deleted', False):
        if orig.get('user') is None or orig['user'].get('id') is None or t['in_reply_to_user_id'] != orig['user']['id']:
          db.tweets.update({'id': twid}, {'$set': {'user.id': t['in_reply_to_user_id']}})
      continue
    idlist.append(twid)
    if verbose(): print " ", twid
    if len(idlist) == 100:
      add100(db, api, twitterapi, idlist)
      idlist = []
  if len(idlist):
    add100(db, api, twitterapi, idlist)

def pull_quoted(db, api, twitterapi):
  tweets = db.tweets.find(
    {'quoted_status_id': {'$gt': 0}, 'quote_pulled': None},
    {'quoted_status_id': 1, 'quoted_status': 1, 'id': 1}
  )
  if verbose():
    tweets = Bar("Processing:", max=tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  idlist = []
  for t in tweets:
    twid = t['quoted_status_id']
    if twid is None:
      db.tweets.update(t, {'$unset': {'quoted_status_id': 1}})
      print "point 1: this should never? be reached, i think"
      continue
    #if get_tracked(db, uid=t['user']['id']) is None or not is_greek(db, uid=t['user']['id']): continue
    orig = db.tweets.find_one({'id': twid})
    if orig:
      if 'quoted_status' not in t:
        del orig['_id']
        db.tweets.update_one(t, {'$set' : { 'quoted_status' : orig }})
        if verbose(): print u"filled in tweet {} into {}".format(twid, t['id'])
      db.tweets.update(t, {'$set': {'quote_pulled': True}})
      continue
    if twid not in idlist:
      idlist.append(twid)
    if verbose(): print " ", twid
    if len(idlist) >= 100:
      add100(db, api, twitterapi, idlist)
      idlist = []
  if len(idlist):
    add100(db, api, twitterapi, idlist)


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  parser.add_option('-q', '--quotes', action='store_true', dest='quotes', default=False, help='Pull quotes instead of replies')
  parser.add_option('-f', '--favorites', action='store_true', dest='favorites', default=False, help='Pull favorited tweets')
  (options, args) = parser.parse_args()

  auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
  auth.set_access_token(config.access_token, config.access_token_secret)
  api = tweepy.API(auth)
  verbose(options.verbose)
  db, twitterapi = init_state(use_cache=True, ignore_api=False)
  if options.quotes:
    pull_quoted(db, api, twitterapi)
  elif options.favorites:
    pull_favorited(db, api, twitterapi)
  else:
    pull_replied(db, api, twitterapi)
