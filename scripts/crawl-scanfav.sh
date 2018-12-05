#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-scanfav.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-scanfav.pid
  exit
fi

date
$CRAWLERBIN/scanfavs.py -v --all
sleep 1h

. $CRAWLERDIR/scripts/crawl-scanfav.sh

