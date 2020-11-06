#!/usr/bin/env python333
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Mark the users with the given IDs as suspended.
"""

import sys
from twkit.utils import *

if __name__ == "__main__":
  db, api = init_state()
  userlist = sys.argv[1:]
  for uidtxt in userlist:
    suspend(db, int(uidtxt))

