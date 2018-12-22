#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Create a graph of the usage of a word and save the data in a csv file.
"""

import optparse
from progress.bar import Bar
from datetime import datetime, timedelta
from collections import Counter
from twkit.utils import *
from twkit.analytics.senti import *
from twkit.analytics.stats import *
from nltk.tokenize import TweetTokenizer
from dateutil.relativedelta import relativedelta


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  parser.add_option("--video", action="store_true", dest="video", default=False, help="Output is animation.")
  parser.add_option("-b", "--before", action="store", dest="before", default=None, help="Before given date.")
  parser.add_option("-a", "--after", action="store", dest="after", default=None, help="After given date.")
  parser.add_option("-m", "--month", action="store_true", dest="month", default=False, help="Group per month.")
  parser.add_option("-o", "--output", action="store", dest="filename", default=None, help="Set output filename label.")
  parser.add_option("-u", "--user", action="store", dest="user", default=None, help="Only scan one user's tweets.")
  parser.add_option("--dump", action="store", dest="dump", default=None, help="Write all tweet texts into a file.")
  parser.add_option("--nourl", action="store_true", dest="nourl", default=False, help="Skip all tweets that include a URL.")
  parser.add_option("--sentiment", action="store_true", dest="sentiment", default=False, help="Compute sentiment of tweets that match.")
  (options, args) = parser.parse_args()

  db, api = init_state(True, False)
  verbose(options.verbose)

  criteria = {}
  if options.before:
    criteria['$lte'] = dateutil.parser.parse(options.before)
    before = criteria['$lte']
  else:
    before = datetime.utcnow()
  if options.after:
    criteria['$gte'] = dateutil.parser.parse(options.after)
    after = criteria['$gte']
  else:
    after = datetime.utcnow() - timedelta(days=3650)

  words = [x.decode('utf-8').lower() for x in args if u'#' not in x.decode('utf-8')]

  tknzr = TweetTokenizer(strip_handles=True, reduce_len=True)
  word_graph = WikiWordGraph('data/word_graph.json')
  if options.sentiment:
    sentiment_analysis = GrSentimentAnalysis("greekdata/lexicon.csv", word_graph)
  entity_analysis = EntityAnalysis({w:[] for w in words}, word_graph)

  if options.dump: dumpfile = open(options.dump, "w")
  cnt = Counter()                       # total tweets that match, per day
  ecnt = defaultdict(lambda: Counter()) # tweets per entity, per day
  grcnt = Counter()                     # total tweets in greek, per day
  if options.sentiment:
    daily_entity_sentiment = defaultdict(lambda: defaultdict(lambda: (0.0, 0.0, 0)))

  if options.user:
    u = lookup_user(db, uname=options.user)
    tweets = get_user_tweets(db, u['id'], criteria)
  else:
    tweets = get_all_tweets(db, criteria, batch=100)
  for tweet in tweets:
    if 'text' not in tweet: continue
    if options.nourl and "http" in tweet['text']: continue
    #words_exact = tknzr.tokenize(tweet['text'].lower())
    #words_wiki = [x for w in words_exact for x in word_graph.get(w)]
    d = tweet['created_at']
    if options.month:
      day = d.replace(day=1,hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    else:
      day = d.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    if tweet.get(u'lang') == config.lang:
      grcnt[day] += 1

    entlist = entity_analysis.analyze(tweet['text'])
    if len(entlist):
      #gprint(entlist)
      cnt[day] += 1
    for e in entlist:
      ecnt[day][e] += 1
      if options.sentiment:
        pos, neg = sentiment_analysis.analyze(tweet['text'])
        daily_entity_sentiment[day][e] = tuple_add(daily_entity_sentiment[day][e], (pos, neg, 1))
      if options.dump: dumpfile.write((tweet['text']+u'\n').encode('utf-8'))
      #break # break inner, continue outer loop with next tweet
  if options.dump: dumpfile.close()

  first = min(grcnt.keys()) if len(grcnt) else before.replace(day=1,hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
  last = max(grcnt.keys()) if len(grcnt) else after.replace(day=1,hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
  day = relativedelta(months=1) if options.month else relativedelta(days=1)
  if verbose(): print first, last
  while first <= last:
    cnt[first] = cnt[first] + 0
    grcnt[first] = grcnt[first] + 0
    first = first + day

  now = datetime.utcnow().isoformat()
  fname = options.filename if options.filename else words[0]+now
  percent = {}
  norm = {}
  for d in grcnt:
    percent[d] = 1.0 * cnt[d] / max(grcnt[d], 1.0)
  if len(percent):
    avg = numpy.mean(percent.values())
    if avg == 0.0: avg = 1.0
  else:
    avg = 1.0
  for d in grcnt:
    norm[d] = percent[d] / avg
  with open(u'data/'+fname+'.csv','w') as f:
    f.write(u'Date,Greek,Matching,Percent,Normalized')
    for w in words:
      f.write(u',{}'.format(w).encode('utf-8'))
    if options.sentiment:
      for e in entity_analysis.entities:
        f.write(u',{}_pos,{}_neg'.format(e,e).encode('utf-8'))
    f.write(u'\n')
    for d in sorted(cnt):
      f.write(u'{},{},{},{},{}'.format(d.date(),grcnt[d],cnt[d],percent[d],norm[d]))
      for w in words:
        f.write(u',{}'.format(ecnt[d][w]))
      if options.sentiment:
        for e in entity_analysis.entities:
          s = daily_entity_sentiment[d][e]
          if s[2]:
            f.write(u',{},{}'.format(s[0]/s[2], s[1]/s[2]))
      f.write(u'\n')



#end main
