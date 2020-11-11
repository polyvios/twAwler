#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Scans all greek retweets by greek users, and lists all seen users that
have written them but are not currently followed.
Used to discover greek speakers in retweets.
"""

import sys
import optparse
from progress.bar import Bar
from collections import Counter
from datetime import datetime, timedelta
import twkit
import twkit.utils
from twkit.utils import *

if __name__ == '__main__':
  start_time = datetime.utcnow()
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("-o", "--output", action="store", dest="outputfile", default="seen.out", help="Output File")
  parser.add_option("-u", "--user", action="store", dest="user", default=None, help="Run for one user.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, api = init_state(True)

  if options.user:
    user = options.user.lower().replace("@","")
    x = db.following.find_one({ 'screen_name_lower' : user })
    if x == None:
      print("Unknown user, first add user for tracking. Abort.")
      sys.exit(1)

  cache = twkit.utils.get_cache()

  names=cache['names']
  ids=cache['ids']
  ignored=cache['ign']
  dead=cache['dead']
  suspended=cache['susp']
  protected=cache['prot']
  greek=cache['gr']

  seen = Counter()
  unseen = Counter()
  cursor = db.tweets.find({'retweeted_status.lang': config.lang, 'created_at': {'$gt': datetime.now()-timedelta(days=30)}}, {'user.id':1, 'retweeted_status.user.id': 1}).sort('user.id', 1)
  #cursor2 = db.tweets.find({'retweeted_status.lang': config.lang}, {'user.id':1, 'retweeted_status.user.id': 1}).sort('user.id', 1)

  if verbose():
    cursor = Bar("Adding:", max = cursor.count(), suffix = '%(index)d/%(max)d - %(eta_td)s ').iter(cursor)
  for tweet in cursor:
    whoid = tweet["user"]["id"]
    if whoid in dead: continue
    if whoid in ignored: continue
    if whoid in protected: continue
    if whoid in suspended: continue
    u = names.get(whoid, None)
    if u is None:
      u = lookup_user(db, uid=whoid)
      if u is None:
        unseen[whoid] += 1
        continue
    if options.user:
      if user != u['screen_name_lower']: continue
    rt = tweet['retweeted_status']
    rtdid = rt['user']['id']
    if rtdid in names: continue
    if rtdid in dead: continue
    if rtdid in ignored: continue
    if rtdid in protected: continue
    if rtdid in suspended: continue
    seen[rtdid] += 1

  with open(options.outputfile, "w") as f:
    for key, value in sorted(seen.items(), key=lambda x: x[1]):
      f.write(u'{:7} {:20} ('.format(value, key))
      for u in db.users.find({'id': key}):
        f.write(u'{} '.format(u['screen_name'].lower()))
        for u2 in db.users.find({'screen_name': u['screen_name']}, {'id':1}).collation({'locale': 'en', 'strength': 1}):
          if u2['id'] == u['id']: continue
          f.write(u' also as {} '.format(u2['id']))
        f.write(u'{} {} {}'.format(u.get('name','').replace('\n', ' '),
          u.get('location', '').replace('\n', ' '),
          u.get('description', '').replace('\n', ' ')
        ).encode('utf-8'))
      f.write(')\n')

  if verbose():
    for i in unseen:
      print("unseen", i, unseen[i], 'ign' if i in ignored else '')

  update_crawlertimes(db, "seen", start_time)
