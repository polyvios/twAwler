#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import re
import sys
import optparse
from progress.bar import Bar
from twkit.utils import *

def dumpuserimageedges(db, edgecnt, image, outf):
  for x in edgecnt:
    outf.write('{} {}\n'.format(x, image))
  edgecnt.clear()

def checkuser(db, src):
  srcu = lookup_user(db, uname=src)
  if srcu is None:
    for x in db.users.find({'screen_name': src}).collation({'locale': 'en', 'strength': 1}).limit(1):
      srcu = x
    if srcu is None:
      print("Unknown user:", src)
  return srcu



if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Make noise.")
  parser.add_option("-g", "--greek", action="store_true", dest="greek", default=False, help="Only get the part of the graph that is followed or marked greek")
  parser.add_option("-o", "--output", action="store", dest="filename", default='avatars.txt', help="Output file")
  parser.add_option("--query", action="store", dest="query", default="{}", help="Select who to vectorize")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Give list of ids")
  #parser.add_option("--bipartite", action="store_true", dest="bipartite", default=False, help="Output a bipartite graph between images and accounts")
  (options, args) = parser.parse_args()

  verbose(options.verbose)
  db, _ = init_state(use_cache=False, ignore_api=True)

  num = db.images.count()

  if options.ids:
    done_images = set('0000000009098-2019-01-26')
    users = (int(i) for i in args)
    if verbose():
      users = Bar("Greek:", max=len(args), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(users)
    with open(options.filename, "w") as outf:
      u1 = None
      u2 = None
      for uid in users:
        u = lookup_user(db, uid)
        uname = u['screen_name']
        for i in db.images.find({'screen_name': uname}):
          img = i['image']
          if img in done_images: continue
          for u in db.images.find({'image': img}).sort('screen_name', 1):
            if u1 == uname and u2 == u['screen_name']: continue
            u1 = uname
            u2 = u['screen_name']
            outf.write(u'{} {} {}\n'.format(u1, u2, img))
          done_images.add(img)
    sys.exit(0)


  if options.greek:
    done_images = set()
    greeks = db.greeks.find().batch_size(10)
    if verbose():
      greeks = Bar("Greek:", max=db.greeks.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(greeks)
    with open(options.filename, "w") as outf:
      u1 = None
      u2 = None
      for g in greeks:
        uname = g.get('screen_name')
        if uname is None:
          uname = db.users.find_one({'id': g['id']})['screen_name']
        for i in db.images.find({'screen_name': uname}):
          img = i['image']
          if img in done_images: continue
          for u in db.images.find({'image': img}).sort('screen_name', 1):
            if u1 == uname and u2 == u['screen_name']: continue
            u1 = uname
            u2 = u['screen_name']
            outf.write(u'{} {} {}\n'.format(u1, u2, img))
          done_images.add(img)
    sys.exit(0)

  if options.query:
    q = json.loads(options.query)
    if verbose():
      gprint(q)
    edges = db.images.find(q).sort('image', 1)
  else:
    edges = db.images.find({}).sort('image', 1).limit(1000)
  if verbose():
    edges = Bar("Processing:", max=num, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(edges)
  with open(options.filename, "w") as outf:
    edgecnt = set()
    lastuser = ''
    lastimage = ''
    for e in edges:
      src = e['screen_name']
      img = e['image']
      if src == lastuser and img == lastimage: continue
      if src != lastuser:
        dumpuserimageedges(db, edgecnt, lastimage, outf)
      lastuser = src
      lastimage = img
      edgecnt.add(src)
    dumpuserimageedges(db, edgecnt, lastimage, outf)

