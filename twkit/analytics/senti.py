#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

import sys
from nltk.tokenize import TweetTokenizer
from twkit.utils import *
from twkit.analytics.stats import *
from twkit.analytics.stem import stem as external_stemmer1
import csv
import optparse
import itertools
from collections import defaultdict, Counter
from greekdict import WikiWordGraph
import dateutil.parser

def external_stemmer(w):
  """
  This is a dummy function taking the place of external_stemmer1 based
  on ntais' stemmer for the greek language.
  I am not committing that code in twawler's public repository, as it
  is not mine.
  """
  try:
    return external_stemmer1(w)
  except:
    return w[:-1] if len(w) > 3 else w


# Smart word dictionary
# Gets a word and looks it up in a dictionary.
# If nothing comes up, try look up "root" form in the wiktionary wrapper above.
# If nothing comes up, try all-lowercase.
# If nothing comes up, try removing all accents.
# If nothing comes up, try the external_stemmer written by Spiliotopoulos, similar to Ntais' stemmer.
# else, return "zeroval" argument.
class WordLookup(object):
  def __init__(self, word_graph, exact, zeroval = None, use_stem = False, use_deaccent = True):
    self.word_graph = word_graph
    self.zeroval = zeroval
    self.use_stem = use_stem
    self.use_deaccent = use_deaccent
    self.exact = exact
    self.lower = {}
    self.accen = {}
    self.stemd = {}
    for key, value in self.exact.items():
      #self.exact[key] = value
      #don't lower ground truth, capitalization in truth stays fixed, allows for capturing e.g. first names.
#      key = key.lower()
      self.lower[key] = value
      key = deaccent(key)
      self.accen[key] = value
      key = external_stemmer(key)
      self.stemd[key] = value

  def analyze1(self, key):
    key_exact = key
    if key_exact in self.exact: return self.exact[key_exact]
    key_lower = key_exact.lower()
    if key_lower in self.lower: return self.lower[key_lower]
    key_accen = deaccent(key_lower)
    if self.use_deaccent:
      if key_accen in self.accen: return self.accen[key_accen]
    key_stemd = external_stemmer(key_accen)
    if self.use_stem:
      if key_stemd in self.stemd: return self.stemd[key_stemd]
    return self.zeroval

  def analyze(self, key, reducer=None):
    wiki_keys = self.word_graph[key]
    wiki_vals = []
    v = self.analyze1(key)
    if v != self.zeroval:
      wiki_vals.append(v)
    for x in wiki_keys:
      v = self.analyze1(x)
      if v != self.zeroval and v not in wiki_vals:
        wiki_vals.append(v)
    if reducer: return reduce(reducer, wiki_vals, self.zeroval)
    else:
      if wiki_vals != self.zeroval:
        return wiki_vals
      return self.zeroval


