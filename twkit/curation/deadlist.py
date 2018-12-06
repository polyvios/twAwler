#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
List all dead accounts.
"""

from twkit.utils import *

if __name__ == "__main__":
  db, _ = init_state(use_cache=False, ignore_api=True)
  for u in db.cemetery.find():
    uid = u['id']
    print uid,

    tracked = get_tracked(db, uid)
    if tracked:
      print "Following as:", tracked['screen_name_lower'],

    if is_ignored(db, uid):
      print "Ignored",

    for us in db.users.find({'id': uid}):
      print "In users as", us.get('screen_name', '<unknown>'),

    print "."
