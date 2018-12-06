#!/bin/bash
#
# This script makes all empty directories for a functional twAwler
# installation.

mkdir $CRAWLERDIR/data
for i in {0..9}; do mkdir $CRAWLERDIR/images/$i; done
for i in {a..z}; do mkdir $CRAWLERDIR/images/$i; done
