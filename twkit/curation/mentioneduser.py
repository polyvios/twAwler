#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
Find any user information based on the user screen name by looking
into tweets that mention the user, and insert into the users
collection.
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

client = MongoClient()
db = client.twittergr

names = {}
ids = {}
for i in db.following.find():
  names[i['id']] = i['screen_name_lower']
  ids[i['screen_name_lower']] = i['id']

ignored = Set()
for i in db.ignored.find():
  ignored.add(i['id'])

if len(sys.argv) < 2:
  print "Usage: {} <users>".format(sys.argv[0])
  sys.exit(1)

userlist = [x.lower().replace("@", "") for x in sys.argv[1:]]

for username in userlist:
  userid = None
  for mention in db.tweets.find({'user_mentions' : { '$elemMatch' : {u'screen_name': {'$regex' : username, '$options' : 'i'}}}}).limit(10):
    print ".", mention
    sys.stdout.flush()
    for i in mention['user_mentions']:
      if i['screen_name'].lower() == username:
        userid = i['id']
        break
    if userid == None: continue
    u = db.users.find_one({'id': userid})
    if u != None: continue
    print userid, "not found in users, adding"
    sys.stdout.flush()
    if userid in ignored:
      print userid, "is ignored, add manually if necessary"
      sys.stdout.flush()
      continue
    try:
      db.users.update_one({'id':userid, 'screen_name_lower': username}, {'$set': {'id':userid, 'screen_name_lower': username}}, upsert=True)
      print "mentioned user inserted into users", userid
      sys.stdout.flush()
      sys.exit(0)
    except:
      print "cannot insert user found in mentions"
      sys.stdout.flush()
      pass

