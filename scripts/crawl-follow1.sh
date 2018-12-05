#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-follow1.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-follow1.pid
  exit
fi

date
$CRAWLERBIN/addfollowers.py --id --all
sleep 15m

. $CRAWLERDIR/scripts/crawl-follow1.sh

