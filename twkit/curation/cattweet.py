#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Gets a tweet ID (only one) and prints out the tweet as a JSON object.
"""

import sys
import json
import time
import re
from pymongo import MongoClient
from bson.json_util import loads
from datetime import datetime
import pprint
from twkit.utils import *

db, api = init_state(False)

if len(sys.argv) != 2:
  print "Usage: {} <tweet id>".format(sys.argv[0])
  sys.exit(1)

tweetid = long(sys.argv[1])

for tw in db.tweets.find({'id': tweetid}):
  MyPrettyPrinter().pprint(tw)
