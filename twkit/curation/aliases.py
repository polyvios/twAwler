#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import sys
import pprint
import optparse
import pprint
import re
from twkit.utils import *

parser = optparse.OptionParser()
parser.add_option("--id", action="store_true", dest="id", default=False, help="Input is id, not username.")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Count found.")
parser.add_option("-r", "--reverse", action="store_true", dest="reverse", default=False, help="Reverse selection, print only unknown users.")
parser.add_option("-q", "--quick", action="store_true", dest="quick", default=False, help="Quick lookup, name to id or reverse.")
(options, args) = parser.parse_args()

verbose(options.verbose)
db, _ = init_state(use_cache=False, ignore_api=True)
for ustr in args:
  cnt = 0
  if options.quick:
    if options.id:
      u = lookup_user(db, uid=long(ustr))
    else:
      u = lookup_user(db, uname=ustr)
    if u is None:
      print "No such user: {}".format(ustr)
    else:
      print u'{} : {}'.format(u['id'], u['screen_name'])
    continue
  if options.id:
    for u in db.users.find({'id': long(ustr)}):
      cnt += 1
      if not options.reverse:
        if 'screen_name_lower' in u:
          print u['screen_name_lower'], u['id']
        else:
          print u'was: {} {}'.format(u['screen_name'], u['id'])
  else:
    for u1 in db.users.find({'screen_name_lower': ustr.lower()}):
      for u2 in db.users.find({'id': u1['id']}):
        cnt += 1
        if not options.reverse:
          print u2['screen_name'], u1['id']
    #nameregex = re.compile(r'^{}$'.format(ustr.lower()), re.IGNORECASE)
    for u1 in db.users.find({'screen_name': ustr.lower()}).collation({'locale': 'en', 'strength': 1}):
      for u2 in db.users.find({'id': u1['id']}):
        cnt += 1
        if not options.reverse:
          print u2['screen_name'], u1['id']
  if verbose():
    print "Found", cnt
  if options.reverse and cnt == 0:
    if is_dead(db, long(ustr)): continue
    if is_suspended(db, long(ustr)): continue
    print ustr

