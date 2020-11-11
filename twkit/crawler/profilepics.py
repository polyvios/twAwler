#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
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

import os
#import os.path
import optparse
from progress.bar import Bar
from subprocess import Popen, PIPE
from datetime import datetime
from twkit.utils import *
from twkit.crawler.freq import *

def file_is_empty(path):
  return os.stat(path).st_size==0

def scan_user_avatar(db, api, u):
  uid = u['id']
  us = lookup_user(db, uid)
  cdata = db.crawlerdata.find_one({'id': uid})
  d = datetime.utcnow().date()
  d = datetime(d.year, d.month, d.day)
  #if us.get('deleted', False):
    #print("User marked deleted. Skip.")
    #continue
  if cdata.get('downloaded_profile_date', datetime(1970,1,1,0,0,0)) > (d - timedelta(days=config.profilepic_expiration_days)):
    #if verbose(): print("Picture already downloaded. Skip.")
    return
  if 'profile_image_url' not in us or not us['profile_image_url'].startswith('http'): return
  link = us['profile_image_url'].replace('_normal.', '_400x400.')
  suffix = link.split(u'.')[-1]
  if suffix.startswith('com/'):
    suffix = 'jpeg'
  imagename = u'{}-{}'.format(u['screen_name_lower'], d.date())
  basename = u'{}.{}'.format(imagename, suffix)
  firstletter = basename.lower().replace("_","")[0]
  filename = u'images/{}/'.format(firstletter) + basename.lower()
  if os.path.isfile(filename):
    if verbose(): print(u'Found it! Skipping.')
    # this is commented out. it either succeeded last time and was
    # inserted, or this was a failed get and this is an empty or
    # corrupted image:
    #db.images.update_one(
    #  {'screen_name': u['screen_name_lower'], 'date': d},
    #  {'$set': {'screen_name': u['screen_name_lower'], 'date': d, 'image': imagename.lower()}},
    #  upsert=True
    #)
    #db.crawlerdata.update_one({'id': uid}, {'$set': {'downloaded_profile_date': d}}, upsert=True)
    return
  else:
    print(link, u"->", filename)
  #print(u'Downloading: {}'.format(link))
  p = Popen(u'wget --timeout 5 --no-hsts -P images {} -O {} 2>&1'.format(link, filename), shell=True, stdout=PIPE)
  output = str(p.communicate()[0], 'utf-8') #wait
  if " 404 Not Found" in output:
    print(u"NOT FOUND:")
    add_id(db, api, uid, wait=False, force=True)
    db.crawlerdata.update_one({'id': uid}, {'$set': {'downloaded_profile_date': d}}, upsert=True)
    os.remove(filename)
  else:
    if not os.path.exists(filename):
      pass
    elif file_is_empty(filename):
      print(u"GOT EMPTY FILE: {}".format(filename))
      os.remove(filename)
    else:
      db.images.update_one(
        {'screen_name': u['screen_name_lower'], 'date': d},
        {'$set': {'screen_name': u['screen_name_lower'], 'date': d, 'image': imagename.lower()}},
        upsert=True
      )
      db.crawlerdata.update_one({'id': uid}, {'$set': {'downloaded_profile_date': d}}, upsert=True)
      print("{} ->> {}".format(u['screen_name_lower'], basename.lower()))
  return


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='List names of tracked users')
  parser.add_option("--skip", action="store", dest="skip", type="int", default=0, help="Restart from index")
  parser.add_option("--stopafter", action="store", dest="stopafter", type="int", default=0, help="Stop after scanning how many")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, api = init_state()
  while True:
    users = db.following.find().batch_size(5000)
    count = users.count();
    if options.skip > 0:
      users = users.skip(options.skip)
      count -= options.skip
    if options.stopafter:
      users = users.limit(options.stopafter)
      count = min(options.stopafter, count)
    if verbose():
      users = Bar("Processing:", max=count, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(users)
    try:
      for u in users:
        scan_user_avatar(db, api, u)
        if options.stopafter: options.stopafter -= 1
        if options.skip: options.skip += 1
    except:
      print("got {}".format(sys.exc_info()))
      print("retrying")
      continue
    break

