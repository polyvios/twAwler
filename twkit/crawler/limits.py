#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Query the API for rate limits and print out all endpoint limits that
are not set to maximum available.
"""

import sys
import time
import optparse
from datetime import datetime
from calendar import timegm
from time import gmtime
from twkit.utils import *

if __name__ == "__main__":
  parser = optparse.OptionParser()
  parser.add_option("-w", "--wait", action="store_true", dest="wait", default=False, help="Wait until timeline requests can be made again")
  parser.add_option("-p", "--pause", action="store_true", dest="pause", default=False, help="Wait until there are no timeline requests left")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Print verbose data on all limits, not just non-full ones")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, api = init_state()

  c = 10
  while c != 0:
    c -= 1
    try:
      api.InitializeRateLimit()
      break
    except:
      print sys.exc_info()
      print "."
      time.sleep(3)
      continue

  for d in api.rate_limit.resources:
    for r in api.rate_limit.resources[d]:
      l = api.rate_limit.get_limit(r)
      if l.remaining == l.limit: continue
      print u'{:<40} {:>3} requests left in the next {:>3} seconds'.format(r, l.remaining, l.reset - timegm(gmtime()))

  if options.wait:
    d = api.rate_limit.get_limit('/statuses/user_timeline')
    if d.remaining == 0:
      sec = d.reset - timegm(gmtime())
      print "waiting for", sec, "seconds"
      sys.stdout.flush()
      time.sleep(sec)

  if options.pause:
    d = api.rate_limit.get('/statuses/user_timeline')
    while d.remaining != 0:
      req = d.remaining
      sys.stdout.flush()
      sec = req
      print req, "requests left, waiting ", sec, "seconds for pause"
      time.sleep(sec)
      limits = api.GetRateLimitStatus()
      d = api.rate_limit('/statuses/user_timeline')

  if verbose():
    limits = api.rate_limit.resources
    gprint(limits)

