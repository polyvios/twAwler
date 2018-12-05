#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-replies.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-replies.pid
  exit
fi

date
$CRAWLERBIN/pullreplied.py -v
echo done
echo
sleep 2h

. $CRAWLERDIR/scripts/crawl-replies.sh

