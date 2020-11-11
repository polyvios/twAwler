#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
scan all seen retweeters of a tweet and list them sorted by account creation date
use --user to have argument be username instead
'''

import optparse
from collections import Counter
from twkit.utils import init_state, lookup_user, verbose
from twkit.analytics.stats import get_user_retweets
from datetime import datetime, timedelta

userfeatures = ['id', 'created_at']

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  parser.add_option('-u', '--user', action='store_true', dest='user', default=False, help='Input is user, scan all retweeters')
  parser.add_option('--id', action='store_true', dest='ids', default=False, help='Input is user id not screen name')
  #parser.add_option('-o', '--output', action='store', dest='filename', default='retweeters.csv', help='Where to output')
  #parser.add_option('-f', '--feature', action='append', dest='features', default=['id', 'created_at'], help='Include extra features from the user document')
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, _ = init_state(ignore_api=True)

  creation_dates = Counter()
  retweeters = Counter()
  if options.user:
    for userstr in args:
      uid = int(userstr) if options.ids else None
      uname = None if options.ids else userstr
      u = lookup_user(db, uid, uname)
      if u is None:
        print(u'Unknown user {}'.format(userstr))
      uid = u['id']
      uname = u['screen_name'].lower()
      for rt in get_user_retweets(db, uid, None, None):
        retweeter_id = rt['user']['id']
        retweeters[retweeter_id] += 1
        if retweeters[retweeter_id] > 1:
          #don't count a user's creation date after their second RT seen
          continue
        retweeter = lookup_user(db, retweeter_id)
        if retweeter is None or 'created_at' not in retweeter:
          print("missing retweeter: {}".format(retweeter_id))
          continue
        d = retweeter['created_at']
        creation_dates[d.date()] += 1
  else:
    for twidstr in args:
      twid = int(twidstr)
      for rt in db.tweets.find({'retweeted_status.id': twid}, {'user.id': 1}):
        retweeter_id = rt['user']['id']
        retweeters[retweeter_id] += 1
        if retweeters[retweeter_id] > 1:
          #don't count a user's creation date after their second RT seen
          continue
        retweeter = lookup_user(db, retweeter_id)
        if retweeter is None or 'created_at' not in retweeter:
          print("missing retweeter: {}".format(retweeter_id))
          continue
        print(retweeter_id, retweeter['screen_name'])
        d = retweeter['created_at']
        creation_dates[d.date()] += 1
    #    rdata = { k: retweeter[k] for k in userfeatures }
    #    vectorwriter.writerow(rdata)

  start = min(creation_dates.keys())
  end = max(creation_dates.keys())
  while start <= end:
    print(start, creation_dates[start])
    start += timedelta(days=1)
