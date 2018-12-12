#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Fetch from twitter and add the user information to the 'users'
collection without following the user.
"""

import twitter
import sys
import optparse
from twkit.utils import *
from twkit.crawler.fillfollow import add100_id

if __name__ == "__main__":
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <id> [<id> ...]')
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("-f", "--force", action="store_true", dest="force", default=False, help="Get anyway")
  (options, args) = parser.parse_args()

  if len(args) < 1:
    parser.print_help()
    sys.exit(1)

  verbose(options.verbose)
  db, api = init_state(use_cache=False)

  if len(args) > 100:
    idlist = []
    for idstr in args:
      userid = long(idstr)
      if is_dead(db, userid):
        if verbose(): print u'user dead, skip'
        continue
      idlist.append(userid)
      if len(idlist) > 99:
        add100_id(db, api, idlist)
        idlist = []
    if len(idlist):
      add100_id(db, api, idlist)
  else:
    for idstr in args:
      userid = long(idstr)
      add_id(db, api, userid, force=options.force)

