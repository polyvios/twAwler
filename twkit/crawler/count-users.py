#!/usr/bin/python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

from collections import Counter
from progress.bar import Bar
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="make noise.")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state(True)

  users = db.users.find({}, {'id':1})
  users = Bar("Processing:", max=users.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(users)
  counter = Counter()
  for u in users:
    counter[u['id']] += 1

  for c in sorted(counter):
    print(u'{} : {}'.format(c, counter[c]))
