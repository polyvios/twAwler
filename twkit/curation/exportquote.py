#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
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
from collections import Counter
from progress.bar import Bar
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek")
  parser.add_option("-o", "--output", action="store", dest="filename", default='quote.txt', help="Output file")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  db, _ = init_state(use_cache=False, ignore_api=True)

  criteria = { 'quoted_status_id': {'$gt': 1} }
  if len(args):
    criteria['user.id'] = int(args[0])

  with open(options.filename, "w") as outf:
    for q in db.tweets.aggregate([
      { '$match': criteria },
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
    ], allowDiskUse=True):
      quoter_id = q['_id']['quoter_id']
      if 'quoted_id' not in q['_id']:
        quoted_id = 'quote-deleted'
      else:
        quoted_id = q['_id']['quoted_id']
      weight = q['weight']
      if options.greek:
        if is_greek(db, quoter_id) or is_greek(db, quoted_id): 
          pass
        else:
          continue
      outf.write('{} {} {}\n'.format(quoter_id, quoted_id, weight))


