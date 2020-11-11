#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Scans the follow graph and gets all user info missing added into the
users collection.
"""

import sys
import twitter
import optparse
from twkit.utils import *
from progress.bar import Bar
from pymongo.errors import CursorNotFound


#def fill_follow(db, api, uid, uname):
#  u = lookup_user(db, uid, uname)
#  if u is None:
#    print("User {} not found".format(uid if uname is None else uname))
#    return
#  scan = db.follow.find({'follows': u['id']})

  

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is ids, not usernames")
  parser.add_option("--skip", action="store", dest="skip", type="int", default=0, help="Restart from index")
  (options, args) = parser.parse_args()
  skipno = options.skip
  verbose(options.verbose)
  db, api = init_state(use_cache=True)
  u = None
  if len(args):
    user = args[0]
    u = lookup_user(db, uid=int(user)) if options.ids else lookup_user(db, uname=user)
    if u is None:
      print("Not found")
      sys.exit(1)
    scan = db.follow.find({'follows': u['id']})
  else:
    scan = db.follow.find().batch_size(10)
  if skipno > 0:
    scan = scan.skip(skipno)
  idlist = []
  while True:
    try:
      for fol in Bar("Loading:", max=scan.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(scan):
        if user_is_missing(db, fol['id']) and fol['id'] not in idlist:
          if verbose(): print(fol['id'])
          idlist.append(fol['id'])
        if user_is_missing(db, fol['follows']) and fol['follows'] not in idlist:
          if verbose(): print(fol['follows'])
          idlist.append(fol['follows'])
        if len(idlist) > 98:
          add100_id(db, api, idlist)
          idlist = []
        skipno += 1
      if len(idlist):
        add100_id(db, api, idlist)
      break
    except CursorNotFound:
      print("lost cursor, restart from", skipno)
      if u:
        scan = db.follow.find({'follows': u['id']}).skip(skipno)
      else:
        scan = db.follow.find().skip(skipno)

    #get_if_missing(db, api, fol['id'])
    #get_if_missing(db, api, fol['follows'])




