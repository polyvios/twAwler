#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-urls-politicians.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-urls-politicians.pid
  exit
fi

echo "Politician URLs "
date
cat $CRAWLERDIR/greekdata/politicians.txt | xargs -n 1 $CRAWLERBIN/deshorten.py -t -u
echo "done"
echo

sleep 24h

. $CRAWLERDIR/scripts/crawl-urls-politicians.sh
