#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Get and save the current trending topics for Greece.
"""

import sys
import dateutil.parser
from twkit.utils import *

if __name__ == "__main__":
  db, api = init_state()

  #geo id for greece
  woeid = 23424833

  for trend in api.GetTrendsWoeid(woeid):
    tr = {
      'trend': trend.name,
      'timestamp': dateutil.parser.parse(trend.timestamp)
    }
    db.trends.insert_one(tr)
    #gprint(trend)
