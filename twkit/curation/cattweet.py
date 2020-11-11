#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Gets a tweet ID (only one) and prints out the tweet as a JSON object.
"""

import sys
import optparse
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <tweet-id>')
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, _ = init_state(use_cache=False, ignore_api=True)

  if len(args) == 0:
    parser.print_help()
    sys.exit(1)

  tweetid = int(args[0])

  for tw in db.tweets.find({'id': tweetid}):
    print(tw)
