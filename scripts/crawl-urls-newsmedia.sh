#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-urls-newsmedia.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-urls-newsmedia.pid
  exit
fi

echo "News URLs "
date
cat $CRAWLERDIR/greekdata/newsmedia.txt | xargs -n 1 $CRAWLERBIN/deshorten.py -t -u
echo "done"
echo

sleep 4h

. $CRAWLERDIR/scripts/crawl-urls-newsmedia.sh
