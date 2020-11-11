#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
scans all users for users that are completely silent
"""

# TODO: 
# - scan all users (sort by id, disregard subsequent/preceding
#   duplicates)
# - find users that are completely silent, find who they follow,
#   compute a vector of all followed users.
# - find all silent users with exactly the same hash-vector (friend
#   signature)
# - cluster them, print large clusters of silent users that follow the
#   exact same set of accounts

import optparse
from collections import Counter, defaultdict
from progress.bar import Bar
import numpy as np
from twkit.utils import *

def vectorized_jaccard(rawdata, ndocs, nfeats):
  # Get the row, col indices that are to be set in output array        
  r,c = np.tril_indices(ndocs,-1)

  # Use those indicees to slice out respective columns 
  p1 = rawdata[:,c]
  p2 = rawdata[:,r]

  # Perform n11 and n00 vectorized computations across all indexed columns
  n11v = ((p1==1) & (p2==1)).sum(0)
  n00v = ((p1==0) & (p2==0)).sum(0)

  # Finally, setup output array and set final division computations
  out = np.eye(ndocs)
  out[c,r] = n11v / (float(nfeats)-n00v)
  return out

def jaccard(a, b):
  return 1.0 * len(a & b) / len(a | b)
  
if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("--all", action="store_true", dest="all", default=False, help="Scan all")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names.")
  parser.add_option("--jthreshold", action="store", dest="jthreshold", default=0.5, type=float, help="Report similarities over threshold.")
  parser.add_option("--fthreshold", action="store", dest="fthreshold", default=0, type=float, help="Ignore accounts with less than N friends.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, api = init_state(use_cache=False, ignore_api=True)
  
  if options.all:
    #users = db.users.find().sort('id').limit(500000)
    #users = (u for x in db.following.find().limit(500) for u in db.users.find({'id': x['id']}))
    users = (u for x in db.following.find().sort('id', -1) for u in db.users.find({'id': x['id']}))
    if verbose():
      users = Bar("Loading:", max=db.users.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(users)
  else:
    users = (x.lower().replace("@", "") for x in args)
    if options.ids:
      users = [lookup_user(db, u) for x in args for u in get_followers(db, int(x))]
    else:
      users = [lookup_user(db, u) for x in args for u in get_followers(db, lookup_user(db, None, x).get('id', -1))]
    if verbose():
      users = Bar("Loading:", max=len(users), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(users)

  found = 0
  silentusers = {}
  lastuser = None
  usertweets = 0
  universe = set()
  for u in users:
    if u is None: continue
    uid = u['id']
    if options.all and get_tracked(db, uid) is None and not is_greek(db, uid): continue
    if uid == lastuser:
      if usertweets > 0: continue
      if 'statuses_count' in u:
        usertweets = max(usertweets, u['statuses_count'])
    else: # new user
      if usertweets == 0 and lastuser:
        found += 1
        #print(" found {}".format(found))
        friends = set(get_friends(db, lastuser))
        if len(friends) >= options.fthreshold:
          silentusers[lastuser] = friends
          universe |= friends
      #if found > 200: break
      usertweets = 0
      lastuser = uid
      if 'statuses_count' in u:
        usertweets = u['statuses_count']

  users = list(silentusers.keys())
  
  hd = users[0]
  tl = users[1:]
  while tl != []:
    for i in tl:
      x = jaccard(silentusers[i], silentusers[hd])
      if x > options.jthreshold:
        print("{} {} {}".format(hd, i, x))
    hd = tl[0]
    tl = tl[1:]

  #universelist = list(universe)
  #ndocs = len(silentusers)
  #nfeats = len(universelist)
  #print("{} by {}".format(ndocs, nfeats))
  #print("universe of friends:")
  #print([id_to_userstr(db, x) for x in universelist])
  #print("")
  #matrix = np.array([np.in1d(universelist, list(x)) for u,x in silentusers.items()])
  #matrix = matrix.transpose()
  #print("computing lookup dictionary")
  #n = 0
  #lookup = {}
  #for k,v in silentusers.items():
  #  lookup[n] = k
  #  n += 1
  # Free some mem?
  #silentusers = None
  #universe = None
  #universelist = None
  #print("jaccard")
  #simtable = vectorized_jaccard(matrix, ndocs, nfeats)
  #print("done jaccard, printing")
  #row = 0
  #for r in simtable:
  #  #print("{}: ".format(id_to_userstr(db, lookup[row])),)
  #  for x in range(row+1,simtable.shape[0]):
  #    if r[x] > options.jthreshold:
  #      #print("{} {} {}".format(lookup[row], id_to_userstr(db, lookup[x]), r[x]))
  #      print("{} {} {}".format(lookup[row], lookup[x], r[x]))
  #  row += 1

