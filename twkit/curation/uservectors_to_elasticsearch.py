#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

from twkit import *
from elasticsearch import Elasticsearch
from twkit.utils import *
from progress.bar import Bar
from bson.json_util import dumps, loads
from twkit.analytics.stats import *
import optparse

user_features = [
  'seen_total', 'total_inferred', 'seen_greek_total',
  'seen_top_tweets', 'top_tweets_pcnt', 'top_intervals',
  'mention_indegree', 'mention_outdegree',
  'mention_inweight', 'mention_outweight',
  'mention_avg_inweight', 'mention_avg_outweight',
  'mention_out_in_ratio', 'mention_pcnt',
  'retweet_indegree', 'retweet_outdegree',
  'retweet_inweight', 'retweet_outweight',
  'retweet_avg_inweight', 'retweet_avg_outweight',
  'retweet_out_in_ratio', 'retweet_pcnt',
  'reply_indegree', 'reply_outdegree',
  'reply_inweight', 'reply_outweight',
  'reply_avg_inweight', 'reply_avg_outweight',
  'reply_out_in_ratio', 'replies_pcnt',
  'seen_replied_to', 'most_engaging_tweet',
  'plain_tweets',
  'number_of_languages', 'tweets_per_language',
  'fr_scanned_at', 'seen_fr', 'gr_fr', 'gr_fr_pcnt', 'tr_fr', 'tr_fr_pcnt',
  'fo_scanned_at', 'seen_fo', 'gr_fo', 'gr_fo_pcnt', 'tr_fo', 'tr_fo_pcnt',
  'fr_fo_jaccard', 'fr_and_fo', 'fr_or_fo', 'gr_fr_fo', 'gr_fr_fo_pcnt',
  'greek',
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
  'seen_urls', 'urls_per_tw', 'avg_edit_distance',
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

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids.")
  parser.add_option("--all", action="store_true", dest="all", default=False, help="Re-vectorize all stale vectors (older than 1 month)")
  (options, args) = parser.parse_args()
  verbose(options.verbose)

  es = Elasticsearch()
  db, api = init_state(ignore_api=True)

  es.indices.create(index='hashtags', ignore=400)
  es.indices.create(index='user_features', ignore=400)

  if options.all:
    count = db.uservectors.count()
    uservectors = db.uservectors.find()
  else:
    count = len(args)
    if options.ids:
      uservectors = (db.uservectors.find_one({'id': long(u)}) for u in args)
    else:
      uservectors = (db.uservectors.find_one({'screen_name_lower': u}) for u in args)

  if verbose():
    uservectors = Bar("Loading:", max=count, suffix = '%(index)d/%(max)d - %(eta_td)s').iter(uservectors)

  for v in uservectors:
    del v['_id']
    #for htc in v['most_common_hashtags']:
    #  ht = htc['hashtag']
    #  c = htc['count']
    #  doc = {'hashtag': ht, 'uid': v['id'], 'user': v['screen_name'], 'count': c} 
    #  es.index(index="hashtags", doc_type="dict", body=doc)
    #  
    u = { f: v[f] for f in user_features }
    es.index(index="user_features", doc_type="dict", id=v['id'], body=u)
    #for t in get_user_tweets(db, v['id'], None):
    #  del t['_id']
    #  es.index(index="user_tweets", doc_type="tweet", id=t['id'], body=t)
