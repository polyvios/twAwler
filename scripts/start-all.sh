#!/bin/bash
###########################################
# (c) 2016-2018 FORTH-ICS
# Author: Polyvios Pratikakis
# Email: polyvios@ics.forth.gr
###########################################

export CRAWLERDIR=$HOME/work/TwitterAnalytics/
export PYTHONPATH=$PYTHONPATH:$CRAWLERDIR
export CRAWLERBIN=$CRAWLERDIR/bin
export DATADIR=$CRAWLERDIR/data

touch $DATADIR/runcrawler

for f in `ls $DATADIR/*pid`; do
  echo -n "Found $f "
  if kill -0 `cat $f` > /dev/null 2>&1; then
    echo "Alive"
    found=true
  else
    echo "Dead. Cleanup."
    rm $f
  fi
done


echo -n "Tweets: "
if [ -f $DATADIR/crawl-tweets.pid ]; then
  echo "Already Running"
else
  nohup $CRAWLERDIR/scripts/crawl-tweets.sh >> $DATADIR/nohup.out 2>&1 &
  tmux new-session -d -s tweets-favs "tail -f $DATADIR/nohup.out"
  echo "OK"
fi

echo -n "API Favorites: "
if [ -f $DATADIR/crawl-favs.pid ]; then
  echo "Already Running"
else
  tmux split-window -h -t tweets-favs $CRAWLERDIR/scripts/crawl-favs.sh
  echo "OK"
fi

tmux select-layout -t tweets-favs even-horizontal 

echo -n "Followers1: "
if [ -f $DATADIR/crawl-follow1.pid ]; then
  echo "Already Running"
else
  tmux new-session -d -s follow $CRAWLERDIR/scripts/crawl-follow1.sh
  echo "OK"
fi

echo -n "Followers2: "
if [ -f $DATADIR/crawl-follow2.pid ]; then
  echo "Already Running"
else
  tmux split-window -t follow -h $CRAWLERDIR/scripts/crawl-follow2.sh
  echo "OK"
fi

echo -n "Friends1: "
if [ -f $DATADIR/crawl-friend1.pid ]; then
  echo "Already Running"
else
  tmux split-window -t follow -h $CRAWLERDIR/scripts/crawl-friend1.sh
  echo "OK"
fi

echo -n "Friends2: "
if [ -f $DATADIR/crawl-friend2.pid ]; then
  echo "Already Running"
else
  tmux split-window -t follow -h $CRAWLERDIR/scripts/crawl-friend2.sh
  echo "OK"
fi

tmux select-layout -t follow even-horizontal 


echo -n "Replies: "
if [ -f $DATADIR/crawl-replies.pid ]; then
  echo "Already Running"
else
  tmux new-session -d -s reply-quote $CRAWLERDIR/scripts/crawl-replies.sh
  echo "OK"
fi

echo -n "Quotes: "
if [ -f $DATADIR/crawl-quotes.pid ]; then
  echo "Already Running"
else
  tmux split-window -t reply-quote -h $CRAWLERDIR/scripts/crawl-quotes.sh
  echo "OK"
fi

echo -n "Favorited: "
if [ -f $DATADIR/crawl-faved.pid ]; then
  echo "Already Running"
else
  tmux split-window -t reply-quote -h $CRAWLERDIR/scripts/crawl-faved.sh
  echo "OK"
fi

tmux select-layout -t reply-quote even-vertical

echo -n "Trends: "
if [ -f $DATADIR/crawl-trends.pid ]; then
  echo "Already Running"
else
  tmux split-window -t reply-quote -h $CRAWLERDIR/scripts/crawl-trends.sh
  echo "OK"
fi

tmux select-layout -t reply-quote tiled


echo -n "URLs: "
if [ -f $DATADIR/crawl-urls.pid ]; then
  echo "Already Running"
else
  tmux new-session -d -s urls $CRAWLERDIR/scripts/crawl-urls.sh
  echo "OK"
fi

echo -n "News URLs: "
if [ -f $DATADIR/crawl-urls-newsmedia.pid ]; then
  echo "Already Running"
else
  tmux split-window -t urls $CRAWLERDIR/scripts/crawl-urls-newsmedia.sh
  echo "OK"
fi

tmux select-layout -t urls even-horizontal

echo -n "Journalist URLs: "
if [ -f $DATADIR/crawl-urls-journalists.pid ]; then
  echo "Already Running"
else
  tmux new-window -t urls $CRAWLERDIR/scripts/crawl-urls-journalists.sh
  echo "OK"
fi

echo -n "Politician URLs: "
if [ -f $DATADIR/crawl-urls-politicians.pid ]; then
  echo "Already Running"
else
  tmux split-window -t urls $CRAWLERDIR/scripts/crawl-urls-politicians.sh
  echo "OK"
fi

tmux select-layout -t urls even-horizontal


echo -n "Lists: "
if [ -f $DATADIR/crawl-lists1.pid ]; then
  echo "Already Running"
else
  tmux new-session -d -s lists $CRAWLERDIR/scripts/crawl-lists1.sh
  echo "OK"
fi

echo -n "Memberships: "
if [ -f $DATADIR/crawl-lists2.pid ]; then
  echo "Already Running"
else
  tmux split-window -t lists -h $CRAWLERDIR/scripts/crawl-lists2.sh
  echo "OK"
fi

echo -n "Subscriptions: "
if [ -f $DATADIR/crawl-lists3.pid ]; then
  echo "Already Running"
else
  tmux split-window -t lists -h $CRAWLERDIR/scripts/crawl-lists3.sh
  echo "OK"
fi

tmux select-layout -t lists even-horizontal 


echo -n "Images: "
if [ -f $DATADIR/crawl-images.pid ]; then
  echo "Already Running"
else
  tmux new-session -d -s images $CRAWLERDIR/scripts/crawl-images.sh
  echo "OK"
fi


