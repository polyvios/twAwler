#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Get a list of words and create a stream of tweets on those words.
For each tweet seen, check if the author is followed and if not, print
their ID out to stdout.
Can be used to discover new users.
"""

import sys
import json
import optparse
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from twkit.utils import *
import config

#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self, db, options):
      self.db = db
      self.options = options

    def on_data(self, data):
        j = pack_tweet(db, data)
        #self.db.tweets.insert(j)
        if j.get('lang', 'en') != config.lang: return True
        if 'retweeted_status' in j:
          print j['retweeted_status']['user']['id']
        else:
          print j['user']['id']
        if self.options.text:
          print j['text']
        sys.stdout.flush()
        return True

    def on_error(self, status):
        print "error: {}".format(status)


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("-a", "--all", action="store_true", dest="all", default=False, help="Get all greek language tweets")
  parser.add_option("--lang", action="store_true", dest="lang", default=config.lang, help="Set language")
  parser.add_option("--text", action="store_true", dest="text", default=config.lang, help="Print tweet text")
  (options, args) = parser.parse_args()

  #This handles Twitter authetification and the connection to Twitter Streaming API
  db, api = init_state(use_cache=False)
  l = StdOutListener(db, options)
  auth = OAuthHandler(config.consumer_key, config.consumer_secret)
  auth.set_access_token(config.access_token, config.access_token_secret)
  stream = Stream(auth, l)

  if options.all:
    stream.sample(languages=[options.lang])
  else:
    #This line filter Twitter Streams to capture data by the keywords: 'python', 'javascript', 'ruby'
    stream.filter(track=[x.decode('utf-8').lower() for x in sys.argv[1:]], languages=[options.lang])
