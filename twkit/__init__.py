#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################
# (c) 2016-2020 Polyvios Pratikakis
# polyvios@ics.forth.gr
###########################################

"""A library for crawling twitter and analyzing crawled tweets and relations.

By Polyvios Pratikakis <polyvios@ics.forth.gr>.

For support, use the github repository contact methods
(https://www.github.com/polyvios/twAwler).

Currently extracts 6 kinds of relations:
  * follow: unweighted, directed graph
  * favorite: weighted, directed graph
  * reply: weighted, directed graph
  * retweet: weighted, directed graph
  * quote: weighted, directed graph
  * listsim: weighted, undirected graph
  * avatar: undirected graph

Currently extracts around 2000 features per user.
"""

__author__       = 'Polyvios Pratikakis'
__email__        = 'polyvios@ics.forth.gr'
__copyright__    = '''
Copyright (c) 2016-present Polyvios Pratikakis, FORTH. All rights reserved.'''
__license__      = 'Apache License 2.0'
__version__      = '0.0.3'
__url__          = 'https://github.com/polyvios/twAwler'
__description__  = 'A Twitter API crawler and feature extraction library'

from twkit.utils import init_state, verbose
