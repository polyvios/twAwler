#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Scan a given user's last favorite tweets.
Keeps asking for older favorites, until a set threshold of 190
previously seen favorites is reached.
"""

import sys
import optparse
from pymongo.errors import CursorNotFound
from progress.bar import Bar
from twkit.utils import *

def load_past_favs(db, api, userid, max_req=-1):
  cdata = db.crawlerdata.find_one({ 'id' : userid })
  fav = cdata.get('fav_scanned') if cdata else None
  if cdata is not None and cdata.get('fav_scanned', False):
    #if verbose(): print("cached")
    return 0
  total = 0
  retry = True
  maxid = None
  known = 0
  while retry and known <= 190:
    retry = False
    try:
      favs = api.GetFavorites(user_id=userid, count=200, max_id=maxid)
    except twitter.TwitterError as e:
      handle_twitter_error(db, api, e, userid, 'favorites/list', None)
      continue
    for tw in favs:
      twid = tw.id
      edge = {'user_id': userid, 'tweet_id': twid}
      result = db.favorites.update_one(edge, {'$set': edge}, upsert=True)
      if result.matched_count:
        known += 1
      elif result.upserted_id:
        total = total + 1
      else:
        print("neither known nor inserted, something's wrong")
      if maxid is None or maxid >= twid: maxid = twid - 1
      retry=True 
    print('.', end= ' ')
    sys.stdout.flush()
  print("found {} new favs".format(total))
  cdata = db.crawlerdata.update_one({ 'id' : userid }, {'$set': {'fav_scanned': True}}, upsert=True)
  return 1



if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is ids, not usernames")
  parser.add_option("--all", action="store_true", dest="all", default=False, help="Scan all tracked users")
  parser.add_option("--skip", action="store", type="int", dest="skip", default=0, help="Skip given number of users")
  parser.add_option("--reset", action="store_true", dest="reset", default=False, help="Reset scan all tracked users")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="make noise.")
  parser.add_option("-f", "--force", action="store_true", dest="force", default=False, help="Force rescan.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, api = init_state()

  if options.reset:
    print("resetting all. rerun to scan all again.")
    db.crawlerdata.update_many({}, {'$set': {'fav_scanned': False}})
    sys.exit(0)

  foundnew = 0
  if options.all:
    skip = options.skip;
    while True:
      try:
        users = db.following.find().batch_size(50)
        if skip > 0:
          users.skip(skip)
        count = db.following.count() - skip
        if verbose():
          users = Bar("Processing:", max=count, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(users)
        for u in users:
          foundnew += load_past_favs(db, api, u['id'])
          skip += 1
        sys.exit(foundnew)
      except CursorNotFound as e:
        print("exception, restarting", e)
        continue
      
  for user in [x.lower().replace("@", "") for x in args]:
    uname = None if options.ids else user
    uid = int(user) if options.ids else None
    print("scanning {}".format(user), end= ' ')
    u = lookup_user(db, uid=uid, uname=uname)
    if u is None:
      print("could not find user locally")
      continue
    userid = u['id']
    if options.force:
      cdata = db.crawlerdata.update_one({ 'id' : userid }, {'$unset': {'fav_scanned': 1}})
    foundnew += load_past_favs(db, api, userid)
  sys.exit(foundnew)
