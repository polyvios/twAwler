#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-lists3.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-lists3.pid
  exit
fi

date
$CRAWLERBIN/addlists.py --id --all --subscriptions
sleep 1h

. $CRAWLERDIR/scripts/crawl-lists3.sh

