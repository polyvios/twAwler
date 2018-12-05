#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
Find any user information based on the user id by looking into tweets
that mention the user, and insert into the users collection.
This is sometimes useful for users that are deleted or suspended.
'''

import sys
import json
import time
import re
from pymongo import MongoClient
from bson.json_util import loads
from datetime import datetime
from sets import Set
from twkit import *


db, api = init_state(False)
#client = MongoClient()
#db = client.twittergr

ignored = Set()
for i in db.ignored.find():
  ignored.add(i['id'])

if len(sys.argv) < 2:
  print "Usage: {} <ids>".format(sys.argv[0])
  sys.exit(1)

userlist = sys.argv[1:]

for idstr in userlist:
  userid = long(idstr)
  for mention in db.tweets.find({'user_mentions' : { '$elemMatch' : {u'id': userid}}}).limit(3):
    sys.stdout.flush()
    username = None
    for i in mention['user_mentions']:
      if i['id'] == userid:
        username = i['screen_name']
        break
    if username == None: continue
    u = db.users.find_one({'id': userid, 'screen_name_lower': {'$gt': ''}})
    if u != None: continue
    print "not found in users, adding"
    sys.stdout.flush()
    if userid in ignored:
      print "is ignored, adding anyway"
      sys.stdout.flush()
    try:
      db.users.update_one({'id':userid, 'screen_name': username}, {'$set': {'id':userid, 'screen_name': username}}, upsert=True)
      print "name of mentioned user inserted into users", userid
      db.users.update_one({'id':userid, 'screen_name_lower': username.lower()}, {'$set': {'id':userid, 'screen_name_lower': username.lower()}}, upsert=True)
      print "keyname of mentioned user inserted into users", userid
      sys.stdout.flush()
    except Exception as e:
      print "cannot insert user found in mentions", e
      sys.stdout.flush()
      pass

