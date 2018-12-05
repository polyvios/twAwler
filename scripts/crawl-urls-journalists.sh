#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-urls-journalists.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-urls-journalists.pid
  exit
fi

echo "Journalist URLs "
date
cat $CRAWLERDIR/greekdata/journalists.txt | xargs -n 1 $CRAWLERBIN/deshorten.py -t -u
echo "done"
echo

sleep 24h

. $CRAWLERDIR/scripts/crawl-urls-journalists.sh
