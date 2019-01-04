#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Print out the sizes of important collections.
"""

from twkit.utils import *

if __name__ == '__main__':
  dat = datetime.utcnow()
  db, api = init_state()
  dumped = db.crawlerdata.count({'reached':True})
  total = db.crawlerdata.count()
  
  tracked = db.following.count()
  totaltw = db.tweets.count()
  totalgr = db.tweets.count({'lang': config.lang})
  totalfol = db.follow.count()
  totallist = db.lists.count()
  totalusers = db.users.count()
  #uniqusers = db.users.aggregate([
    #{ '$group': { '_id': '$id' } },
    #{ '$group': { '_id': 1, 'count': {'$sum': 1} } }
  #], allowDiskUse=True)
  #totalu = db.follow.find({'id': }).count()
  print "loaded", dumped, "out of", total, "with", tracked, "total followed users"
  print totalgr, "tweets in greek out of", totaltw, "total tweets"
  print totalfol, "follow edges"
  print totallist, "lists"
  print totalusers, "user instances"
  #print uniqusers, "unique users"
  db.crawlerstats.update({'date': dat},
    {'$set': {
      'loaded': dumped,
      'tracked': tracked,
      'edges': totalfol,
      'grtweets': totalgr,
      'dbtweets': totaltw,
      'lists': totallist,
      'users': totalusers,
      'suspended': db.suspended.count(),
      'ignored': db.ignored.count(),
      'dead': db.cemetery.count(),
      'greeks': db.greeks.count(),
      'favs': db.favorites.count()
      'protected': db.protected.count()
    }}, upsert=True)

