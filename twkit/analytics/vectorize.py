#!/usr/bin/env python2
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2019 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Computes all features for the given user and save the vector in the
uservectors collection.
"""

import sys
import optparse
from progress.bar import Bar
from datetime import datetime,timedelta
from twkit.utils import *
from twkit.analytics.stats import *
from twkit.analytics.senti import *
from twkit.analytics.gender import get_gender
import unicodecsv
import json

def vectorize_func(db, u, criteria, entity_file):
  if u == None: return
  now = datetime.utcnow()
  if verbose(): print now.isoformat(), u['id'], u['screen_name']
  if verbose(): print "{} Getting tweets".format(datetime.utcnow()),
  user_tweets = get_user_tweets(db, u['id'], criteria)
  if verbose(): print "{} Loading metadata".format(datetime.utcnow())
  fill_metadata_stats(db, u)
  if verbose(): print "{} Computing lexical".format(datetime.utcnow())
  fill_word_stats(db, u, criteria)
  if verbose(): print "{} Computing graph".format(datetime.utcnow())
  fill_follower_stats(db, u)
  if verbose(): print "{} Computing temporal".format(datetime.utcnow())
  usage_times_stats(db, u, criteria)
  if verbose(): print "{} Computing sentiment".format(datetime.utcnow())
  daily_entity_sentiment = fill_user_sentiment(db, u, criteria, entity_file)
  if verbose(): print "{} Compute user self-reference gender".format(datetime.utcnow())
  u['lexical_gender'] = get_gender(db, u['id'])
  if verbose(): print "{} Compute favorite graph features".format(datetime.utcnow())
  fill_favoriter_stats(db, u)
  if verbose(): print "{} Done, timestamping and saving".format(datetime.utcnow())
  u['vector_timestamp'] = now
  if '_id' in u: del u['_id']
  if verbose():
    gprint(u)
  db.uservectors.update({'id': u['id']}, {'$set': u}, upsert=True)


fields = [
  'seen_top_tweets',
  'seen_retweets',
  'seen_mentions',
  'seen_replies',
  'seen_total'
]


def flatten_dict(key, value):
  if type(value) is dict:
    r = {}
    for k, v in value.iteritems():
      r.update(flatten_dict(u'{}_{}'.format(key, k), v))
    return r
  elif type(value) is list:
    r = {}
    for i, v in enumerate(value):
      r.update(flatten_dict(u'{}_{}'.format(key, i), v))
    return r
  else:
    return {key: value}


if __name__ == '__main__':
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <user> [<user> ...]')
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  parser.add_option("-f", "--force", action="store_true", dest="force", default=False, help="Re-vectorize even if cached recently")
  parser.add_option("-o", "--output", action="store", dest="filename", default=None, help="Output file")
  parser.add_option("-b", "--before", action="store", dest="before", default=False, help="Before given date.")
  parser.add_option("-a", "--after", action="store", dest="after", default=False, help="After given date.")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids.")
  parser.add_option("--all", action="store_true", dest="all", default=False, help="Re-vectorize all stale vectors (older than 1 month)")
  parser.add_option("--skip", action="store", type="int", dest="skip", default=None, help="Skip given number of users (for parallelization)")
  parser.add_option("--stopafter", action="store", dest="stopafter", type="int", default=None, help="Stop after scanning how many")
  parser.add_option("--query", action="store", dest="query", default="{}", help="Select who to vectorize")
  parser.add_option("--greek", action="store_true", dest="greek", default=False, help="Ignore any users not marked as greek")
  parser.add_option("--purge", action="store_true", dest="purge", default=False, help="Clean database")
  parser.add_option("--queue", action="store_true", dest="queue", default=False, help="Vectorize users found in the vectorizequeue collection.")
  #parser.add_option("--group", action="store_true", dest="group", default=False, help="Input is group name.")
  parser.add_option("--dumpgraph", action="store_true", dest="dumpgraph", default=False, help="Print graph of users.")
  parser.add_option("--save", action="store_true", dest="save", default=False, help="Only output file")
  parser.add_option("-e", "--entities", action="store", dest="entity_file", default='greekdata/entities.json', help="File with entities (def: greekdata/entities.json).")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  db, api = init_state(False, False)

  if verbose(): print u"{} start".format(datetime.utcnow())

  if options.purge:
    if (raw_input("sure? (y/n)") == 'y'):
      x = db.uservectors.delete_many({})
      print "deleted ", x.deleted_count
    else:
      print "aborted"
    sys.exit(0)

  criteria = {}
  if options.before:
    criteria['$lte'] = dateutil.parser.parse(options.before)
  if options.after:
    criteria['$gte'] = dateutil.parser.parse(options.after)

  if options.all:
    q = {}
    if options.query:
      q = json.loads(options.query)
      if verbose():
        gprint(q)
    it = db.uservectors.find(q, {'id':1}).sort('id', 1)
    if options.skip > 0:
      it = it.skip(options.skip)
    if options.stopafter:
      it = it.limit(options.stopafter)
    userlist = (x['id'] for x in it)
    #options.ids = True
  elif options.queue:
    if options.dumpgraph:
      print "Save and queue options are incompatible. Aborting."
      sys.exit(2)
    userlist = (x['id'] for x in db.vectorizequeue.find())
    #options.ids = True
  else:
    userlist = []
    for x in args:
      x = x.lower().replace("@", "")
      if options.ids:
        u = long(x)
      else:
        u = get_tracked(db, uname=x)
        if u is None:
          u = lookup_user(db, uname=x)
        #u = db.following.find_one({'screen_name_lower': x})
        if u is not None: 
          u = u.get('id')
        else:
          print u'Unknown user {}'.format(x)
      if u: userlist.append(u)

  userlist = list(userlist)
  if verbose():
    userlist = Bar("Process user:", max=len(userlist), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(userlist)
  if options.dumpgraph and options.filename:
    with open(options.filename, "a") as f:
      f.write("digraph {\n")
      for uid in userlist:
        v = db.uservectors.find_one({'id': uid})
        if v is None:
          sys.stderr.write(u"couldn't find {}\n".format(uid))
          continue
        f.write(u'  "{}" [userid="{}",shape="box",greek="{}",ignored="{}",tracked="{}"];\n'.format(
          v['screen_name'],
          v['id'],
          v['greek'],
          is_ignored(db,v['id']),
          get_tracked(db,v['id']) != None
        ))
        for u in v['most_mentioned_users']:
          f.write(u'  "{}" -> "{}" [label=mention, weight={}];\n'.format(v['screen_name'], u['user'], u['count']))
        for u in v['most_mentioned_by']:
          f.write(u'  "{}" -> "{}" [label=mention, weight={}];\n'.format(u['user'], v['screen_name'], u['count']))
        for u in v['most_retweeted_users']:
          f.write(u'  "{}" -> "{}" [label=retweet, weight={}];\n'.format(v['screen_name'], u['user'], u['count']))
        for u in v['most_retweeted_by']:
          f.write(u'  "{}" -> "{}" [label=retweet, weight={}];\n'.format(u['user'], v['screen_name'], u['count']))
        for u in v['most_replied_to']:
          f.write(u'  "{}" -> "{}" [label=reply, weight={}];\n'.format(v['screen_name'], u['user'], u['count']))
      f.write("}\n")
    sys.exit(0)

  vectorwriter = None
  if options.filename:
    vectorwriter = unicodecsv.DictWriter(open(options.filename, 'a'),
      fieldnames=user_metadata_attrs + usage_times_attrs +
        follower_stats_attrs + word_stats_attrs +
        user_sentiment_attrs + favoriter_attrs + ['lexical_gender', 'vector_timestamp'],
      #restval='ignore',
      encoding='utf-8')
    vectorwriter.writeheader()
  for user in userlist:
    now = datetime.utcnow()
    uid = long(user) # if options.ids else None
    #uname = None if options.ids else user
    x = lookup_user(db, uid)
    if x and 'screen_name' in x:
      u = { 'id': x['id'], 'screen_name': x['screen_name'] }
    else:
      print "Skipping unknown user:", uid, uname
      continue
    if options.greek and not is_greek(db, u['id']): continue
    if not options.save:
      vect = db.uservectors.find_one({'id': u['id']}, {'vector_timestamp':1})
      if vect and not options.force:
        if vect['vector_timestamp'] + timedelta(days=30) > now: 
          if verbose():
            print "Found cached version produced less than a month ago, skip"
          u = db.uservectors.find_one({'id': long(u['id'])})
        else:
          print "Found stale cached version, recompute"
          vectorize_func(db, u, criteria, options.entity_file)
          u = db.uservectors.find_one({'id': u['id']})
      else:
        vectorize_func(db, u, criteria, options.entity_file)
        u = db.uservectors.find_one({'id': u['id']})
    else:
      u = db.uservectors.find_one({'id': u['id']})
    if u is None:
      print "No user vector to save:", user
    else:  
      if '_id' in u: del u['_id']
      if vectorwriter:
        vectorwriter.writerow(u)
    if options.queue:
      db.vectorizequeue.delete_one({'id': u['id']})

