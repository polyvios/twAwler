#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
Find any user information based on the user id by looking into tweets
that mention the user, and insert into the users collection.
This is sometimes useful for users that are deleted or suspended.
'''

import sys
import optparse
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <userid> [<userid> ...]')
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, _ = init_state(use_cache=False, ignore_api=True)

  userlist = (int(x) for x in args)

  for userid in userlist:
    look_for_mentioned_id(db, userid)
