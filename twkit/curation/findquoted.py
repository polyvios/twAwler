#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import sys
import re
import tweepy
import twitter
from progress.bar import Bar
import optparse
from datetime import datetime
from twkit.utils import *
from twkit.analytics.stats import *
from pymongo.errors import CursorNotFound
import config

quote_pattern = re.compile(r'^https://twitter.com/([^/]*)/status/([0-9]*)$')

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state(True)
  tweets = db.tweets.find({'lang': config.lang, 'urls': {'$exists': 1}, 'quoted_status_id': None, 'retweeted_status': None})
  if verbose():
    tweets = Bar("Loading tweets:", max=db.tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  for tw in tweets:
    for url in tw.get('urls',[]):
      lurl = unshort_url(db, url)
      m = quote_pattern.match(lurl)
      if m:
        uname = m.group(1)
        twid = m.group(2)
        print u'found'
        print u'uname : {}'.format(uname)
        print u'id    : {}'.format(twid)
        print u'quoter: {}'.format(tw['id'])
        print u'-----'
        db.tweets.update_one(tw, {'$set': {'quoted_status_id': twid}})
