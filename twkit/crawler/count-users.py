#!/usr/bin/python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import re
import json
import sys
from collections import Counter
from progress.bar import Bar
from twkit.utils import *


db, api = init_state(True)
users = db.users.find({}, {'id':1})
users = Bar("Processing:", max=users.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(users)
counter = Counter()
for u in users:
  counter[u['id']] += 1

for c in sorted(counter):
  print u'{} : {}'.format(c, counter[c])
