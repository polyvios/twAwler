#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################


"""
Scans all self references in user tweets and counts how many of them
included an adjective or noun in the masculine/feminine gender.
"""

import re
import sys
import optparse
from progress.bar import Bar
from collections import Counter
from twkit.utils import *
from twkit.analytics.stats import *
from twkit.analytics.senti import get_word_graph

def get_gender(db, uid):
  male = 0
  female = 0
  locationarticles = [ u'στο', u'στην', u'στη', u'στα', u'στους', u'στις', u'σε', u'στον' ]
  pattern = re.compile(u'(?:ειμαι|είμαι|ήμουν|ήμουνα|ημουν):? ([Α-ωάώίύέόήΐϊϋ]*)', re.I)
  tweets = get_user_tweets(db, uid, None)
  #print("got {} tweets for {}".format(tweets.count(), uid))
  for t in tweets:
    if 'retweeted_status' in t: continue
    if 'text' not in t: continue
    txt = t['text']
    detxt = deaccent(txt).lower()
    if not all(w not in detxt for w in negationwords): continue
    m = pattern.search(txt)
    if m is None: continue
    nextword = m.group(1)
    if deaccent(nextword).lower() in locations: continue
    if deaccent(nextword).lower() in locationarticles: continue
    pos = get_word_graph().get_pos(nextword)
    #print(nextword,)
    #print(pos)
    if pos is None: continue
    for x in pos:
      if u'αρσ' in x:
        if verbose(): print(u"male: {}".format(nextword))
        male += 1
      if u'θηλ' in x:
        if verbose(): print(u"female: {}".format(nextword))
        female += 1
  total = male + female
  return {
    'male': 100.0 * male/total if total > 0 else 0.0,
    'female': 100.0 * female/total if total > 0 else 0.0
  }


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  if len(args) == 0:
    parser.print_help()
    sys.exit(1)
  db, _ = init_state(use_cache=False, ignore_api=True)
  userlist = [x.lower().replace("@", "") for x in args]
  for user in userlist:
    uid = int(user) if options.ids else None
    uname = None if options.ids else user
    u = get_tracked(db, uid, uname)
    if u == None:
      x = lookup_user(db, uid, uname)
      if x:
        u = { 'id': x['id'], 'screen_name_lower': x['screen_name'].lower() }
      else:
        print("unknown user:", uid, uname)
        continue
    #user_tweets = get_user_tweets(db, u['id'], None)
    g = get_gender(db, u['id'])
    print(g)
