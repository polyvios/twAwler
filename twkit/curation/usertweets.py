#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2017 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
List all tweets of a given user, either as JSON objects or in plain
text.
"""

import sys
import optparse
import config
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names")
  parser.add_option("-d", "--deleted", action="store_true", dest="deleted", default=False, help="Show only deleted")
  parser.add_option("-t", "--text", action="store_true", dest="text", default=False, help="Show only text")
  parser.add_option("-l", "--lang", action="store_true", dest="lang", default=False, help="Restrict to target language")
  (options, args) = parser.parse_args()

  db, api = init_state()
  userlist = [x.lower().replace("@", "") for x in args]
  for user in userlist:
    uname = None if options.ids else user
    uid = long(user) if options.ids else None
    u = lookup_user(db, uid, uname)
    print "getting {} tweets".format(id_to_userstr(db, u['id']))

    criteria = {'user.id': u['id']}
    if options.deleted:
      criteria['deleted'] = True
    if options.lang:
      criteria['lang'] = config.lang
    tweets =db.tweets.find(criteria).sort('id')

    for tw in tweets:
      if options.text:
        if 'text' in tw:
          print u'{}: {}'.format(tw['created_at'], tw['text']).encode('utf-8')
      else:
        print(tw)
