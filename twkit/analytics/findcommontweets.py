#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2017-2020 Polyvios Pratikakis
# based on initial design by Alex Shevtsov
# polyvios@ics.forth.gr
###########################################

"""
Compute copying events, using "synchrotrap" algorithm. Used in Alex's paper.
"""

import datetime, sys, time
from isoweek import Week
from nltk.tokenize import TweetTokenizer
from pymongo import MongoClient
import optparse
import dateutil.parser
from twkit import *
import config

Time_window = 600 # in seconds
Threshold = 0.8 #80% bag-of-words jaccard similarity
TwTk = TweetTokenizer(strip_handles=True)
db, _ = init_state(use_cache=False, ignore_api=True)


def jaccard(a, b):
  return 1.0 * len(a & b) / len(a | b)


def compare_one(tweet, tweets):
  matched = [t for t in tweets if jaccard(tweet['bow'], t['bow']) >= Threshold and t['user']['id'] != tweet['user']['id']]
  return [(tweet, matched)]


def scan_interval(start_date):
  mid_date = start_date + datetime.timedelta(seconds=Time_window/2)
  end_date = start_date + datetime.timedelta(seconds=Time_window)
  tweets = list(db.tweets.find(
    {'created_at': {'$gte' : start_date, '$lt' : end_date}, 'lang': config.lang, 'retweeted_status': None, 'text': {'$gte': ''} },
    {'id': 1, 'created_at': 1, 'user.id': 1, 'text': 1, 'urls':1}
  ).sort('created_at',1))
  tokenized = [dict(t, **{'id': t['id'], 'bow': set(TwTk.tokenize(t['text']))}) for t in tweets if u'RT' not in t['text']]
  edges = [edge for i in range(0, len(tokenized)) for edge in compare_one(tokenized[i], tokenized[i+1:]) if edge[1] != [] and tokenized[i]['created_at'] < mid_date ]
  #maybe filter tweets with this, but probably unnecessary...
  #keys = ['id', 'created_at', 'user', 'text', 'urls']
  return edges


#def main(firstweek, lastweek):
def main(start_date, end_date):
  #start_date = datetime.datetime.combine(firstweek.monday(), datetime.time())
  #lastweek += 1 # lastweek is given inclusive, increase by one to get start of following week
  #end_date = datetime.datetime.combine(lastweek.monday(), datetime.time()) + datetime.timedelta(seconds=Time_window/2)
  while start_date < end_date:
    if verbose(): print(u"Scanning {}".format(start_date))
    edges = scan_interval(start_date)
    start_date += datetime.timedelta(seconds=Time_window/2)
    for (t, copied) in edges:
      db.botsperweek.update_one({'id': t['id']},
        {'$set': {
          'id': t['id'],
          'user_id': t['user']['id'],
          'text': t['text'],
          'event_start': t['created_at'],
          'user_ids': [tw['user']['id'] for tw in copied],
          'timestamps': [tw['created_at'] for tw in copied],
          'tweet_ids': [tw['id'] for tw in copied],
          'same_found': len(copied),
          'time_diff': (copied[-1]['created_at'] - t['created_at']).total_seconds()
        }}, upsert=True)

if __name__ == '__main__':
  parser = optparse.OptionParser(usage=u'Usage: %prog [options]\nExample: %prog --before 2017W07 --after 2017W02')
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  parser.add_option('-b', '--before', action='store', dest='before', default='2019W52', help='End on given isoweek, inclusive.')
  parser.add_option('-a', '--after', action='store', dest='after', default='2006W09', help='Start on given isoweek.')
  parser.add_option('--clear', action='store_true', dest='clear', default=False, help='DELETE all previous contents of the output collection.')
  #parser.add_option('-p', '--processes', action='store', type=int, dest='processes', default=1, help='How many processes to use to parallelize.')
  (options, args) = parser.parse_args()

  verbose(options.verbose)

  before = None
  after = None
  if options.clear:
    db.botsperweek.delete_many({})
    sys.exit(0)
  if options.before:
    #before = Week.fromstring(options.before)
    before = dateutil.parser.parse(options.before)
  if options.after:
    #after = Week.fromstring(options.after)
    after = dateutil.parser.parse(options.after)

  main(after, before)
