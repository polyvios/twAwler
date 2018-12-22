#!/usr/bin/python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import sys
import optparse
from datetime import datetime,timedelta
from twkit.utils import *
from twkit.analytics.stats import *
from twkit.analytics.senti import *
#from group import *
from twkit.analytics.gender import get_gender
import unicodecsv

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids.")
  parser.add_option("--all", action="store_true", dest="all", default=False, help="Aggregate over all user vectors.")
  (options, args) = parser.parse_args()
  db, api = init_state(False, True)

  userlist = [x.lower().replace("@", "") for x in args]

  if options.all:
    userlist = [x['id'] for x in db.uservectors.find({},{'id':1})]
    options.ids = True

  word_count = Counter()

  if options.verbose:
    userlist = Bar("Processing:", max=len(userlist), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(userlist)
  for user in userlist:
    now = datetime.utcnow()
    uid = long(user) if options.ids else None
    uname = None if options.ids else user
    x = lookup_user(db, uid, uname)
    vect = db.uservectors.find_one({'id': x['id']})

    for d in vect.get('most_common_words', []):
      word_count[d['word']] += d['count']
    #word_count += Counter({d['word']: d['count'] for d in vect.get('most_common_words')})

  for w in sorted(word_count):
    print u'{}\t{}'.format(word_count[w], w)encode('utf-8')