# sentiment analysis
class GrSentimentAnalysis(object):
  def __init__(self, lexicon_filename, word_graph):
    self.tknzr = TweetTokenizer(strip_handles=True, reduce_len=True)
    self.word_graph = word_graph
    self.senti_words_exact = {}
    self.senti_words_lower = {}
    self.senti_words_accen = {}
    #self.senti_words_stem = {}
    self.senti_ngrams_exact = {}
    self.senti_ngrams_lower = {}
    self.senti_ngrams_accen = {}
    #self.senti_ngrams_stem = {}
    with open(lexicon_filename, 'r') as csvfile:
      vectorreader = csv.DictReader(csvfile)
      for v in vectorreader:
        key = v['InitialTerm']
        if key[0] == u'#': continue
        value = int(v['Sentiment'])
        if key in self.senti_words_exact:
          if verbose(): print(u'Ignoring duplicate sentiment pattern: {} : {}, already assigned {}'.format(key, value, self.senti_words_exact[key]))
          continue
        self.senti_words_exact[key] = value
        key = key.lower()
        self.senti_words_lower[key] = value
        key = deaccent(key)
        self.senti_words_accen[key] = value
        #key = external_stemmer(key)
        #self.senti_words_stem[key] = value
        key_words = key.split()
        if len(key_words) > 2:
          self.senti_ngrams_exact[key] = value
          key = key.lower()
          self.senti_ngrams_lower[key] = value
          key = deaccent(key)
          self.senti_ngrams_accen[key] = value
          #key = u' '.join([external_stemmer(w) for w in key.split()])
          #self.senti_ngrams_stem[key] = value
         
  def analyze_slow(self, text):
    words_exact = self.tknzr.tokenize(text)
    words_lower = [w.lower() for w in words_exact]
    words_accen = [deaccent(w) for w in words_lower]
    #words_stem = [external_stemmer(w) for w in words_accen]
    words_wiki = [self.word_graph.get(w) for w in words_exact]
    senti_scores_exact = [self.senti_words_exact.get(w, 0) for w in words_exact]
    senti_scores_lower = [self.senti_words_lower.get(w, 0) for w in words_lower]
    senti_scores_accen = [self.senti_words_accen.get(w, 0) for w in words_accen]
    #senti_scores_stem = [self.senti_words_stem.get(w, 0) for w in words_stem]
    senti_scores_wiki = [[self.senti_words_exact.get(w, 0) for w in l] if l else [] for l in words_wiki]
    senti_scores_wiki_avg = [numpy.mean(s) if len(s) else 0 for s in senti_scores_wiki]
    #bigrams = zip(words_exact, words_exact[1:])
    #bigrams_exact = [' '.join(x) for x in bigrams]
    #bigrams_lower = [w.lower() for w in bigrams_exact]
    #bigrams_accen = [deaccent(w) for w in bigrams_lower]
    #bigrams_stem = [' '.join([external_stemmer(x) for x in w.split()]) for w in bigrams_accen]
    #bigram_scores_exact = [self.senti_ngrams_exact.get(w, 0) for w in bigrams_exact]
    #bigram_scores_lower = [self.senti_ngrams_lower.get(w, 0) for w in bigrams_lower]
    #bigram_scores_accen = [self.senti_ngrams_accen.get(w, 0) for w in bigrams_accen]
    #bigram_scores_stem = [self.senti_ngrams_stem.get(w, 0) for w in bigrams_stem]
    #trigrams = zip(words_exact, words_exact[1:], words_exact[2:])
    if verbose():
      for i in xrange(len(words_exact)):
        print(u'{} '.format(words_exact[i]).encode('utf-8'), end='')
        if senti_scores_exact[i]: print(u'ex({}:{})'.format(words_exact[i], senti_scores_exact[i]).encode('utf-8'), end=' ')
        if senti_scores_lower[i]: print(u'lo({}:{})'.format(words_lower[i], senti_scores_lower[i]).encode('utf-8'), end=' ')
        if senti_scores_accen[i]: print(u'ac({}:{})'.format(words_accen[i], senti_scores_accen[i]).encode('utf-8'), end=' ')
        #if senti_scores_stem[i]: print(u'st({}:{})'.format(words_stem[i], senti_scores_stem[i]).encode('utf-8'), end=' ')
        if senti_scores_wiki[i]:
          print(u'wiki', end=' ')
          for j,k in zip(words_wiki[i], senti_scores_wiki[i]):
            print(u'({}:{})'.format(j,k).encode('utf-8'), end=' ')
          print(u'endwiki', end=' ')
        print(u'')
    senti_all = zip(
      senti_scores_exact,
      senti_scores_wiki_avg,
      senti_scores_lower,
      senti_scores_accen)#, senti_scores_stem)
    senti_scores = [ next((x for x in list(s) if x != 0), 0) for s in senti_all ]
    positives = [s for s in senti_scores if s > 0]
    negatives = [s for s in senti_scores if s < 0]
    senti_pos = numpy.mean(positives) if len(positives) else 0
    senti_neg = numpy.mean(negatives) if len(negatives) else 0
    return senti_pos, senti_neg

  def analyze(self, text):
    senti_scores = []
    wordswiki = []
    wordslower = []
    wordsaccent = []
    #wordsstem = []
    wordsleft = []
    for w in self.tknzr.tokenize(text):
      s = self.senti_words_exact.get(w)
      if s:
        senti_scores.append(s)
      else:
        wordswiki.append(w)
    for w in wordswiki:
      ww = self.word_graph.get(w)
      if ww and len(ww):
        s = numpy.mean([self.senti_words_exact.get(w2, 0) for w2 in ww])
        if s:
          senti_scores.append(s)
      else:
        wordslower.append(w)
    for w in wordslower:
      s = self.senti_words_exact.get(w.lower())
      if s:
        senti_scores.append(s)
      else:
        wordsaccent.append(w)
    for w in wordsaccent:
      s = self.senti_words_exact.get(deaccent(w.lower()))
      if s:
        senti_scores.append(s)
      else:
        wordsleft.append(w)
    #for w in wordsstem:
    #  s = self.senti_words_exact.get(external_stemmer(w))
    #  if s:
    #    senti_scores.append(s)
    #  else:
    #    wordsleft.append(w)
    positives = [s for s in senti_scores if s > 0]
    negatives = [s for s in senti_scores if s < 0]
    senti_pos = numpy.mean(positives) if len(positives) else 0
    senti_neg = numpy.mean(negatives) if len(negatives) else 0
    #print(wordsleft)
    return senti_pos, senti_neg
   
