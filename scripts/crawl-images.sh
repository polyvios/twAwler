#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-images.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-images.pid
  exit
fi

date
$CRAWLERBIN/profilepics.py -v
cd images/
#rm *.db
find . -empty -exec /bin/rm \{\} \;
./reindex-relink-dir.sh */
sleep 24h

. $CRAWLERDIR/scripts/crawl-images.sh
