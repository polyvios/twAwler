#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
Statistical analysis of tweets
This file recreates many feature engineering papers
It computes mostly features based on "over all tweets" computations.
"""

import re
import sys
import optparse
import emoji
from datetime import datetime
from collections import Counter, defaultdict
from sets import Set
from nltk.tokenize import TweetTokenizer
from nltk.metrics.distance import edit_distance
import calendar
import numpy
import operator
from urlparse import urlparse
from progress.bar import Bar
from itertools import izip
from twkit.utils import *

usage_times_attrs = [
  'seen_total', 'total_inferred', 'seen_greek_total',
  'deleted_tweets',
  'all_intervals',
  'seen_top_tweets', 'top_tweets_pcnt', 'top_intervals',
  'mention_indegree', 'mention_outdegree',
  'mention_inweight', 'mention_outweight',
  'mention_avg_inweight', 'mention_avg_outweight',
  'mention_out_in_ratio', 'mention_pcnt',
  'most_mentioned_users', 'most_mentioned_by',
  'retweet_indegree', 'retweet_outdegree',
  'retweet_inweight', 'retweet_outweight',
  'retweet_avg_inweight', 'retweet_avg_outweight',
  'retweet_out_in_ratio', 'retweet_pcnt',
  'most_retweeted_users', 'most_retweeted_by',
  'rt_intervals',
  'reply_indegree', 'reply_outdegree',
  'reply_inweight', 'reply_outweight',
  'reply_avg_inweight', 'reply_avg_outweight',
  'reply_out_in_ratio', 'replies_pcnt',
  'most_replied_to', 'most_replied_by',
  'reply_intervals',
  'seen_replied_to', 'most_engaging_tweet',
  'plain_tweets',
  'most_used_sources',
  'time_between_any', 'time_between_top', 'time_between_rt', 'time_between_replies',
  'tweets_per_hour_of_day', 'tweets_per_weekday', 'tweets_per_active_day', 'tweets_per_day',
  'last_tweeted_at', 'life_time', 'max_daily_interval',
  'number_of_languages', 'tweets_per_language',
  'last_month'
  ]
usage_times_buckets_sec = [1, 30, 60, 3600, 3600*24, 3600*24*7, 3600*24*30, 3600*24*365]


def log_event(d, lastd, quanta, intervals):
  if lastd is None: return None
  delta = d - lastd
  i = 0
  sec = delta.total_seconds()
  while(i < 8 and sec > usage_times_buckets_sec[i]): i+=1
  quanta[i] += 1
  intervals.append(sec)
  return sec

def get_all_tweets(db, criteria, batch=None):
  if criteria:
    tweets = db.tweets.find({'created_at' : criteria}).sort('created_at', 1)
  else:
    tweets = db.tweets.find().sort('created_at', 1)
  if batch:
    tweets = tweets.batch_size(batch)
  if verbose():
    return Bar("Loading:", max=tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  return tweets

cached_tweets={}
def get_user_tweets(db, userid, criteria, batch=None, cacheifsmall=True):
  global cached_tweets
  if cacheifsmall:
    if cached_tweets.get('uid', -1) == userid and 'tweets' in cached_tweets:
      # and cached_tweets.get('before', None) == before and cached_tweets.get('after', None) == after:
      return cached_tweets['tweets']
  if criteria:
    tweets = db.tweets.find({'user.id' : userid, 'created_at' : criteria }).sort('created_at', 1)
  else:
    tweets = db.tweets.find({'user.id' : userid}).sort('created_at', 1)
  if batch:
    tweets = tweets.batch_size(batch)
  count = tweets.count()
  if cacheifsmall:
    if count < 100000:
      cached_tweets.clear()
      cached_tweets['uid'] = userid
      #cached_tweets['before'] = before
      #cached_tweets['after'] = after
      cached_tweets['tweets'] = list(tweets)
      tweets = cached_tweets['tweets']
  if verbose():
    return Bar("Loading:", max=count, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  return tweets

def get_user_replies(db, userid, criteria):
  if criteria:
    tweets = db.tweets.find({'in_reply_to_user_id' : userid, 'created_at' : criteria})
  else:
    tweets = db.tweets.find({'in_reply_to_user_id' : userid})
  if verbose():
    return Bar("Loading replies:", max=tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  return tweets


def get_user_mentions(db, userid, criteria):
  if criteria:
    tweets = db.tweets.find({'user_mentions' : {'$elemMatch': {'id': userid}}, 'created_at' : criteria})
  else:
    tweets = db.tweets.find({'user_mentions' : {'$elemMatch': {'id': userid}}})
  if verbose():
    return Bar("Loading mentions:", max=tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  return tweets

def get_user_retweets(db, userid, criteria):
  """
  Returns tweets by other users that retweet tweets by the given user.
  """
  if criteria:
    tweets = db.tweets.find({'retweeted_status.user.id' : userid, 'created_at': criteria})
  else:
    tweets = db.tweets.find({'retweeted_status.user.id' : userid})
  if verbose():
    return Bar("Loading retweets:", max=tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  return tweets

def get_retweeters(db, uid, criteria):
  retweeters = Counter()
  for t in get_user_retweets(db, uid, criteria):
    retweeters[t['user']['id']] += 1
  return retweeters

def get_retweeted(db, uid, criteria):
  retweeted = Counter()
  for t in get_user_tweets(db, uid, criteria):
    if 'retweeted_status' not in t: continue
    retweeted[t['retweeted_status']['user']['id']] += 1
  return retweeted


def get_user_quoted_tweets(db, userid, criteria):
  """
  Returns tweets by other users that quote tweets by the given user.
  """
  if criteria:
    tweets = db.tweets.find({'quoted_status.user.id' : userid, 'created_at': criteria})
  else:
    tweets = db.tweets.find({'quoted_status.user.id' : userid})
  if verbose():
    return Bar("Loading quotes:", max=tweets.count(), suffix = '%(index)d/%(max)d - %(eta_td)s').iter(tweets)
  return tweets

def get_quoters(db, uid, criteria):
  """
  Returns users that have quoted the given user.
  """
  quoters = Counter()
  for t in get_user_quoted_tweets(db, uid, criteria):
    quoters[t['user']['id']] += 1
  return quoters

def get_quoted(db, uid, criteria):
  """
  Returns users quoted by the given user.
  """
  quoted = Counter()
  for t in get_user_tweets(db, uid, criteria):
    if 'quoted_status' not in t: continue
    quoted[t['quoted_status']['user']['id']] += 1
  return quoted



def fill_lastmonth_usage(db, u):
  lastday = u['last_tweeted_at'].replace(hour=0, minute=0, second=0, microsecond=0)
  monthstart = lastday - timedelta(days=30)
  lastmonth = {x: Counter() for x in range(0,31)}
  criteria = {}
  criteria['$lte'] = lastday
  criteria['$gte'] = monthstart
  for tweet in get_user_tweets(db, u['id'], criteria):
    d = tweet.get('created_at')
    if d is None: continue
    if d > monthstart:
      sec = int((d - monthstart).total_seconds())
      days = sec // 3600 // 24
      hours = sec // 3600 % 24
      lastmonth[days][hours] += 1
  u['last_month'] = [{'day': i, 'hour': j, 'count': lastmonth[i][j]} for i in lastmonth for j in lastmonth[i]]



def usage_times_stats(db, u, criteria):
  userid = u['id']

  hcnt = Counter({x: 0 for x in range(0, 24)})
  dcnt = Counter({x: 0 for x in range(0, 7)})

  allquanta = Counter()
  intervals = []
  lasttime = None

  max_daily_interval = Counter()
  tweets_per_day = Counter()

  topquanta = Counter()
  topintervals = []
  lasttoptime = None
  seentop = 0

  rtquanta = Counter()
  rtintervals = []
  lastrttime = None
  rtcnt = Counter()

  replyquanta = Counter()
  replyintervals = []
  lastreplytime = None
  replycnt = Counter()

  mentioncnt = Counter()

  sourcecnt = Counter()
  lastday = datetime.now()

  el_tweets = 0
  languages = Counter()
  plain_tweets = 0
  total = 0
  total_seen = 0
  deleted_tweets = 0

  if verbose(): print " scan tweets"
  for tweet in get_user_tweets(db, u['id'], criteria):
    total += 1
    if 'created_at' not in tweet: continue
    total_seen += 1
    d = tweet['created_at']
    if tweet.get('deleted', False):
      deleted_tweets += 1
    if 'lang' in tweet:
      if tweet['lang'] == config.lang: el_tweets += 1
      languages[tweet['lang']] += 1
    lastday = d
    sleepseconds = log_event(d, lasttime, allquanta, intervals)
    lasttime = d
    sourcecnt[tweet.get('source', 'empty_source_tag')] += 1
    day = d.replace(hour=0, minute=0, second=0, microsecond=0)
    tweets_per_day[day] += 1
    if sleepseconds:
      max_daily_interval[day] = max(max_daily_interval[day], sleepseconds)

    if 'retweeted_status' in tweet:
      rtid = tweet['retweeted_status']['user']['id']
      if rtid is None: raise "oops!"
      log_event(d, lastrttime, rtquanta, rtintervals)
      lastrttime = d
      rtcnt[rtid] += 1
    else: #orig user content, not RT
      if tweet.get('in_reply_to_user_id', None):
        log_event(d, lastreplytime, replyquanta, replyintervals)
        replycnt[tweet['in_reply_to_user_id']] += 1
        lastreplytime = d
      elif len(tweet.get('user_mentions', [])):
        #mentions that are not replies
        mentioncnt += Counter(x['id'] for x in tweet['user_mentions'] if x is not None)
      else:
        #top level tweets
        log_event(d, lasttoptime, topquanta, topintervals)
        seentop += 1
        lasttoptime = d
      if len(tweet.get('urls', [])) == 0 and len(tweet.get('user_mentions',[])) == 0 and len(tweet.get('hashtags', [])) == 0:
        plain_tweets += 1
    hcnt[d.hour] += 1
    dcnt[d.weekday()] += 1

  if verbose(): print " mentions"
  mentionbycnt = Counter()
  seenmentions = 0
  user_mentions = get_user_mentions(db, u['id'], criteria)
  for tweet in user_mentions:
    mentionbycnt[tweet['user']['id']] += 1
    seenmentions += 1

  if verbose(): print " retweets"
  rtbycnt = Counter()
  user_retweets = get_user_retweets(db, u['id'], criteria)
  for tweet in user_retweets:
    rtbycnt[tweet['user']['id']] += 1

  if verbose(): print " replies"
  user_replies = get_user_replies(db, u['id'], criteria)
  repliedcnt = Counter()
  repliedto = Counter()
  for tweet in user_replies:
    repliedcnt[tweet['user']['id']] += 1
    if 'in_reply_to_status_id' not in tweet:
      # if the replied-to tweet is deleted, twitter doesn't populate
      # the field
      #print "oops:",
      #gprint(tweet)
      continue
    repliedto[tweet['in_reply_to_status_id']] += 1
  most_engaging = repliedto.most_common(1)
  if len(most_engaging):
    most_engaging_tweet = db.tweets.find_one({'id': most_engaging[0]})
  else:
    most_engaging_tweet = None

  if verbose(): print " saving"
  #total = seentop + seenreplies + seenrt + seenmention
  qrange = range(0,len(usage_times_buckets_sec))
  u['seen_total'] = total_seen
  u['total_inferred'] = total
  total = total_seen
  u['seen_greek_total'] = el_tweets
  u['deleted_tweets'] = deleted_tweets
  u['number_of_languages'] = len(languages)
  u['tweets_per_language'] = [{'lang': i[0], 'count': i[1]} for i in languages.most_common(5)]
  u['all_intervals'] = [{'bucket': i, 'count': allquanta[i]} for i in qrange]
  if total == 0: total = 1 #avoid divzero
  u['seen_top_tweets'] = seentop
  u['top_tweets_pcnt'] = 100.0 * seentop / total
  u['top_intervals'] = [{'bucket': i, 'count': topquanta[i]} for i in qrange]

  u['mention_indegree'] = len(mentionbycnt)
  u['mention_outdegree'] = len(mentioncnt)
  u['mention_inweight'] = sum(mentionbycnt.values())
  u['mention_outweight'] = sum(mentioncnt.values())
  u['mention_avg_inweight'] = 1.0 * u['mention_inweight'] / max(1, u['mention_indegree'])
  u['mention_avg_outweight'] = 1.0 * u['mention_outweight'] / max(1, u['mention_outdegree'])
  u['mention_out_in_ratio'] = 1.0 * u['mention_outdegree'] / max(1, u['mention_indegree'])
  u['mention_pcnt'] = 100.0 * u['mention_outweight'] / total
  u['most_mentioned_users'] = [{'user': id_to_userstr(db, i[0]), 'count': i[1]} for i in mentioncnt.most_common(500)]
  u['most_mentioned_by'] = [{'user': id_to_userstr(db, i[0]), 'count': i[1]} for i in mentionbycnt.most_common(500)]

  u['retweet_indegree'] = len(rtbycnt)
  u['retweet_outdegree'] = len(rtcnt)
  u['retweet_inweight'] = sum(rtbycnt.values())
  u['retweet_outweight'] = sum(rtcnt.values())
  u['retweet_avg_inweight'] = 1.0 * u['retweet_inweight'] / max(1, u['retweet_indegree'])
  u['retweet_avg_outweight'] = 1.0 * u['retweet_outweight'] / max(1, u['retweet_outdegree'])
  u['retweet_out_in_ratio'] = 1.0 * u['retweet_outdegree'] / max(1, u['retweet_indegree'])
  u['retweet_pcnt'] = 100.0 * u['retweet_outdegree'] / total
  u['most_retweeted_by'] = [{'user': id_to_userstr(db, i[0]), 'count': i[1]} for i in rtbycnt.most_common(500)]
  u['most_retweeted_users'] = [{'user': id_to_userstr(db, i[0]), 'count': i[1]} for i in rtcnt.most_common(500)]
  u['rt_intervals'] = [{'bucket': i, 'count': rtquanta[i]} for i in qrange]

  u['reply_indegree'] = len(repliedcnt)
  u['reply_outdegree'] = len(replycnt)
  u['reply_inweight'] = sum(repliedcnt.values())
  u['reply_outweight'] = sum(replycnt.values())
  u['reply_avg_inweight'] = 1.0 * u['reply_inweight'] / max(1, u['reply_indegree'])
  u['reply_avg_outweight'] = 1.0 * u['reply_outweight'] / max(1, u['reply_outdegree'])
  u['reply_out_in_ratio'] = 1.0 * u['reply_outdegree'] / max(1, u['reply_indegree'])
  u['replies_pcnt'] = 100.0 * u['reply_outdegree'] / total
  u['most_replied_to'] = [{'user': id_to_userstr(db, i[0]), 'count': i[1]} for i in replycnt.most_common(500)]
  u['most_replied_by'] = [{'user': id_to_userstr(db, i[0]), 'count': i[1]} for i in repliedcnt.most_common(500)]
  u['reply_intervals'] = [{'bucket': i, 'count': replyquanta[i]} for i in qrange]
  u['seen_replied_to'] = len(repliedto)
  u['most_engaging_tweet'] = {'id': most_engaging_tweet['id'], 'text': most_engaging_tweet.get('text', '<not crawled>')} if most_engaging_tweet is not None else None

  u['plain_tweets'] = plain_tweets
  u['most_used_sources'] = [{'source': i[0], 'count': i[1]} for i in sourcecnt.most_common(500)]
  u['time_between_any'] = {
    'min': min(intervals) if len(intervals) else None,
    'max': max(intervals) if len(intervals) else None,
    'avg': numpy.mean(intervals) if len(intervals) else None,
    'med': numpy.median(intervals) if len(intervals) else None,
    'std': numpy.std(intervals) if len(intervals) else None
  }
  u['time_between_top'] = {
    'min': min(topintervals) if len(topintervals) else None,
    'max': max(topintervals) if len(topintervals) else None,
    'avg': numpy.mean(topintervals) if len(topintervals) else None,
    'med': numpy.median(topintervals) if len(topintervals) else None,
    'std': numpy.std(topintervals) if len(topintervals) else None
  }
  u['time_between_rt'] = {
    'min': min(rtintervals) if len(rtintervals) else None,
    'max': max(rtintervals) if len(rtintervals) else None,
    'avg': numpy.mean(rtintervals) if len(rtintervals) else None,
    'med': numpy.median(rtintervals) if len(rtintervals) else None,
    'std': numpy.std(rtintervals) if len(rtintervals) else None
  }
  u['time_between_replies'] = {
    'min': min(replyintervals) if len(replyintervals) else None,
    'max': max(replyintervals) if len(replyintervals) else None,
    'avg': numpy.mean(replyintervals) if len(replyintervals) else None,
    'med': numpy.median(replyintervals) if len(replyintervals) else None,
    'std': numpy.std(replyintervals) if len(replyintervals) else None
  }
  maxdinterval = max_daily_interval.values()
  u['max_daily_interval'] = {
    'min': min(maxdinterval),
    'minday': min(max_daily_interval, key=max_daily_interval.get),
    'max': max(maxdinterval),
    'maxday': max(max_daily_interval, key=max_daily_interval.get),
    'avg': numpy.mean(maxdinterval),
    'med': numpy.median(maxdinterval),
    'std': numpy.std(maxdinterval)
  } if len(maxdinterval) else {
    'min': None,
    'minday': None,
    'max': None,
    'avg': None,
    'med': None,
    'std': None
  }
  u['last_tweeted_at'] = lastday
  lifetime = long((lastday - u['created_at']).total_seconds())
  seconds = lifetime % 60
  minutes = (lifetime / 60) % 60
  hours = (lifetime / 3600) % 24
  days = lifetime / (3600 * 24) % 365
  years = lifetime / (3600 * 24 * 365)
  u['life_time'] = {
    'years': years,
    'days': days,
    'hours': hours,
    'minutes': minutes,
    'seconds': seconds
  }
  u['tweets_per_hour_of_day'] = [{'hour': i, 'count': hcnt[i]} for i in hcnt]
  u['tweets_per_weekday'] = [{'day': i, 'count': dcnt[i]} for i in dcnt]
  twdinterval = tweets_per_day.values()
  u['tweets_per_active_day'] = {
    'min': min(twdinterval) if len(twdinterval) else None,
    'minday': min(tweets_per_day, key=tweets_per_day.get) if len(twdinterval) else None,
    'max': max(twdinterval) if len(twdinterval) else None,
    'maxday': max(tweets_per_day, key=tweets_per_day.get) if len(twdinterval) else None,
    'avg': numpy.mean(twdinterval) if len(twdinterval) else None,
    'med': numpy.median(twdinterval) if len(twdinterval) else None,
    'std': numpy.std(twdinterval) if len(twdinterval) else None
  }
  startd = u['created_at'].replace(hour=0, minute=0, second=0, microsecond=0)
  endd = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
  while startd <= endd:
    if startd not in tweets_per_day:
      tweets_per_day[startd] = 0  #zero the missing ones
    startd = startd + timedelta(days=1)
  twdinterval = tweets_per_day.values() #now count all zero days
  u['tweets_per_day'] = {
    'min': min(twdinterval) if len(twdinterval) else None,
    'minday': min(tweets_per_day, key=tweets_per_day.get) if len(twdinterval) else None,
    'max': max(twdinterval) if len(twdinterval) else None,
    'maxday': max(tweets_per_day, key=tweets_per_day.get) if len(twdinterval) else None,
    'avg': numpy.mean(twdinterval) if len(twdinterval) else None,
    'med': numpy.median(twdinterval) if len(twdinterval) else None,
    'std': numpy.std(twdinterval) if len(twdinterval) else None
  }
  fill_lastmonth_usage(db, u)


# end



follower_stats_attrs = [
  'fr_scanned_at', 'seen_fr', 'gr_fr', 'gr_fr_pcnt', 'tr_fr', 'tr_fr_pcnt',
  'fo_scanned_at', 'seen_fo', 'gr_fo', 'gr_fo_pcnt', 'tr_fo', 'tr_fo_pcnt',
  'fr_fo_jaccard', 'fr_and_fo', 'fr_or_fo', 'gr_fr_fo', 'gr_fr_fo_pcnt',
  'greek' ]

def fill_follower_stats(db, u):
  totalfr = 0
  grfrcnt = 0
  trackedfr = 0
  #for fid in db.follow.find({'id': u['id']}).distinct('follows'):
  friends = set(get_friends(db, u['id']))
  followers = set(get_followers(db, u['id']))
  fr_fo_count = len(friends & followers)
  all_count = len(friends | followers)
  fr_fo_jaccard = 1.0 * fr_fo_count / (all_count if all_count > 0 else 1)
  fr_fo_gr = Counter()
  for fid in friends:
    if is_greek(db, fid):
      grfrcnt += 1
      fr_fo_gr[fid] += 1
    x = get_tracked(db, fid)
    if x:
      trackedfr += 1
    totalfr += 1
  totalfo = 0
  grfocnt = 0
  trackedfo = 0
  #for fid in db.follow.find({'follows': u['id']}).distinct('id'):
  for fid in followers:
    if is_greek(db, fid):
      grfocnt += 1
      fr_fo_gr[fid] += 1
    x = get_tracked(db, fid)
    if x:
      trackedfo += 1
    totalfo += 1
  frscan = is_recently_scanned(db, u['id'], 'friends')
  if frscan: frscan = frscan.replace(microsecond=0).isoformat()
  foscan = is_recently_scanned(db, u['id'], 'followers')
  gr_fr_fo = len(fr_fo_gr.keys())
  if foscan: foscan = foscan.replace(microsecond=0).isoformat()
  u['fr_scanned_at'] = frscan
  u['seen_fr'] = totalfr
  u['gr_fr'] = grfrcnt
  if totalfr == 0: totalfr = 1 #smoothing to avoid div by zero
  u['gr_fr_pcnt'] = 100.0*grfrcnt/totalfr
  u['tr_fr'] = trackedfr
  u['tr_fr_pcnt'] = 100*trackedfr/totalfr
  u['fo_scanned_at'] = foscan
  u['seen_fo'] = totalfo
  u['gr_fo'] = grfocnt
  if totalfo == 0: totalfo = 1 #smoothing to avoid div by zero
  u['gr_fo_pcnt'] = 100.0*grfocnt/totalfo
  u['tr_fo'] = trackedfo
  u['tr_fo_pcnt'] = 100.0*trackedfo/totalfo
  u['fr_fo_jaccard'] = fr_fo_jaccard
  u['fr_and_fo'] = fr_fo_count
  u['fr_or_fo'] = all_count
  u['gr_fr_fo'] = gr_fr_fo
  u['gr_fr_fo_pcnt'] = 100.0*gr_fr_fo / (all_count if all_count > 0 else 1)
  u['greek'] = is_greek(db, u['id'])


class itertext(object):
  def __init__(self, cursor):
    self.cursor = cursor
  def __iter__(self):
    return self
  def next(self):
    n = self.cursor.next()
    while 'text' not in n:
      n = self.cursor.next()
    text = n['text']
    res = re.sub(r'https?://[\S/]+', '', text, flags=re.MULTILINE)
    res = re.sub(r'@[a-zA-Z0-9_]+', '', res, flags=re.MULTILINE)
    res = re.sub(r'#\S+', '', res, flags=re.MULTILINE)
    res = re.sub(r'\b\d+\b', '', res, flags=re.MULTILINE)
    #res = re.sub('ς', 'σ', res)
    #print text.encode('utf-8')
    #print res.encode('utf-8')
    #print "-----"
    return res

def deaccent(s):
  return s \
    .replace(u'ά', u'α') \
    .replace(u'έ', u'ε') \
    .replace(u'ή', u'η') \
    .replace(u'ί', u'ι') \
    .replace(u'ό', u'ο') \
    .replace(u'ύ', u'υ') \
    .replace(u'ώ', u'ω') \
    .replace(u'ς', u'σ')

import os
crawlerdir = os.environ['CRAWLERDIR']

expletives = Set()
with open(crawlerdir+"greekdata/expletives", "r") as f:
  for line in f:
    expletives.add(deaccent(unicode(line, 'utf-8').strip().lower()))
articles = Set()
with open(crawlerdir+"greekdata/articles", "r") as f:
  for line in f:
    articles.add(deaccent(unicode(line, 'utf-8').strip().lower()))
pronouns = Set()
with open(crawlerdir+"greekdata/pronouns", "r") as f:
  for line in f:
    pronouns.add(deaccent(unicode(line, 'utf-8').strip().lower()))
locations = Set()
with open(crawlerdir+"greekdata/locations", "r") as f:
  for line in f:
    locations.add(deaccent(unicode(line, 'utf-8').strip().lower()))
negationwords = Set()
with open(crawlerdir+"greekdata/negationwords", "r") as f:
  for line in f:
    negationwords.add(deaccent(unicode(line, 'utf-8').strip().lower()))
emoticons = Set()
with open(crawlerdir+"greekdata/emoticons", "r") as f:
  for line in f:
    emoticons.add(deaccent(unicode(line, 'utf-8').strip().lower()))
stopwords = Set()
with open(crawlerdir+"greekdata/stopwords", "r") as f:
  for line in f:
    w = line.strip()
    stopwords.add(deaccent(unicode(line, 'utf-8').strip().lower()))
punctuation_chars = u'@![]...;:?«»"\'+-&()\\/,<>`´“”|*%…’'


def is_location(word):
  for l in locations:
    if re.match(l, word, re.I): return True
  return False

def letter_count(word):
  digit = 0
  alpha = 0
  upper = 0
  lower = 0
  greek = 0
  for i in word:
    if i.isdigit(): digit += 1
    if i.isalpha(): alpha += 1
    if i.islower(): lower += 1
    if i.isupper(): upper += 1
    if i.lower() in u'αβγδεζηθικλμνξοπρσςτυφχψωάέήίόύώϊϋΐΰ': greek += 1
  return digit, alpha, upper, lower, greek


def get_phrase_stats(tweetwords):
  allupper = 0
  alllower = 0
  allnumber = 0
  punctuation = 0
  digit = 0
  alpha = 0
  upper = 0
  lower = 0
  total = 0
  greek = 0
  for w in tweetwords:
    if w.isupper() and len(w) > 1: allupper += 1
    if w.islower(): alllower += 1
    if w in punctuation_chars : punctuation += 1
    total += len(w)
    d,a,u,l,g = letter_count(w)
    digit += d
    alpha += a
    upper += u
    lower += l
    greek += g
  return len(tweetwords), allupper, alllower, punctuation, digit, alpha, upper, lower, total, greek

def get_bigrams(wordlist):
  wordlist = [x for x in wordlist if deaccent(x.lower()) not in stopwords and deaccent(x.lower()) not in punctuation_chars and not emoji.get_emoji_regexp().match(x)]
  return zip(wordlist, wordlist[1:])

word_stats_attrs = [
  'total_words', 'min_wptw', 'avg_wptw', 'med_wptw', 'std_wptw',
  'unique_words', 'lex_freq',
  'total_bigrams', 'unique_bigrams', 'bigram_lex_freq',
  'articles', 'pronouns', 'expletives', 'locations', 'emoticons',
  'emoji', 'alltokens',
  'all_caps_words', 'all_caps_words_pcnt',
  'all_caps_tweets', 'all_caps_tweets_pcnt',
  'all_nocaps_words', 'all_nocaps_words_pcnt',
  'punctuation_chars', 'punctuation_pcnt',
  'total_chars',
  'digit_chars', 'digit_pcnt',
  'alpha_chars', 'alpha_pcnt',
  'upper_chars', 'upper_pcnt',
  'lower_chars', 'lower_pcnt',
  'greek_chars', 'greek_pcnt',
  'total_hashtags', 'hashtags_per_tw',
  'uniq_hashtags', 'total_rt_hashtags', 'uniq_rt_hashtags',
  'most_common_words', 'most_common_bigrams',
  'most_common_hashtags', 'most_common_rt_hashtags',
  'most_common_urls', 'most_common_rt_urls',
  'seen_urls', 'urls_per_tw', 'avg_edit_distance'
  ]

def unshort_url(db, url):
  cached = db.shorturl.find_one({'shorturl': url})
  if cached != None and cached['url'] != None:
    if cached['url'] == url:
      db.shorturl.delete_one({'shorturl': url})
    return unshort_url(db, cached['url'])
  return url

def fill_word_stats(db, u, criteria):
  tknzr = TweetTokenizer(strip_handles=True, reduce_len=True)
  own_tweets = []
  rturlcnt = Counter()
  urlcnt = Counter()
  urlpertw = []
  tagcnt = Counter()
  tagpertw = []
  rttags = []
  words = []
  url_to_name = []
  uname = u['screen_name'].lower()
  for t in get_user_tweets(db, u['id'], criteria, batch=1000):
    if 'retweeted_status' in t:
      if 'urls' in t['retweeted_status'] and t['retweeted_status']['urls'] is not None:
        rturlcnt += Counter(urlparse(unshort_url(db, i)).netloc for i in t['retweeted_status'].get('urls',[]))
      if 'hashtags' in t['retweeted_status']:
        rttags.append(t['retweeted_status']['hashtags'])
    else:
      if 'urls' in t and t['urls'] is not None:
        urlcnt += Counter(urlparse(unshort_url(db, i)).netloc for i in t['urls'])
        url_to_name.extend(edit_distance(urlparse(unshort_url(db, i)).netloc, uname) for i in t['urls'])
        urlpertw.append(len(t['urls']))
      else:
        urlpertw.append(0)
      if 'hashtags' in t:
        tagcnt += Counter(t['hashtags'])
        tagpertw.append(len(t['hashtags']))
      else:
        tagpertw.append(0)
      if 'text' in t:
        own_tweets.append({'text': t['text']})

  if verbose(): print " tokenize"
  words = [tknzr.tokenize(s) for s in itertext(iter(own_tweets))]
  wcounts = [len(s) for s in words]

  #tagfreq = Counter(t for s in tags for t in s)
  #tagpertw = [len(s) for s in tags]
  uniqtags = len(tagcnt)
  totaltags = sum(tagcnt.values())

  rttagfreq = Counter(t for s in rttags for t in s)
  uniqrtags = len(rttagfreq)
  totalrtags = sum(rttagfreq.values())

  if verbose(): print " wc"
  artcnt  = 0
  proncnt = 0
  explcnt = 0
  loccnt = 0
  emocnt = 0
  emojicnt = 0
  tw = 0
  tuw = 0
  tu2w = 0
  t2w = 0
  ustat = [0]*10
  wc = Counter()
  bifreq = Counter()
  capstweets = 0

  try:
    if verbose(): print "  words"
    capstweets = sum(1 if all(w.isupper() for w in s) else 0 for s in words)
    wc = Counter(w for s in words for w in s)
    bigrams = (get_bigrams(s) for s in words)
    twstat = (get_phrase_stats(s) for s in words)
    ustat = reduce(lambda x, y: tuple(map(operator.add, x, y)), twstat)
    if verbose(): print "  bigrams"
    bc = Counter(b for s in bigrams for b in s)
    if verbose(): print "  dicts"
    tuw = len(wc)
    tw = sum(wc.values())
    tu2w = len(bc)
    t2w = sum(bc.values())
    if verbose(): print "  freqs"
    bifreq = bc
    if verbose(): print "  pos"
    for w,i in wc.iteritems():
      wd = deaccent(w.lower())
      if wd in expletives: explcnt += i
      if wd in articles: artcnt += i
      if wd in pronouns: proncnt += i
      if is_location(wd): loccnt += i
      if wd in emoticons: emocnt += i
      if emoji.get_emoji_regexp().match(wd):
        emojicnt += i
        wc[w] = 0
      if wd in stopwords: wc[w] = 0 #do not count stopwords
      if wd in punctuation_chars: wc[w] = 0 #do not count punctuation
  except:
    pass

  seen_own = len(own_tweets)
  if seen_own == 0: seen_own = 1 #for division
  if verbose(): print " saving"
  u['total_words'] = tw
  if tw == 0: tw = 1 # avoid divzero
  u['min_wptw'] = min(wcounts) if len(wcounts) else 0
  u['avg_wptw'] = numpy.mean(wcounts) if len(wcounts) else 0
  u['med_wptw'] = numpy.median(wcounts) if len(wcounts) else 0
  u['std_wptw'] = numpy.std(wcounts) if len(wcounts) else 0
  u['unique_words'] = tuw
  u['lex_freq'] = 1.0*tuw/tw
  u['total_bigrams'] = t2w
  if t2w == 0: t2w = 1 # avoid divzero
  u['unique_bigrams'] = tu2w
  u['bigram_lex_freq'] = 1.0*tu2w/t2w
  u['articles'] = artcnt
  u['pronouns'] = proncnt
  u['expletives'] = explcnt
  u['locations'] = loccnt
  u['emoticons'] = emocnt
  u['emoji'] = emojicnt
  u['alltokens'] = ustat[0]
  u['all_caps_words'] = ustat[1]
  u['all_caps_words_pcnt'] = 100.0*ustat[1]/tw
  u['all_caps_tweets'] = capstweets
  u['all_caps_tweets_pcnt'] = 100.0*capstweets/seen_own
  u['all_nocaps_words'] = ustat[2]
  u['all_nocaps_words_pcnt'] = 100.0*ustat[2]/tw
  u['punctuation_chars'] = ustat[3]
  u['total_chars'] = ustat[8]
  u['punctuation_pcnt'] = 100.0*ustat[3]/max(ustat[8], 1)
  u['digit_chars'] = ustat[4]
  u['digit_pcnt'] = 100.0*ustat[4]/max(ustat[8], 1)
  u['alpha_chars'] = ustat[5]
  u['alpha_pcnt'] = 100.0*ustat[5]/max(ustat[8], 1)
  u['upper_chars'] = ustat[6]
  u['upper_pcnt'] = 100.0*ustat[6]/max(ustat[8], 1)
  u['lower_chars'] = ustat[7]
  u['lower_pcnt'] = 100.0*ustat[7]/max(ustat[8], 1)
  u['greek_chars'] = ustat[9]
  u['greek_pcnt'] = 100.0*ustat[9]/max(ustat[8], 1)
  u['total_hashtags'] = totaltags
  u['hashtags_per_tw'] = {
    'min': min(tagpertw) if len(tagpertw) else None,
    'max': max(tagpertw) if len(tagpertw) else None,
    'avg': numpy.mean(tagpertw) if len(tagpertw) else None,
    'med': numpy.median(tagpertw) if len(tagpertw) else None,
    'std': numpy.std(tagpertw) if len(tagpertw) else None
  }
  u['uniq_hashtags'] = uniqtags
  u['total_rt_hashtags'] = totalrtags
  u['uniq_rt_hashtags'] = uniqrtags
  u['most_common_words'] = [{'word': i[0], 'count': i[1]} for i in wc.most_common(500)]
  u['most_common_bigrams'] = [{'bigram': ' '.join(i[0]), 'count': i[1]} for i in bifreq.most_common(500)]
  u['most_common_hashtags'] = [{'hashtag': i[0], 'count': i[1]} for i in tagcnt.most_common(500)]
  u['most_common_rt_hashtags'] = [{'hashtag': i[0], 'count': i[1]} for i in rttagfreq.most_common(500)]
  u['most_common_urls'] = [{'url': i[0], 'count': i[1]} for i in urlcnt.most_common(500)]
  u['most_common_rt_urls'] = [{'url': i[0], 'count': i[1]} for i in rturlcnt.most_common(500)]
  u['seen_urls'] = sum(urlcnt.values())
  u['urls_per_tw'] = {
    'min': min(urlpertw) if len(urlpertw) else None,
    'max': max(urlpertw) if len(urlpertw) else None,
    'avg': numpy.mean(urlpertw) if len(urlpertw) else None,
    'med': numpy.median(urlpertw) if len(urlpertw) else None,
    'std': numpy.std(urlpertw) if len(urlpertw) else None
  }
  u['avg_edit_distance'] = numpy.mean(url_to_name) if len(url_to_name) else None



user_metadata_attrs = [
  'id',
  'screen_name', 'screen_name_len', 'screen_name_upper',
  'screen_name_lower', 'screen_name_digit', 'screen_name_alpha',
  'name', 'name_len', 'name_upper', 'name_lower', 'name_digit',
  'name_alpha', 'name_greek',
  'created_at', 'tweet_count', 'favourites_count',
  'followers_count', 'friends_count', 'fr_fo_ratio',
  'location', 'has_location', 'time_zone', 'lang',
  'protected', 'verified', 'dead', 'suspended',
  'user_url',
  'bio_words', 'bio_upper_words', 'bio_lower_words',
  'bio_punctuation_chars', 'bio_digit_chars', 'bio_alpha_chars',
  'bio_upper_chars', 'bio_lower_chars', 'bio_greek_chars',
  'bio_total_chars'
  ]


def fill_metadata_stats(db, u):
  u2 = lookup_user(db, u['id'])
  digit, alpha, upper, lower, greek = letter_count(u2['screen_name'])
  assert(greek == 0)
  (bio_words, bio_upper_words, bio_lower_words, bio_punctuation_chars,
    bio_digit_chars, bio_alpha_chars, bio_upper_chars, bio_lower_chars,
    bio_total_chars, bio_greek_chars) = get_phrase_stats(u2['description'].split()) if 'description' in u2 else (None,) * 10
  totalfo = u2.get('followers_count', 0)
  totalfr = u2.get('friends_count', 0)
  u['screen_name'] = u2['screen_name']
  u['screen_name_len'] = len(u2['screen_name'])
  u['screen_name_upper'] = upper
  u['screen_name_lower'] = lower
  u['screen_name_digit'] = digit
  u['screen_name_alpha'] = alpha
  u['name'] = u2.get('name', None)
  digit, alpha, upper, lower, greek = letter_count(u2.get('name', u''))
  u['name_len'] = len(u2.get('name',''))
  u['name_upper'] = upper
  u['name_lower'] = lower
  u['name_digit'] = digit
  u['name_alpha'] = alpha
  u['name_greek'] = greek
  u['created_at'] = u2.get('created_at', datetime.now())
  u['tweet_count'] = u2.get('statuses_count', 0)
  u['favourites_count'] = u2.get('favourites_count', 0)
  u['followers_count'] = totalfo
  u['friends_count'] = totalfr
  if totalfo == 0: totalfo = 1 # smoothing to avoid division by zero
  u['fr_fo_ratio'] = 1.0*totalfr/totalfo
  u['location'] = u2.get('location', None)
  u['has_location'] = ('location' in u2)
  u['time_zone'] = u2.get('time_zone', None)
  u['lang'] = u2.get('lang', None)
  u['protected'] = u2.get('protected', False)
  u['verified'] = u2.get('verified', False)
  u['dead'] = is_dead(db, u['id'])
  u['suspended'] = is_suspended(db, u['id'])
  u['user_url'] = u2.get('url', None)
  u['bio_words'] = bio_words
  u['bio_upper_words'] = bio_upper_words
  u['bio_lower_words'] = bio_lower_words
  u['bio_punctuation_chars'] = bio_punctuation_chars
  u['bio_digit_chars'] = bio_digit_chars
  u['bio_alpha_chars'] = bio_alpha_chars
  u['bio_upper_chars'] = bio_upper_chars
  u['bio_lower_chars'] = bio_lower_chars
  u['bio_greek_chars'] = bio_greek_chars
  u['bio_total_chars'] = bio_total_chars
  #u['censored_somewhere'] = u2.get('withheld_in_countries', '') != ''


favoriter_attrs = [
  'favoriters', 'favorited',
  'most_favoriters', 'most_favorited'
]

def get_favoriters(db, uid):
  favoriters = defaultdict(lambda: [])
  if verbose(): sys.stderr.write(u'Fav graph for user {}/{}\n'.format(uid, id_to_userstr(db, uid)))
  for tw in get_user_tweets(db, uid, None, None):
    for faver in db.favorites.find({'tweet_id': tw['id']}):
      favoriters[faver['user_id']].append(tw['id'])
  return favoriters

def get_favorited(db, uid):
  favorited = defaultdict(lambda: [])
  for faved in db.favorites.find({'user_id': uid}):
    twid = faved['tweet_id']
    tw = db.tweets.find_one({'id': twid}) 
    if tw is None:
      if verbose(): print "missing tweet {}".format(twid)
      continue
    if 'user' in tw:
      twuid = tw['user']['id']
      favorited[twuid].append(twid)
  return favorited

def fill_favoriter_stats(db, u):
  f = Counter({k: len(v) for k,v in get_favoriters(db, u['id']).iteritems()})
  u['favoriters'] = len(f)
  u['most_favoriters'] = [{'user': id_to_userstr(db, i[0]), 'count': i[1]} for i in f.most_common(500)]
  fd = Counter({k: len(v) for k,v in get_favorited(db, u['id']).iteritems()})
  u['favorited'] = len(fd)
  u['most_favorited'] = [{'user': id_to_userstr(db, i[0]), 'count': i[1]} for i in fd.most_common(500)]

if __name__ == '__main__':
  #print("used as library only")
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids.")
  parser.add_option("-b", "--before", action="store", dest="before", default=False, help="Before given date.")
  parser.add_option("-a", "--after", action="store", dest="after", default=False, help="After given date.")
  (options, args) = parser.parse_args()

  verbose(options.verbose)

  criteria = {}
  if options.before:
    criteria['$lte'] = dateutil.parser.parse(options.before)
  if options.after:
    criteria['$gte'] = dateutil.parser.parse(options.after)

  if len(args) == 0:
    parser.print_help()
    sys.exit(1)

  db, api = init_state(True, ignore_api=True)
  userlist = [x.lower().replace("@", "") for x in args]
  for user in userlist:
    uid = long(user) if options.ids else None
    uname = None if options.ids else user
    u = get_tracked(db, uid, uname)
    if u == None:
      x = lookup_user(db, uid, uname)
      if x:
        u = { 'id': x['id'], 'screen_name_lower': x['screen_name'].lower() }
      else:
        print "unknown user:", uid, uname
        continue
  #  fill_word_stats(db, u, True)
  #  fill_follower_stats(db, u, True)
    usage_times_stats(db, u, criteria, True)
    gprint(u)