# end class

class Entity(object):
  def __init__(self, key):
    if key[0] == u'#': key = key[1:]
    self.key = key
    self.count_norm = 0
    self.count = 0
    self.overlap_count = Counter()
    #self.sentiment = (0.0, 0.0)
  def visit(self, weight):
    #if word == self.key:
    self.count_norm += weight
    self.count += 1
    return 1
  def coexists_with(self, word, weight):
    if word == self.key: return #do not count myself
    self.overlap_count[word] += weight
# end class

class EntityAnalysis(object):
  def __init__(self, entity_dict, word_graph):
    self.tknzr = TweetTokenizer(strip_handles=True, reduce_len=True)
    self.word_graph = word_graph
    self.entities = {}
    #self.entity_by_word = {}
    self.entity_lookup = {}
    for key, values in entity_dict.items():
      if key[0] == u'#':
        key = key[1:]
      self.entities[key] = Entity(key)
      if key in self.entity_lookup:
        print(u'double key entry for {}'.format(key).encode('utf-8'))
      else:
        self.entity_lookup[key] = [key]
      for v in values:
        if v in self.entity_lookup:
          if key not in self.entity_lookup[v]:
            if verbose(): print(u'double entry for different keys (count will be evenly distributed)! {} {} {}'.format(v, key, self.entity_lookup[v]).encode('utf-8'))
            self.entity_lookup[v].append(key)
          else:
            if verbose(): print(u'double entry for {}'.format(v).encode('utf-8'))
        else:
          self.entity_lookup[v] = [key]
    self.lookup = WordLookup(self.word_graph, self.entity_lookup, zeroval=[], use_stem=False)

  def analyze(self, text):
    #for now, do not differentiate hashtags
    words_exact = [w[1:] if w[0] == u'#' else w for w in self.tknzr.tokenize(text)]
    tw_entities = []
    for w in words_exact:
      for l in self.lookup.analyze(w):
        if l not in tw_entities:
          tw_entities.append(l)
    flat_list = [x for l in tw_entities for x in l]
    if len(flat_list):
      weight = 1.0/len(flat_list)
      for k in flat_list:
        ent = self.entities[k]
        ent.visit(weight)
      for k1, k2 in itertools.permutations(flat_list, 2):
        e1 = self.entities[k1]
        e1.coexists_with(k2, 1)
    return flat_list

  def dump(self):
    for key,value in self.entities.items():
      print(u'{}: seen {} times, normalized {} times '.format(key, value.count, value.count_norm).encode('utf-8'))
      print(value.overlap_count)
      print(u'---')
      
# end class


word_graph = None
part_of_speech = None
sentiment_analysis = None

def get_word_graph():
  global word_graph
  if word_graph is None:
    if verbose(): print("{} loading word graph".format(datetime.utcnow()))
    word_graph = WikiWordGraph('data/word_graph.json')
  return word_graph


def get_sentiment_analysis():
  global sentiment_analysis
  if sentiment_analysis is None:
    sentiment_analysis = GrSentimentAnalysis("greekdata/lexicon.csv", get_word_graph())
  return sentiment_analysis


user_sentiment_attrs = [
  'daily_sentiment',
  'entity_overlap',
  'senti_entities'
  ]


def compute_sentiment(db, tweets, entity_file):
  word_graph = get_word_graph()
  sentiment_analysis = get_sentiment_analysis()

  with open(entity_file, 'r') as f:
    a = EntityAnalysis(json.load(f), word_graph)

  daily_sentiment = defaultdict(lambda: (0.0, 0.0, 0))
  entity_sentiment = defaultdict(lambda: (0.0, 0.0, 0))
  daily_entity_sentiment = defaultdict(lambda: defaultdict(lambda: (0.0, 0.0, 0)))
  for tw in tweets:
    if 'text' not in tw: continue
    day = tw['created_at'].replace(hour=0, minute=0, second=0, microsecond=0) #daily
    sentiment = sentiment_analysis.analyze(tw['text'])
    #sentiment2 = sentiment_analysis.analyze1(tw['text'])
    #print("compare:", sentiment, sentiment2)
    entlist = a.analyze(tw['text'])
    if sentiment != (0.0, 0.0, 0):
      daily_sentiment[day] = tuple_add(daily_sentiment[day], sentiment + (1,))
      #uncomment next 3 to split tweet sentiment over all tweet entities, instead of double-counting it
      #if len(entlist):
        #weight = 1.0/len(entlist)
        #sentiment = [s*weight for s in sentiment]
      for e in entlist:
        entity_sentiment[e] = tuple_add(entity_sentiment[e], sentiment + (1,))
        daily_entity_sentiment[day][e] = tuple_add(daily_entity_sentiment[day][e], sentiment + (1,))
  return daily_sentiment, entity_sentiment, daily_entity_sentiment, a


