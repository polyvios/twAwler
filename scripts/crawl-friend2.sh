#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-friend2.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-friend2.pid
  exit
fi

date
$CRAWLERBIN/addfriends.py --full --all
sleep 15m

. $CRAWLERDIR/scripts/crawl-friend2.sh

