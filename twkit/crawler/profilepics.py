#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
  This tool scans all followed users in the db.following collection,
  selects the ones having a "downloaded_profile_date" field more than
  30 days ago, and wgets the URL in the "profile_image_url" field of
  the corresponding entry in the db.users collection.  The image is
  downloaded in the
    images/<first letter of screen_name>/<screen_name-date-extension>
  file.
"""

import os.path
import optparse
from progress.bar import Bar
from subprocess import Popen, PIPE
from datetime import datetime
from twkit.utils import *
from twkit.crawler.freq import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, api = init_state()
  users = db.following.find().batch_size(100)
  if verbose():
    users = Bar("Processing:", max=users.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(users)
  for u in users:
    uid = u['id']
    us = lookup_user(db, uid)
    cdata = db.crawlerdata.find_one({'id': uid})
    d = datetime.utcnow().date()
    d = datetime(d.year, d.month, d.day)
    #if us.get('deleted', False):
      #print "User marked deleted. Skip."
      #continue
    if cdata.get('downloaded_profile_date', datetime(1970,01,01,00,00,00)) > (d - timedelta(days=30)):
      #if verbose(): print "Picture already downloaded. Skip."
      continue
    if 'profile_image_url' not in us or not us['profile_image_url'].startswith('http'): continue
    link = us['profile_image_url'].replace('_normal.', '_400x400.')
    suffix = link.split(u'.')[-1]
    imagename = u'{}-{}'.format(u['screen_name_lower'], d.date())
    basename = u'{}.{}'.format(imagename, suffix)
    firstletter = basename.lower().replace("_","")[0]
    filename = u'images/{}/'.format(firstletter) + basename.lower()
    if os.path.isfile(filename):
      if verbose(): print u'Found it! Skipping.'
      db.crawlerdata.update_one({'id': uid}, {'$set': {'downloaded_profile_date': d}}, upsert=True)
      continue
    else:
      print link, u"->", filename
    #print u'Downloading: {}'.format(link)
    p = Popen(u'wget --no-hsts -P images {} -O {} 2>&1'.format(link, filename), shell=True, stdout=PIPE)
    output = p.communicate()[0] #wait
    if " 404 Not Found" in output:
      print u"NOT FOUND:"
      gprint(output)
      add_id(db, api, uid, wait=False, force=True)
    else:
      db.crawlerdata.update_one({'id': uid}, {'$set': {'downloaded_profile_date': d}}, upsert=True)
      print "{} ->> {}".format(u['screen_name_lower'], basename.lower())
      db.images.update_one(
        {'screen_name': u['screen_name_lower'], 'date': d},
        {'$set': {'screen_name': u['screen_name_lower'], 'date': d, 'image': imagename.lower()}},
        upsert=True
      )
