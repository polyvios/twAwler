#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################


"""
User similarity computation
"""

import sys
import optparse
from datetime import datetime
from collections import Counter
from sets import Set
from twkit.utils import *
from twkit.analytics.stats import get_favoriters, get_favorited

def user_info(db, user):
  fr = set(get_friends(db, user['id']))
  fo = set(get_followers(db, user['id']))
  fr_fo_jaccard = 1.0 * len(fr & fo) / len(fr | fo)
  print "Fr-fo similarity of {}: {}".format(user['screen_name_lower'], fr_fo_jaccard)
  print "{} is not followed back by {}".format(user['screen_name_lower'], len(fr - fo))
  for i in fr - fo:
    print "  {}".format(id_to_userstr(db, i))
  print "{} does not follow back {}".format(user['screen_name_lower'], len(fo - fr))
  #for i in fo - fr:
  #  print "  {}".format(id_to_userstr(db, i))

def fr_fo_jaccard_similarity(db, user1, user2):
  fr1 = set(get_friends(db, user1['id']))
  fo1 = set(get_followers(db, user1['id']))
  fr2 = set(get_friends(db, user2['id']))
  fo2 = set(get_followers(db, user2['id']))

  if verbose():
    user_info(db, user1)
    user_info(db, user2)
  
  all_fr = fr1 | fr2
  all_fo = fo1 | fo2
  fr_jaccard = (1.0 * len(fr1 & fr2) / len(all_fr)) if len(all_fr) else float('nan')
  fo_jaccard = (1.0 * len(fo1 & fo2) / len(all_fo)) if len(all_fo) else float('nan')
  common_fr = len(fr1 & fr2)
  common_fo = len(fo1 & fo2)
  if verbose():
    print "{} followers : {}".format(user1['screen_name_lower'], len(fo1))
    print "{} followers : {}".format(user2['screen_name_lower'], len(fo2))
    print "Common       : {}".format(common_fo)
    print "Follower Jaccard Similarity {}:{}: {}".format(user1['screen_name_lower'], user2['screen_name_lower'], fo_jaccard)

    print "{} friends   : {}".format(user1['screen_name_lower'], len(fr1))
    print "{} friends   : {}".format(user2['screen_name_lower'], len(fr2))
    print "Common       : {}".format(common_fr)
    print "Friend Jaccard Similarity {}:{}  : {}".format(user1['screen_name_lower'], user2['screen_name_lower'], fr_jaccard)
  return {
    "friend_jaccard_similarity" : fr_jaccard,
    "common_friends" : common_fr,
    "follower_jaccard_similarity" : fo_jaccard,
    "common_followers" : common_fo
  }

def favorite_similarity(db, user1, user2):
  f1 = set(get_favoriters(db, user1['id']).keys())
  f2 = set(get_favoriters(db, user2['id']).keys())
  common_fav = len(f1 & f2)
  fav_jaccard = 1.0 * common_fav / len(f1 | f2)

  fd1 = set(get_favorited(db, user1['id']).keys())
  fd2 = set(get_favorited(db, user2['id']).keys())
  common_faved = len(fd1 & fd2)
  inter_faved = max(len(fd1 | fd2), 1)
  faved_jaccard = 1.0 * common_faved / inter_faved
  return {
    "favoriter_jaccard_similarity" : fav_jaccard,
    "common_favoriters": common_fav,
    "favorited_jaccard_similarity" : faved_jaccard,
    "common_favorited": common_faved
  }





if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  if len(args) == 0:
    parser.print_help()
    sys.exit(1)
  db, api = init_state(use_cache=True, ignore_api=True)
  user1 = args[0]
  userlist = args[1:]
  uid1 = long(user1) if options.ids else None
  uname1 = None if options.ids else user1
  u1 = get_tracked(db, uid1, uname1)
  if u1 == None:
    u1 = lookup_user(db, uid1, uname1)
  uname1 = id_to_userstr(db, u1['id'])
  for user2 in userlist:
    uid2 = long(user2) if options.ids else None
    uname2 = None if options.ids else user2
    u2 = get_tracked(db, uid2, uname2)
    if u2 == None:
      u2 = lookup_user(db, uid2, uname2)
    uname2 = id_to_userstr(db, u2['id'])
    sim = fr_fo_jaccard_similarity(db, u1, u2)
    favsim = favorite_similarity(db, u1, u2)
    u = dict(sim, **favsim)
    u['user1'] = uname1
    u['user2'] = uname2
    gprint(u)


