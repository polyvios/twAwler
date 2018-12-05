#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-faved.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-faved.pid
  exit
fi

date
$CRAWLERBIN/pullreplied.py -v --favorites
echo done
echo
sleep 2h

. $CRAWLERDIR/scripts/crawl-faved.sh

