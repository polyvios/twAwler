#!/usr/bin/python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################


"""
This tool can completely purge a user from the database.
Warning: This may reduce information on other users, as the given user
is purged from all mined relations, too.
"""

import optparse
from datetime import datetime
#from py2neo import Graph, Node, Relationship
from twkit.utils import *
#from graph import *

def del_userid(db, graph, uid):
  #print(graph.evaluate("MATCH (n) where n.id_str = {} detach delete n".format(uid)))
  print(db.cemetery.delete_many({'id':uid}).deleted_count)
  print(db.crawlerdata.delete_many({'id':uid}).deleted_count)
  print(db.favorites.delete_many({'user_id':uid}).deleted_count)
  print(db.follow.delete_many({'id': uid}).deleted_count)
  print(db.follow.delete_many({'follows': uid}).deleted_count)
  print(db.following.delete_many({'id':uid}).deleted_count)
  print(db.greeks.delete_many({'id':uid}).deleted_count)
  print(db.ignored.delete_many({'id': uid}).deleted_count)
  print(db.groups.delete_many({'id':uid}).deleted_count)
  print(db.lastscan.delete_many({'id':uid}).deleted_count)
  print(db.listmembers.delete_many({'user_id':uid}).deleted_count)
  print(db.listsubscribers.delete_many({'user_id':uid}).deleted_count)
  print(db.protected.delete_many({'id':uid}).deleted_count)
  print(db.suspended.delete_many({'id':uid}).deleted_count)
  print(db.users.delete_many({'id':uid}).deleted_count)
  print(db.uservectors.delete_many({'id':uid}).deleted_count)
  print(db.tweets.delete_many({'user.id':uid, 'lang': {'$ne': config.lang}}).deleted_count)



if __name__ == '__main__':
  parser = optparse.OptionParser(usage=u'Usage: %prog [options] <user>')
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Argument is user id")
  (options, args) = parser.parse_args()

  db, _ = init_state(ignore_api=True)
  #graph = Graph("http://neo4j:twittergr@localhost:7474/db/data/")
  graph= None

  now = datetime.utcnow()
  userlist = [x.lower().replace("@","") for x in args]
  for user in userlist:
    uid = int(user)
    del_userid(db, graph, uid)

