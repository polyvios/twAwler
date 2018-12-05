#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-favs.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-favs.pid
  exit
fi

if $CRAWLERBIN/dumpfavs.py --all; then
  echo "Please reset, no change!"
fi
sleep 10

. $CRAWLERDIR/scripts/crawl-favs.sh
