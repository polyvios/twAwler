#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-urls.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-urls.pid
  exit
fi

echo "All URLs "
date
$CRAWLERBIN/deshorten.py -t 
sleep 10

. $CRAWLERDIR/scripts/crawl-urls.sh