def fill_user_sentiment(db, u, criteria, entity_file):
  user_tweets = get_user_tweets(db, u['id'], criteria)
  daily_sentiment, entity_sentiment, daily_entity_sentiment, a = compute_sentiment(db, user_tweets, entity_file)
  if verbose(): print(" saving")
  u['daily_sentiment'] = [
    { 
      'day': day,
      'sentiment' : (daily_sentiment[day][0]/daily_sentiment[day][2], daily_sentiment[day][1]/daily_sentiment[day][2]),
      'per_entity': [
        {
          'entity': e,
          'sentiment' : (s[0]/s[2], s[1]/s[2])
        } for e, s in row.items()
      ]
    } for day, row in sorted(daily_entity_sentiment.items())
  ]
  #elist = [a.entities[x] for x in set([x for e in a.entities.values() for x in e.overlap_count.keys()])]
  elist = [a.entities[x[0]] for x in Counter([x for e in a.entities.values() for x in e.overlap_count.keys()]).most_common(500)]
  u['entity_overlap'] = {
    'nodes' : [
      {
        'entity': e.key,
        'count' : e.count
      } for e in elist
    ],
    'links' : [
      {
        'source': elist.index(e),
        'target': elist.index(a.entities[e2]),
        'value': cnt
      } for e in elist for e2, cnt in e.overlap_count.items() if a.entities[e2] in elist
    ]
  }
  u['senti_entities'] = [
    {
      'entity': e,
      'sentiment' : (s[0]/s[2], s[1]/s[2])
    } for e, s in sorted(entity_sentiment.items(), key=lambda i: int(numpy.ceil((i[1][0] - i[1][1]))))
  ]
  return daily_entity_sentiment


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="List names of tracked users")
  parser.add_option("--id", action="store_true", dest="ids", default=False, help="Input is user ids.")
  parser.add_option("--tweet", action="store_true", dest="onetweet", default=False, help="Analyze one tweet.")
  parser.add_option("-b", "--before", action="store", dest="before", default=False, help="Before given date.")
  parser.add_option("-a", "--after", action="store", dest="after", default=False, help="After given date.")
  parser.add_option("-e", "--entities", action="store", dest="entity_file", default='greekdata/entities.json', help="File with entities (def: greekdata/entities.json).")
  (options, args) = parser.parse_args()
  db, api = init_state(True)

  verbose(options.verbose)

  criteria = {}
  if options.before:
    criteria['$lte'] = dateutil.parser.parse(options.before)
  if options.after:
    criteria['$gte'] = dateutil.parser.parse(options.after)

  if options.onetweet:
    s = compute_sentiment(db, db.tweets.find({'id': int(args[0])}), options.entity_file)
    print(s)
    sys.exit(0)

  userlist = [x.lower().replace("@", "") for x in args]
  for userstr in userlist:
    uid = int(userstr) if options.ids else None
    uname = None if options.ids else userstr
    u = lookup_user(db, uid, uname)
    if u is None:
      if verbose(): print(u'Skipping unknown user: {}'.format(userstr))
      continue
    #user_tweets = get_user_tweets(db, u['id'], criteria)
    fill_user_sentiment(db, u, criteria, options.entity_file)
    print(u)
    #poscnt = {}
    #negcnt = {}
    #for (d, (senti_pos, senti_neg)) in daily_sentiment.items():
    #  poscnt[d] = poscnt.get(d, []) + [senti_pos]
    #  negcnt[d] = negcnt.get(d, []) + [senti_neg]
    #  print(u'{} {} {}'.format(tw['created_at'].isoformat(), senti_pos, senti_neg) # blob_sent, blob_subj, tw['text']))
    #posx = []
    #posy = []
    #negx = []
    #negy = []
    #for i in sorted(poscnt.items(), lambda x, y: int((x[0]-y[0]).total_seconds())):
    #  posx.append(i[0])
    #  posy.append(numpy.mean(i[1]))
    #for i in sorted(negcnt.items(), lambda x, y: int((x[0]-y[0]).total_seconds())):
    #  negx.append(i[0])
    #  negy.append(numpy.mean(i[1]))
    #fig, ax = plt.subplots(figsize=(18,7))
    #plt.plot_date(posx, posy, '-')
    #plt.fill_between(posx, 0, posy, facecolor='blue')
    #plt.plot_date(negx, negy, '-')
    #plt.fill_between(negx, 0, negy, facecolor='red')
    #plt.show()
