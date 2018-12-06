#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import sys
import re
import optparse
from progress.bar import Bar
from collections import Counter
from datetime import datetime,timedelta
#from greekdict import WikiWordGraph
from sets import Set
from twkit.utils import *
from twkit.analytics.stats import *
from twkit.analytics.senti import get_word_graph

#word_graph = WikiWordGraph(crawlerdir+'data/word_graph.json')
tknzr = TweetTokenizer(strip_handles=True, reduce_len=True)

def match_cases(word1pos, word2pos):
  #gprint(word1pos)
  #gprint(word2pos)
  #print "----"
  res1 = []
  res2 = []
  for v in word2pos[1]:
    if v in word1pos[1]:
      res1.append(v)
  for v in word1pos[1]:
    if v in word2pos[1]:
      res2.append(v)
   #match1 = any(x in word1pos for x in word2pos)
  #match2 = any(x in word2pos for x in word1pos)
  #print "matching:", match1, match2
  #gprint(word1pos)
  #gprint(word2pos)
  r1 = word1pos
  r2 = word2pos
  if len(res1):
    r1 =(word1pos[0], res1)
  if len(res2):
    r2 = (word2pos[0],res2)
  return r1, r2


def process_sentence(sentence):
  for i in range(0, len(sentence)-1):
    w1 = sentence[i]
    w2 = sentence[i+1]
    w1n, w2n = match_cases(w1, w2)
    sentence[i] = w1n
    sentence[i+1] = w2n

def get_entities(db, uid, limit):
  tweets = get_user_tweets(db, uid, None)
  if limit:
    print limit
    tweets = tweets.limit(int(limit))
  for t in tweets:
    if 'retweeted_status' in t: continue
    if 'text' not in t: continue
    txt = t['text']
    print txt.encode('utf-8')
    sentence = []
    for w in tknzr.tokenize(txt):
      pos = get_word_graph().get_pos(w)
      #print u"{}".format(w).encode('utf-8'),
      #if pos: gprint(pos)
      #print u"----"
      if pos is not None and u'Συν' in pos:
        process_sentence(sentence)
        gprint(sentence)
        sentence = []
      else:
        sentence.append((w, pos))
    process_sentence(sentence)
    gprint(sentence)
  return 


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids.")
  parser.add_option("--limit", action="store", dest="limit", type="int", default=None, help="Limit to given number of tweets (for debugging).")
  parser.add_option("--stdin", action="store_true", dest="stdin", default=None, help="analyze stdin.")
  #parser.add_option("--query", action="store", dest="query", default=None, help="Custom tweet selection.")
  (options, args) = parser.parse_args()

  verbose(options.verbose)

  if options.stdin:
    for line in sys.stdin.readlines():
      sentence = []
      for w in tknzr.tokenize(line):
        pos = get_word_graph().get_pos(w)
        if pos is not None and u'Συν' in pos:
          process_sentence(sentence)
          gprint(sentence)
          sentence = []
        else:
          sentence.append((w, pos))
      process_sentence(sentence)
      gprint(sentence)
    sys.exit(0) 

  db, _ = init_state(use_cache=False, ignore_api=True)
  userlist = [x.lower().replace("@", "") for x in args]
  for user in userlist:
    uid = long(user) if options.ids else None
    uname = None if options.ids else user
    u = get_tracked(db, uid, uname)
    if u == None:
      x = lookup_user(db, uid, uname)
      if x:
        u = { 'id': x['id'], 'screen_name_lower': x['screen_name'].lower() }
      else:
        print "unknown user:", uid, uname
        continue
    #user_tweets = get_user_tweets(db, u['id'], None)
    get_entities(db, u['id'], options.limit)
