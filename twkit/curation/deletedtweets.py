#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
This tool lists all tweets marked as deleted for the given users.
Use -s switch to re-scan the existence of crawled tweets and discover
newly deleted tweets.
'''

from twkit.utils import *
from twkit.crawler.freq import *
from twkit.analytics.stats import *
from twkit.curation.repopulate import add100
from progress.bar import Bar
import optparse
import tweepy

import config

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is id, not username.")
  parser.add_option("-s", '--scan', action="store_true", dest="scan", default=False, help="Scan tweets to discover deleted ones.")
  parser.add_option('--nort', action="store_true", dest="nort", default=False, help="Ignore retweets.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, twitterapi = init_state()
  auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
  auth.set_access_token(config.access_token, config.access_token_secret)
  api = tweepy.API(auth)

  for user in args:
    uid = long(user) if options.ids else None
    uname = None if options.ids else user
    u = lookup_user(db, uid, uname)
    if u is None:
      print uid, uname, "not found"
    if options.scan:
      tweets = db.tweets.find({'user.id': u['id'], 'deleted': None}).sort('created_at', 1)
      idlist = []
      for t in tweets:
        idlist.append(t['id'])
        if len(idlist) == 100:
          idlist = add100(db, api, twitterapi, idlist)
          print u'found {} deleted'.format(len(idlist))
          idlist = []
      idlist = add100(db, api, twitterapi, idlist)
      print u'found {} deleted'.format(len(idlist))
      idlist = []

    tweets = db.tweets.find({'deleted': True, 'user.id': u['id']}).sort('created_at', 1)
    if verbose():
      tweets = Bar("Processing:", max=tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
    for t in tweets:
      if options.nort and 'retweeted_status' in t: continue
      print u'{} {} {}: {}'.format(t.get('id', '-'), t.get('created_at', None), u['screen_name_lower'], t.get('text', '<not found>')).encode('utf-8')

