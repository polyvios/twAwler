#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-friend1.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-friend1.pid
  exit
fi

date
$CRAWLERBIN/addfriends.py --id --all
sleep 15m

. $CRAWLERDIR/scripts/crawl-friend1.sh

