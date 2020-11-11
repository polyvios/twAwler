#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
This tool scans all tweets (or tweets of given user) and re-crawls
them in case we have mis-identified them as deleted.
'''

from twkit.utils import *
from twkit.crawler.freq import *
from twkit.curation.repopulate import add100
from progress.bar import Bar
import optparse
import tweepy

import config

def pull_deleted(db, api, twitterapi, uid, nort=False):
  if uid:
    tweets = db.tweets.find({'deleted': True, 'user.id': uid})
  else:
    tweets = db.tweets.find({'deleted': True})
  if verbose():
    tweets = Bar("Processing:", max=tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  idlist = []
  for t in tweets:
    twid = t['id']
    if nort and 'retweeted_status' in t: continue
    idlist.append(twid)
    if len(idlist) == 100:
      add100(db, api, twitterapi, idlist)
      idlist = []
  if len(idlist):
    add100(db, api, twitterapi, idlist)

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is id, not username.")
  parser.add_option('--nort', action="store_true", dest="nort", default=False, help="Ignore retweets.")
  (options, args) = parser.parse_args()

  auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
  auth.set_access_token(config.access_token, config.access_token_secret)
  api = tweepy.API(auth)

  verbose(options.verbose)
  db, twitterapi = init_state(ignore_api=False)

  if len(args):
    for user in args:
      uid = int(user) if options.ids else None
      uname = None if options.ids else user
      u = lookup_user(db, uid, uname)
      pull_deleted(db, api, twitterapi, u['id'] if u else None, options.nort)
  else:
    u = None
    pull_deleted(db, api, twitterapi, None, options.nort)
