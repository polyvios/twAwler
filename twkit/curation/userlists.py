#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Compute and print the given users' lists, or a user's list similarity
to other users.
"""

import sys
import optparse
from datetime import datetime
from progress.bar import Bar
from collections import Counter
from twkit.utils import *

def user_lists(db, uid):
  seen = {}
  for edge in db.listmembers.find({'user_id': uid}, {'list_id':1}):
    list_id = edge['list_id']
    if seen.get(list_id): continue
    seen[list_id] = True
  return seen.keys()

def list_similarity(db, uid, lists=None):
  if lists is None:
    lists = user_lists(db, uid)
  common = Counter()
  for l in lists:
    for uid2 in (m['user_id'] for m in db.listmembers.find({'list_id': l}, {'user_id':1})):
      common[uid2] += 1
  return common


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--all", action="store_true", dest="all", default=False, help="Scan all tracked users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("-s", "--similarity", action="store_true", dest="similarity", default=False, help="Compute this user's list-similarity edges")
  parser.add_option("--dot", action="store_true", dest="dot", default=False, help="Use dot output format")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state()

  if options.all:
    options.ids = True
    userlist = (x['id'] for x in db.following.find().batch_size(1))
    userlistlen = db.following.count()
  else:
    userlist = (x.lower().replace("@", "") for x in args)
    userlistlen = len(args)
  if verbose():
    userlist = Bar("Processing:", max=userlistlen, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(userlist)
  for user in userlist:
    uname = None if options.ids else user
    uid = long(user) if options.ids else None
    u = lookup_user(db, uid, uname)
    if u is None:
      sys.stderr.write("missing user {}/{}\n".format(uid, uname))
      if uid is None: continue
    else:
      uid = u.get('id', uid)
      uname = u.get('screen_name_lower', uname)

    if verbose(): 
      sys.stderr.write(u"user {}/{} in lists:\n".format(uid, uname))
    lists = user_lists(db, uid)

    if not options.similarity:
      for list_id in lists:
        listname = db.lists.find_one({'id': list_id})
        print u"{} : {} in {} : {}".format(id_to_userstr(db, uid), uid, list_id, listname['uri']).encode('utf-8')
    else:
      common = list_similarity(db, uid, lists)
      #del common[uid]
      for u2 in common:
        if options.dot:
          print u'"{}" -- "{}" [weight={}];'.format(uid, u2, common[u2])
        else:
          print u'{} {} {}'.format(uid, u2, common[u2])

