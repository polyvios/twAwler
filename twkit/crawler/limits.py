#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
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
  parser.add_option("--waitfor", action="store", dest="waitfor", default=None, help="Wait until timeline requests can be made again")
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
      print(sys.exc_info())
      print(".")
      time.sleep(3)
      continue

  for d in sorted(api.rate_limit.resources):
    for r in sorted(api.rate_limit.resources[d]):
      l = api.rate_limit.get_limit(r)
      if l.remaining == l.limit: continue
      left = l.reset - timegm(gmtime())
      rem = l.remaining
      if sys.stdout.isatty():
        if left < rem:
          rem = u'\033[93m{:>3}\033[0m'.format(rem)
        if rem == 0:
          rem = u'\033[91m{:>3}\033[0m'.format(rem)
      print(u'{:<40} {:>3} requests left in the next {:>3} seconds'.format(r, rem, left))

  if options.waitfor:
    d = api.rate_limit.get_limit(options.waitfor)
    if d.remaining == 0:
      sec = d.reset - timegm(gmtime())
      print("waiting for", sec, "seconds")
      sys.stdout.flush()
      time.sleep(sec)

  if options.wait:
    d = api.rate_limit.get_limit('/statuses/user_timeline')
    if d.remaining == 0:
      sec = d.reset - timegm(gmtime())
      print("waiting for", sec, "seconds")
      sys.stdout.flush()
      time.sleep(sec)

  if options.pause:
    d = api.rate_limit.get('/statuses/user_timeline')
    while d.remaining != 0:
      req = d.remaining
      sys.stdout.flush()
      sec = req
      print(req, "requests left, waiting ", sec, "seconds for pause")
      time.sleep(sec)
      limits = api.GetRateLimitStatus()
      d = api.rate_limit('/statuses/user_timeline')

  if verbose():
    limits = api.rate_limit.resources
    print(limits)

