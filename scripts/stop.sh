#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

CRAWLERDIR=$HOME/work/TwitterAnalytics/
PYTHONPATH=$PYTHONPATH:$CRAWLERDIR
CRAWLERBIN=$CRAWLERDIR/bin
DATADIR=$CRAWLERDIR/data

rm $DATADIR/runcrawler

found=false
for f in `ls $DATADIR/*pid`; do
  echo -n "Found $f: "
  if kill -0 `cat $f`; then
    echo "Running"
    found=true
  else
    echo "Dead. Cleanup."
    rm $f
  fi
done

if $found; then
  echo "Wait for 15 minutes for crawler to finish crawl cycle."
  sleep 15m
  echo "Kill'em all!"
  for f in `ls $DATADIR/*pid`; do
    echo "Killing $f"
    kill -15 `cat $f`
    rm $f
  done
else
  echo "Nothing running."
fi

