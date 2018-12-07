#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2018 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""
A library for crawling twitter and analyzing crawled tweets and
relations.  

Currently extracts 6 kinds of relations:
  * follow: unweighted, directed graph
  * favorite: weighted, directed graph
  * reply: weighted, directed graph
  * retweet: weighted, directed graph
  * quote: weighted, directed graph
  * listsim: weighted, undirected graph

Currently extracts around 2000 features per user.
"""

__author__       = 'Polyvios Pratikakis'
__email__        = 'polyviosr@ics.forth.gr'
__copyright__    = 'Copyright (c) 2016-present Polyvios Pratikakis, FORTH-ICS'
__license__      = 'Apache License 2.0'
__version__      = '0.0.1'
__url__          = 'https://github.com/polyvios/twAwler'
__description__  = 'A Twitter API crawler and feature extraction library'

from utils import init_state, verbose
