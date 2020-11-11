#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Get all list members of a given list
"""

import sys
import optparse
from datetime import datetime
from progress.bar import Bar
from collections import Counter
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Contain search to greek users")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, _ = init_state(ignore_api=True)

  lists = [int(x) for x in args]
  if verbose():
    lists = Bar("Processing:", max=len(lists), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(lists)
  for list_id in lists:
    l = db.lists.find_one({'id': list_id})
    if options.greek and not is_greek(db, l['owner_id']): continue
    members = db.listmembers.find({'list_id': list_id})
    seenmembers = set()
    for m in members:
      uid = m['user_id']
      if uid in seenmembers: continue
      if options.greek and not is_greek(db, uid): continue
      seenmembers.add(uid)
      u = lookup_user(db, uid)
      if verbose():
        print(u"{} in {}".format(id_to_userstr(db, uid), l['uri']))
      else:
        print(u"{} {}".format(uid, list_id))

