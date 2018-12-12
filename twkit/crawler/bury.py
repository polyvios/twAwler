#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Mark a given user id as dead.
"""

import sys
from twkit.utils import *

if __name__ == '__main__':
  db, api = init_state(ignore_api=True)

  if len(sys.argv) < 2:
    print "Usage: {} <ids>".format(sys.argv[0])
    sys.exit(1)

  userlist = sys.argv[1:]
  for useridstr in userlist:
    userid = long(useridstr)
    bury_user(db, userid)
