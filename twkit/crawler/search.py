#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Get a list of words and look them up in the search API and add them to
the database.  For each tweet seen, check if the author is followed;
can be used to discover new users.
"""

import sys
import json
import optparse
from datetime import datetime
from pymongo.errors import BulkWriteError,InvalidOperation
from twkit.utils import *

def search_for_terms(db, api, term, options, max_id=None, max_req=-1):
  count = 0;
  posts = []
  j = None
  while max_req != 0:
    sys.stdout.flush()
    max_req -= 1
    try:
      posts = api.GetSearch(
        term=term.decode('utf-8'),
        max_id=max_id,
        count=100,
        result_type="recent",
        since=options.after,
        until=options.before,
        include_entities=True,
      )
    except twitter.TwitterError as e:
      if verbose(): print u"exception for {} {}".format(term, e).encode('utf-8')
      repeatf = lambda x: search_for_terms(db, api, term, options, max_id)
      handle_twitter_error(db, api, e, None, 'search/tweets', repeatf)
      return
    except:
      if verbose(): print u"some other error, retrying", sys.exc_info(),
      time.sleep(2)
      continue
    bulk = db.tweets.initialize_unordered_bulk_op()
    for s in posts:
      if max_id == None or max_id > s.id:
        max_id = s.id -1
      j = pack_tweet(db, s)
      try:
        bulk.insert(j)
        count += 1
      except:
        if verbose(): print "some issue", j, sys.exc_info()[0]
        pass
      if options.text: print j['text']
      uid = j['user']['id']
      if options.add:
        follow_user(db, api, uid)
        if 'retweeted_status' in j:
          uid = j['retweeted_status']['user']['id']
          follow_user(db, api, uid)
      sys.stdout.flush()
    try:
      bulk.execute()
    except BulkWriteError as bwe:
      if verbose(): print "Errors:", bwe.message
      pass
    except InvalidOperation as e:
      if verbose(): print "Invalid op:", e.message
      pass
    if len(posts) == 0: break
  if(count > 0):
    print "Found {} tweets".format(count)
    if j: print "earliest date seen: {}".format(j.get("created_at", datetime.utcnow()))
  else:
    print "no tweets found"
  sys.stdout.flush()
  return



if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("--add", action="store_true", dest="add", default=False, help="Track all discovered users")
  parser.add_option("--text", action="store_true", dest="text", default=False, help="Print tweet text")
  parser.add_option("--max-req", action="store", dest="req", type='int', default=-1, help="How many requests per term, with 100 tweets per request, max.")
  parser.add_option("-b", "--before", action="store", dest="before", default=False, help="Before given date.")
  parser.add_option("-a", "--after", action="store", dest="after", default=False, help="After given date.")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state(use_cache=False)

  for term in args:
    search_for_terms(db, api, term, options, max_id=None, max_req=options.req)

  print "done"


