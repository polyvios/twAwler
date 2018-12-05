#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import sys
from twkit.utils import *

if __name__ == '__main__':
  db, api = init_state()

  if len(sys.argv) < 2:
    print "Usage: {} <ids>".format(sys.argv[0])
    sys.exit(1)

  userlist = sys.argv[1:]
  for useridstr in userlist:
    userid = long(useridstr)
    bury_user(db, userid)
