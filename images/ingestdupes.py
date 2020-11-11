#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################


import os
import sys
from datetime import datetime, timedelta
from twkit.utils import *

db, api = init_state()

for link in sys.argv[1:]:
  linkfile = link
  linked = os.readlink(link)
  link = link.split('.')[0].split('/')[-1]
  linked = linked.split('.')[0].split('/')[-1]
  linkedstr = linked.split('-')
  linked_name = linkedstr[0]
  linked_year = int(linkedstr[1])
  linked_month = int(linkedstr[2])
  linked_day = int(linkedstr[3])
  linkstr =  link.split('-')
  link_name = linkstr[0]
  link_year = int(linkstr[1])
  link_month = int(linkstr[2])
  link_day = int(linkstr[3])
  d = datetime(link_year, link_month, link_day)

  x = db.images.find_one({'screen_name': link_name, 'date': d})
  if x is None:
    print("{} not added when crawling!".format(link))
  else:
    #print "!",
    pass

  #gprint(
  db.images.update_one(
    {'screen_name': link_name, 'date': d},
    {'$set': {'screen_name': link_name, 'date': d, 'image': linked}},
    upsert=True
  )
  #.raw_result)
  #gprint(
  db.images.update(
    {'image': link},
    {'$set': {'image': linked}},
    multi=True
  )
  #)

  if linked_name != link_name:
    print("Same avatar: {} -> {}".format(link_name, linked_name))
  os.remove(linkfile)
