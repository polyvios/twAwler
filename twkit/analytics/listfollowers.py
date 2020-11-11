#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
List all followers of the given user.
Output is edges in "follower-id user-id" syntax: direction of "follow" to the right.
"""

import sys
import optparse
import fileinput
import unicodecsv
import dateutil.parser
from twkit.utils import *

def fill_follow_graph(db, userids):
  followerlists = {uid:frozenset(get_followers(db, uid)).intersection(userids) for uid in userids}
  return followerlists

fieldnames = [
  'id',
  'screen_name_lower',
  'created_at',
  'statuses_count',
  'followers_count',
  'friends_count',
  'listed_count',
  'protected',
  'verified',
  'ignored',
  'dead',
  'greek',
  'following',
  'suspended',
  'lang',
  'timestamp_at',
  #'contributors_enabled',
  'default_profile',
  'default_profile_image',
  'description',
  #'entities',
  'favourites_count',
  #'follow_request_sent',
  'geo_enabled',
  #'id_str',
  #'is_translator',
  'location',
  'name',
  #'notifications',
  'profile_background_color',
  'profile_background_image_url',
  #'profile_background_image_url_https',
  'profile_background_tile',
  'profile_banner_url',
  'profile_image_url',
  #'profile_image_url_https',
  'profile_link_color',
  #'profile_sidebar_border_color',
  'profile_sidebar_fill_color',
  'profile_text_color',
  #'profile_use_background_image',
  'profile_use_background_image', 'profile_image_url_https', 'id_str', 'profile_background_image_url_https', 'profile_sidebar_border_color',
  'screen_name',
  'time_zone',
  'url',
  'utc_offset',
  #'withheld_in_countries',
  #'withheld_scope',
  'downloaded_profile'
]

def save_csv(db, userids, filename):
  with open(filename, 'w') as csvfile:
    vectorwriter = unicodecsv.DictWriter(csvfile,
      fieldnames=fieldnames,
      restval='',
      encoding='utf-8',
      extrasaction='ignore',
      quoting=unicodecsv.QUOTE_MINIMAL)
      
    vectorwriter.writeheader()
    for fid in userids:
      flr = lookup_user(db, fid)
      if flr is None:
        if verbose(): sys.stderr.write(u'unknown user: {}\n'.format(fid))
        continue
      flr['ignored'] = is_ignored(db, fid)
      flr['dead'] = is_dead(db, fid)
      flr['greek'] = is_greek(db, fid)
      flr['following'] = (get_tracked(db, fid) is not None)
      flr['suspended'] = is_suspended(db, fid)
      del flr['_id']
      if 'downloaded_profile_date' in flr: del flr['downloaded_profile_date']
      vectorwriter.writerow(flr)
  return


def get_userlist_followers(db, userlist, options, criteria):
  common = None
  total = frozenset()
  for user in userlist:
    uname = None if options.ids else user
    uid = long(user) if options.ids else None
    u = lookup_user(db, uid, uname)
    if u is None:
      if verbose(): sys.stderr.write(u'Unknown user {}\n'.format(user))
      continue
    uid = u['id']
    followers = frozenset(get_followers(db, u['id'], criteria))
    total |= followers
    if options.common:
      if common is None: common = followers
      else: common &= followers
    else:
      for f in followers:
        if options.greek and not is_greek(db, f): continue
        print u'{} {}'.format(f, uid)
        if options.addusers:
          if is_dead(db, f): continue
          if is_suspended(db, f): continue
          if get_tracked(db, f): continue
          u = lookup_user(db, f)
          try:
            add_to_followed(db, f, u['screen_name'].lower(), is_protected(db, f))
          except:
            follow_user(db, api, f)
  #end for
  return common, total

 
if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("--fromfile", action="store_true", dest="fromfile", default=False, help="Args are filenames containing users, where '-' is stdin.")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Arguments are user id not user names.")
  parser.add_option("--addusers", action="store_true", dest="addusers", default=False, help="Add all followers to tracked users.")
  parser.add_option("--greek", action="store_true", dest="greek", default=False, help="Only Greek ones.")
  parser.add_option("--common", action="store_true", dest="common", default=False, help="Only common to all given users.")
  parser.add_option("--before", action="store", dest="before", default=False, help="Before given date.")
  parser.add_option("--after", action="store", dest="after", default=False, help="After given date.")
  parser.add_option("--close", action="store_true", dest="close", default=False, help="List all edges between given set.")
  parser.add_option("--ego", action="store", dest="ego", type=int, default=0, help="Compute ego net at given depth.")
  parser.add_option("--csv", action="store", dest="csv", default=None, help="Save data per follower.")
  parser.add_option("--dot", action="store", dest="dot", default=None, help="Save data as graph in given file.")
  (options, args) = parser.parse_args()
  verbose(options.verbose)
  db, api = init_state(use_cache=False, ignore_api=not options.addusers)

  criteria = {}
  if options.before:
    criteria['$lte'] = dateutil.parser.parse(options.before)
  if options.after:
    criteria['$gte'] = dateutil.parser.parse(options.after)

  if options.fromfile:
    userlist = fileinput.input(args)
  else:
    userlist = [x.lower().replace("@", "") for x in args]
  common, total = get_userlist_followers(db, userlist, options, criteria)
  for d in range(options.ego):
    userlist = total
    options.ids = True
    common, t = get_userlist_followers(db, userlist, options, criteria)
    total |= t
    
  if options.common:
    for f in common:
      if options.greek and not is_greek(db, f): continue
      print u'{}'.format(f)
  if options.close:
    g = fill_follow_graph(db, total)
  if options.dot:
    save_dot(db, g, options.dot)
  if options.csv:
    save_csv(db, total, options.csv)
