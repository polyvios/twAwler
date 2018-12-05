#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

TIMEFORMAT="real %3lR    user %3lU    sys %3lS"

cd $CRAWLERDIR

echo $$ > $DATADIR/crawl-tweets.pid

if [ -f $DATADIR/runcrawler ]; then
  true;
else
  echo "Crawler finished"
  rm $DATADIR/crawl-tweets.pid
  exit
fi

echo ""
echo "============== Cycle Begin =============="

date -Iseconds
temp=`mktemp`
if [ -f $DATADIR/runstats ]; then
  echo "Running Statistics on this cycle"
  dorunstats=1
  rm -f $DATADIR/runstats
else
  dorunstats=0
fi


echo ""
echo "================ Phase 1 ================"
echo ""
(
  echo ""
  echo `date -Iseconds`": Compute frequencies"
  time $CRAWLERBIN/freq.py > $DATADIR/frequences.tmp
  sort -nk 9 $DATADIR/frequences.tmp > $DATADIR/frequences
) > $temp 2>&1 &
$CRAWLERBIN/load-past.py --all --crawl-req=2
$CRAWLERBIN/dumpall.py --crawl-late=2000
wait
cat $temp
rm $temp
newcomers=`grep -a Missing $DATADIR/frequences | wc -l`
echo ""
echo "New users left: $newcomers"
$CRAWLERBIN/limits.py --wait
echo ""
echo `date -Iseconds`": Get new tweets"
$CRAWLERBIN/dumpall.py --crawl-expected=500
echo ""
echo `date -Iseconds`": Refresh too old"
$CRAWLERBIN/dumpall.py --crawl-late=350
if [ $dorunstats = 1 ]; then
  (
    echo ""
    echo `date -Iseconds`": Count ignored"
    time $CRAWLERBIN/count-ignored.py | sort -n > $DATADIR/ign.tmp
    mv $DATADIR/ign.tmp $DATADIR/ign
  ) > $temp 2>&1 &
  $CRAWLERBIN/dumpall.py --crawl-late=1350
  wait
  cat $temp
  rm $temp
fi

echo ""
echo "================ Phase 2 ================"
echo `date -Iseconds`": Load newcomers"
grep -a Missing $DATADIR/frequences | cut -f 3 -d \  | sort | head -n 200 | xargs $CRAWLERBIN/load-past.py --crawl-req=2
echo ""
$CRAWLERBIN/limits.py --wait
echo `date -Iseconds`": Get new tweets"
$CRAWLERBIN/dumpall.py --crawl-expected=500
echo ""
echo `date -Iseconds`": Refresh too old"
$CRAWLERBIN/dumpall.py --crawl-late=350
if [ $dorunstats = 1 ]; then
  (
    echo ""
    echo `date -Iseconds`": Compute greek-tweets"
    time $CRAWLERBIN/count-gr-tweets.py --tracked -f > $DATADIR/greek-cnt.tmp
    LC_ALL=C sort -gk 5 $DATADIR/greek-cnt.tmp > $DATADIR/greek-cnt
    cat $DATADIR/greek-cnt | awk '$5 >= 0.2 && $4 >= 100' | cut -f 1 -d\  | xargs $CRAWLERBIN/setgreek.py --id
    cat $DATADIR/greek-cnt | awk '$5 <= 0.01 && $4 >= 500' | cut -f 1 -d\  | xargs $CRAWLERBIN/stop.py --id
    cat $DATADIR/greek-cnt | awk '$5 <= 0.02 && $4 >= 1500' | cut -f 1 -d\  | xargs $CRAWLERBIN/stop.py --id
    cat $DATADIR/greek-cnt | awk '$5 <= 0.03 && $4 >= 3000' | cut -f 1 -d\  | xargs $CRAWLERBIN/stop.py --id
    cat $DATADIR/greek-cnt | awk '$5 == 0.00 && $4 >= 200' | cut -f 1 -d\  | xargs $CRAWLERBIN/stop.py --id
    grep -a -i -f greekdata/regex-greeks $DATADIR/greek-cnt | awk '$5 >= 0.1 && $4 >= 500' | cut -f 1 -d\ | xargs $CRAWLERBIN/setgreek.py --id
    time $CRAWLERBIN/count-gr-tweets.py > $DATADIR/greek-cnt.tmp
    LC_ALL=C sort -gk 5 $DATADIR/greek-cnt.tmp > $DATADIR/greek-cnt
  ) > $temp 2>&1 &
  $CRAWLERBIN/dumpall.py --crawl-expected=6000
  wait
  cat $temp
  rm $temp
fi


echo ""
echo "================ Phase 3 ================"
$CRAWLERBIN/limits.py --wait
echo ""
echo `date -Iseconds`": Get new tweets"
$CRAWLERBIN/dumpall.py --crawl-expected=500
echo ""
echo `date -Iseconds`": Refresh too old"
$CRAWLERBIN/dumpall.py --crawl-late=350
echo ""
if [ $dorunstats = 1 ]; then
  (
    echo `date -Iseconds`": Compute seen"
    time $CRAWLERBIN/find-seen.py -o $DATADIR/seen.tmp -v | sort -nk 3 > $DATADIR/unseen
    sort -n $DATADIR/seen.tmp > $DATADIR/seen
  ) > $temp 2>&1 &
  $CRAWLERBIN/dumpall.py --crawl-late=6000
  wait
  cat $temp
  rm $temp
  echo ""
fi


echo "================ Phase 4 ================"
$CRAWLERBIN/limits.py --wait
echo ""
echo `date -Iseconds`": Get new tweets"
$CRAWLERBIN/dumpall.py --crawl-expected=500
echo ""
echo `date -Iseconds`": Load newcomers"
grep -a Missing $DATADIR/frequences | cut -f 3 -d \  | sort | head -n 200 | xargs $CRAWLERBIN/dumpall.py --crawl-req=3
echo ""
echo `date -Iseconds`": Get missing users"
for i in `grep -a "()" $DATADIR/seen | tail -20 | cut -c 8-29`; do
  echo -e "g/\<$i\>/d\nw" | ed -s $DATADIR/seen &
  $CRAWLERBIN/addid.py $i
  wait
done
echo `date -Iseconds`": Add one to track"
for i in `grep -a -v "()" data/seen | tail -1 | cut -c 8-29`; do
  bin/adduser.py --id $i && echo -e "g/\<$i\>/d\nw" | ed -s data/seen;
  bin/dumpall.py --id $i;
done
echo ""
echo `date -Iseconds`": Refresh too old"
$CRAWLERBIN/dumpall.py --crawl-late=350
#if [ $dorunstats = 1 ]; then
#  echo ""
#  echo `date -Iseconds`": Count tweets"
#  time $CRAWLERBIN/count-tweets.py | sort -nr > $DATADIR/cnt.tmp
#  mv $DATADIR/cnt.tmp $DATADIR/cnt
#fi
echo ""
echo `date -Iseconds`": Database:"
time $CRAWLERBIN/count-dumped.py

echo ""
echo "=============== Cycle End ==============="

. $CRAWLERDIR/scripts/crawl-tweets.sh
