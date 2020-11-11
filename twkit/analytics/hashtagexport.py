#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################


"""
  export hashtag word-count
  before running this, run from mongo client the following map-reduce:

db.tweets.mapReduce(
  function() {
    if(this.hashtags) {
      this.hashtags.forEach(
        function(h) {
          emit(h, 1);
        }
      );
    }
  },
  function(k, vals) {
    var total=0;
    for(var v of vals)
      if (v !== null)
        total+=v;
    return total;
  },
  {
    out: 'hashtag_sum',
    query: {'hashtags.0': {$exists: true}}
  }
)

"""

import optparse
from datetime import datetime,timedelta
from twkit.utils import *

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state(False, True)

  for hashtag in db.hashtag_sum.find():
    print(u'{}, {}'.format(int(hashtag['value']), hashtag['_id']).encode('utf-8'))
