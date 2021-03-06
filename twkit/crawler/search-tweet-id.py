#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
get a list of tweet ids, and look them up using twitter api
"""

import sys
import tweepy
from twkit.utils import *
import twitter
import optparse
from progress.bar import Bar
import config

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="make noise.")

  (options, args) = parser.parse_args()
  verbose(options.verbose)

  auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
  auth.set_access_token(config.access_token, config.access_token_secret)
  api = tweepy.API(auth)
  db, twitterapi = init_state(use_cache=False)

  idlist = []
  for x in Bar("Lookup:", suffix = '%(index)d/%(max)d - %(eta_td)s').iter(sys.argv[1:]):
    twid = int(x)
    old = db.tweets.find_one({'id': twid})
    #if old and 'text' in old:
    #  print(old)
    #  continue
    idlist.append(twid)

  print(idlist)
  bulk = db.tweets.initialize_unordered_bulk_op()
  cursor = api.statuses_lookup(id_=idlist, trim_user=True)
  found_at_least_one = False
  for tweet in Bar("Tweets:", suffix = '%(index)d/%(max)d - %(eta_td)s').iter(cursor):
    j1 = tweet._json
    tw = twitter.Status.NewFromJsonDict(j1)
    j2 = pack_tweet(db, tw)
    bulk.find({'id': j2['id']}).upsert().update({'$set': j2})
    idlist.remove(j2['id'])
    found_at_least_one = True

  if found_at_least_one:
    bulk.execute()

  print("Remaining, probably deleted: {}".format(idlist))
