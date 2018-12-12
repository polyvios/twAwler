#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Crawl twitter for retweeters of a given tweet id and add them to the
tracked users.
"""

import sys
import twitter
import optparse
from twkit.utils import *
from twkit.analytics.stats import get_user_tweets

def addretweeters(db, api, twid):
  if verbose():
    print u'adding retweeters of tweet {}'.format(twid)
  tweetid = long(twid)
  userids = []
  try:
    userids = api.GetRetweeters(status_id = tweetid)
    if verbose(): print u'Found {}'.format(len(userids))
  except twitter.TwitterError as e:
    handle_twitter_error(db, api, e, waitstr='/statuses/retweeters/ids')
  except:
    if verbose():
      print 'some other issue with', twid
  for userid in userids:
    follow_user(db, api, userid, wait=True, refollow=options.refollow)

if __name__ == '__main__':
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <tweet> [<tweet> ...]')
  parser.add_option('--refollow', action='store_true', dest='refollow', default=False, help='Re-follow ignored users')
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='Make noise')
  parser.add_option('-u', '--userscan', action='store_true', dest='userscan', default=False, help='Scan all user tweets')
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids, not tweet ids.")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state()

  if options.userscan:
    for user in args:
      uid = long(user) if options.ids else None
      uname = None if options.ids else user
      u = get_tracked(db, uid, uname)
      for tw in get_user_tweets(db, u['id'], None, None, batch=10):
        if tw.get('deleted', False): continue
        twid = tw['id']
        addretweeters(db, api, twid)
  else:
    for twid in args:
      addretweeters(db, api, twid)
