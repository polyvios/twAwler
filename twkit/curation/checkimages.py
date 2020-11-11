#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
check all images in db
list missing images
"""

import os
import sys
import glob
from datetime import datetime, timedelta
from twkit.utils import *

db, api = init_state()

total = 0
missing = 0
for image in db.images.find():
  fname = image['image']
  total += 1
  letter = fname[0]
  files = [x for x in glob.glob(u"images/{}/{}.*".format(letter, fname))]
  if len(files) == 0:
    missing += 1
    print(u"Missing file({}/{}): {}: {} -> images/{}/{}.*".format(missing, total, image['date'], image['screen_name'], letter, image['image']))
  if len(files) > 1:
    print(u"More than one file! {}: {} -> {}".format(image['date'], image['screen_name'], files))
