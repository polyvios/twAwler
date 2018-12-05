#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Use wget to crawl all shortened URLs for the specified user bio or
tweets, or all users, and populate the shorturl collection.
"""

import optparse
import pymongo
from progress.bar import Bar
import pipes, shlex, subprocess
from subprocess import Popen, PIPE
from twkit.utils import *

def deshorten_url(db, url):
  if ('://t.co' not in url
    and '://ift.tt' not in url
    and '://bit.ly' not in url
    and '://amzn.to' not in url
    and '://goo.gl' not in url
    and '://ow.ly' not in url
    and '://ht.ly' not in url
    and '://tinyurl.com' not in url
    and '://tr.im' not in url
    and '://lnked.in' not in url
    and '://eepurl.com' not in url
    and '://dlvr.it' not in url
    and '://lnkd.in' not in url
    and '://nyti.ms' not in url
    and '://wp.me' not in url
    and '://fb.me' not in url
    and '://instagr.am' not in url
    and '://trib.al' not in url
    and '://econ.trib.al' not in url
    and '://youtu.be' not in url
    and '://shar.es' not in url
    and '://n.mynews.ly' not in url
    and '://oak.ctx.ly' not in url
    and '://j.mp' not in url
    and '://econ.st' not in url
    and '://www.linkedin.com/slink?code=' not in url
    and '://sml.lnk.to' not in url
    #and '://feeds.feedburner.com/~r' not in url
    #and '://smarturl.it' not in url
  ):
    return url

  cached = db.shorturl.find_one({'shorturl': url})
  if cached is not None:
    if cached['url'] is None:
      return None
      #pass
    else:
      if url != cached['url']:
        return deshorten_url(db, cached['url'])

  args = u'wget -t 1 --user-agent=Firefox --timeout=5 --spider -S {} 2>&1 | grep ^Location | head -n 1'.format(pipes.quote(url))
  p = Popen(args, shell=True, stdout=PIPE)
  output = p.communicate()[0]
  locstrs = output.split()
  if len(locstrs) >= 2:
    out_url = locstrs[1]
  #try:
    if len(out_url):
      print u'{} -> {}'.format(url, out_url)
      db.shorturl.update_one(
        {'shorturl': url},
        {'$set': {'shorturl': url, 'url': out_url}},
        upsert=True)
      return deshorten_url(db, out_url)
  #except Exception as e:
  else:
    print u'bad location: "{}" for url "{}"'.format(output, url).encode('utf-8')
  db.shorturl.update_one(
    {'shorturl': url},
    {'$set': {'shorturl': url, 'url': None}},
    upsert=True)
  return url

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='Make noise.')
  parser.add_option('-t', '--tweets', action='store_true', dest='tweets', default=False, help='Look up and resolve urls in tweets.')
  parser.add_option('-u', '--user', action='store', dest='user', default=None, help='Only handle urls for the given user.')
  parser.add_option('--id', action='store_true', dest='ids', default=False, help='Input is user id.')
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, api = init_state(use_cache=False, ignore_api=True)

  if options.user:
    u = lookup_user(db, uid=long(options.user)) if options.ids else lookup_user(db, uname=options.user)
    if u is None:
      print u'unknown user', options.user
      sys.exit(1)
  if options.tweets:
    if options.user:
      cursor = db.tweets.find({'user.id': u['id'], 'urls': {'$ne': None}, 'deshorten': None}).batch_size(2)
    else:
      cursor = db.tweets.find({'urls': {'$ne': None}, 'deshorten': None}).batch_size(2)
    if verbose():
      cursor = Bar('Loading:', max=db.tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(cursor)
    for t in cursor:
      out_urls = []
      if 'urls' not in t or t['urls'] is None: continue
      for url in t['urls']:
        try:
          out_url = deshorten_url(db, url)
        except pymongo.errors.WriteError:
          continue
        if out_url:
          out_urls.append(out_url)
      db.tweets.update_one({'id': t['id']}, {'$set': {'deshorten': True}})
      #if len(out_urls):
        #db.tweets.update_one({'id': t['id']}, {'$set': {'urls': out_urls}})
  else:
    if options.user:
      cursor = db.users.find({'id': u['id'], 'url': {'$ne': None}}).batch_size(10)
    else:
      cursor = db.users.find({'url': {'$ne': None}}).batch_size(10)
    cnt = cursor.count()
    if verbose():
      cursor = Bar('Loading:', max=cnt, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(cursor)
    print u'Found {}'.format(cnt)
    for u in cursor:
      url = u['url']
      out_url = deshorten_url(db, url)
      #if out_url:
        #db.users.update_one(u, {'$set': {'url': out_url}})

