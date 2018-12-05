#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Mark the given user as suspended.
"""

import sys
from pymongo import MongoClient
from bson.json_util import loads
from datetime import datetime
from twkit.utils import *

if __name__ == "__main__":
  db, api = init_state()
  userlist = [x.lower().replace("@", "") for x in sys.argv[1:]]
  for username in userlist:
    userid = None
    u = db.following.find_one( { 'screen_name_lower' : username } )
    if u != None:
      db.following.delete_one(u)
      print "stopped following"
      sys.stdout.flush()
      userid = u['id']
    if userid == None:
      u = db.users.find_one({'screen_name_lower': username})
      if u != None:
        userid = u['id']
      else:
        print "could not find user locally"
        sys.stdout.flush()
    if userid == None: continue
    if is_dead(db, userid):
      print "user dead, abort", userid, username
      sys.stdout.flush()
      continue
    if is_ignored(db, userid):
      print "already ignored", userid, username
      sys.stdout.flush()
      continue
    try:
      db.suspended.insert_one({'id': userid})
      print username, userid, "added to suspended set"
      sys.stdout.flush()
    except:
      print "cannot insert suspended", userid, username
      sys.stdout.flush()
      pass
