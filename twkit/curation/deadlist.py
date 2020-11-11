#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
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
    print(uid, end=' ')

    tracked = get_tracked(db, uid)
    if tracked:
      print("Following as:", tracked['screen_name_lower'], end=' ')

    if is_ignored(db, uid):
      print("Ignored", end=' ')

    for us in db.users.find({'id': uid}):
      print("In users as", us.get('screen_name', '<unknown>'), end=' ')

    print(".")
