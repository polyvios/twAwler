#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
List all users that have quoted tweets of the given user.
Output is edges in "quoter-id user-id" syntax: direction of "quotes" to the right.
"""

import sys
import optparse
import unicodecsv
import dateutil.parser
from collections import Counter
from twkit.utils import *
from twkit.analytics.stats import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--addusers", action="store_true", dest="addusers", default=False, help="Add all quoters to tracked users.")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names.")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("--greek", action="store_true", dest="greek", default=False, help="Only Greek ones.")
  parser.add_option("--common", action="store_true", dest="common", default=False, help="Only common to all given users.")
  parser.add_option("--before", action="store", dest="before", default=False, help="Before given date.")
  parser.add_option("--after", action="store", dest="after", default=False, help="After given date.")
  parser.add_option("--inv", action="store_true", dest="inv", default=False, help="Inverse query: look for users quoted by the given user instead.")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state(use_cache=False, ignore_api=not options.addusers)

  criteria = {}
  if options.before:
    criteria['$lte'] = dateutil.parser.parse(options.before)
  if options.after:
    criteria['$gte'] = dateutil.parser.parse(options.after)

  userlist = [x.lower().replace("@", "") for x in args]
  common = None
  for user in userlist:
    uname = None if options.ids else user
    uid = int(user) if options.ids else None
    u = lookup_user(db, uid, uname)
    if u is None:
      if verbose(): sys.stderr.write(u'Unknown user {}\n'.format(user))
      continue
    uid = u['id']
    qcnt = get_quoted(db, u['id'], criteria) if options.inv else get_quoters(db, u['id'], criteria) 
    quoters = frozenset(qcnt.keys())
    if options.common:
      if common is None: common = quoters 
      else: common &= quoters
    else:
      for f in quoters:
        if options.greek and not is_greek(db, f): continue
        print(u'{} {} {}'.format(uid, f, qcnt[f]) if options.inv else u'{} {} {}'.format(f, uid, qcnt[f]))
        if options.addusers:
          if is_dead(db, f): continue
          if is_suspended(db, f): continue
          if get_tracked(db, f): continue
          u = lookup_user(db, f)
          try:
            add_to_followed(db, f, u['screen_name'].lower(), is_protected(db, f))
          except:
            follow_user(db, api, f)
  #end for
  if options.common:
    for f in common:
      if options.greek and not is_greek(db, f): continue
      print(u'{}'.format(f))

