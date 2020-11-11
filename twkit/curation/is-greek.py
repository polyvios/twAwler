#!/usr/bin/python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
  Compute the percentage of followers, friends, and followers|friends
  that are classified as Greek.
"""
import sys
import optparse
from progress.bar import Bar
from collections import Counter
from datetime import datetime,timedelta
from twkit import *
from twkit.analytics.stats import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids.")
  (options, args) = parser.parse_args()
  if len(args) == 0:
    parser.print_help()
    sys.exit(1)
  verbose(options.verbose)
  db, api = init_state(use_cache=False, ignore_api=True)
  userlist = [x.lower().replace("@", "") for x in args]
  if verbose():
    print(u'{:<18}\t{}\t{}\t{}\t{}\t{}\t{:<15}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{:>5}\t{:>5}\t{}'.format(
      'id',
      'is_gr',
      'trckd',
      'dead',
      'susp',
      'prot',
      'screen_name',
      'seen_fr',
      'seen_fo',
      'fr|fo',
      'gr_fr',
      'gr_fo',
      'gr_frfo',
      'gr_fr%',
      'gr_fo%',
      'gr_frfo%',
      'url'))
    print(u'-'*180)

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
    v = db.uservectors.find_one({'id': u['id']})
    if v is None: 
      fill_follower_stats(db, u)
    else:
      u = v
    print(u'{:<18}\t{}\t{}\t{}\t{}\t{}\t{:<15}\t{:>7}\t{:>7}\t{:>5}\t{:>5}\t{:>5}\t{:>7}\t{:>6}\t{:>6.1f}\t{:>8.1f}\thttps://www.twitter.com/{}'.format(
      u['id'],
      is_greek(db, u['id']),
      get_tracked(db, u['id']) is not None,
      is_dead(db, u['id']),
      is_suspended(db, u['id']),
      is_protected(db, u['id']),
      u['screen_name_lower'],
      u['seen_fr'],
      u['seen_fo'],
      u['fr_or_fo'],
      u['gr_fr'],
      u['gr_fo'],
      u['gr_fr_fo'],
      u['gr_fr_pcnt'],
      u['gr_fo_pcnt'],
      u['gr_fr_fo_pcnt'],
      u['screen_name_lower']))
    
