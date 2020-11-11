#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

'''
  run this file to create quote.txt graph (with weights)
  exportquote .py -v > quote.out.txt

  the script generates quote.txt with "src dst w" quote edges
  "src dst w" means user #src quoted user #dst #w times

  to fill in unknowns for next time then run
  cat quote.out.txt |grep unknown | cut -f 2 -d\( | cut -f 1 -d\)| xargs bin/addid.py -v

  to process the graph, use visualization/graphfigures.py
'''


import sys
import optparse
import dateutil.parser
from datetime import datetime
from collections import Counter
from progress.bar import Bar
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek.")
  parser.add_option("-o", "--output", action="store", dest="filename", default='quote.txt', help="Output file")
  parser.add_option("-b", "--before", action="store", dest="before", default=False, help="Before given date.")
  parser.add_option("-a", "--after", action="store", dest="after", default=False, help="After given date.")
  parser.add_option("--deleted", action="store_true", dest="deleted", default=False, help="Report quotes even if the quoted has been deleted.")
  (options, args) = parser.parse_args()

  verbose(options.verbose)

  db, _ = init_state(use_cache=False, ignore_api=True)

  query = { 'quoted_status_id': {'$gt': 1}, 'retweeted_status': None }

  criteria = {}
  if options.before:
    criteria['$lte'] = dateutil.parser.parse(options.before)
  if options.after:
    criteria['$gt'] = dateutil.parser.parse(options.after)

  if verbose():
    sys.stderr.write("initialize quote scan\n")
    sys.stderr.flush()
  if options.before or options.after:
    query['created_at'] = criteria
    num = db.tweets.count({'created_at': criteria})
  else:
    num = db.tweets.count()
  
  quotes = db.tweets.aggregate([
    { '$match': query },
    {
      '$lookup': {
        'from': 'tweets',
        'localField': 'quoted_status_id',
        'foreignField': 'id',
        'as': 'quoted_tweet'
      }
    },
    { '$unwind' : '$quoted_tweet' },
    {
      '$group': {
        '_id': { 'quoter_id': '$user.id', 'quoted_id': '$quoted_tweet.user.id'},
        'weight': {'$sum': 1}
      }
    }
  ], allowDiskUse=True)
  if verbose():
    sys.stderr.write("about to scan {} total tweets for quotes\n".format(num))
    sys.stderr.flush()
    quotes = Bar("Processing:", max=num, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(quotes)
  with open(options.filename, "w") as outf:
    for q in quotes:
      quoter_id = q['_id']['quoter_id']
      if 'quoted_id' not in q['_id']:
        if options.deleted:
          quoted_id = 'quote-deleted'
        else:
          continue
      else:
        quoted_id = q['_id']['quoted_id']
      weight = q['weight']
      if options.greek:
        if is_greek(db, quoter_id) or is_greek(db, quoted_id): 
          pass
        else:
          continue
      outf.write('{} {} {}\n'.format(quoter_id, quoted_id, weight))


