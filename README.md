# twAwler
A lightweight twitter crawler

This crawler can use a single machine and discover a language-based
community.  This criterion is programmable, so it should be able to
discover and track any community recognized by a programmable filter.

For guidelines on how to extend it with new non-language based filters
contact the author.

The crawler uses the Twitter API exclusively and does not scrape
information.  As such, all datasets generated comply with the Twitter
ToS.

Dynamic compliance may take some manual curation: if for example an
installation needs to purge deleted tweets or users every so often,
this is currently not automated, but there are tools to help.

## Social Network Analytics for Twitter

This repository includes tools for twitter crawling and analytics
* Directory twkit/ includes python modules for crawling, analytics, and data curation
* Directory scripts/ includes bash scripts for setting up the crawler

For a list of all the features extracted from the graph, see the
ongoing report draft at <https://arxiv.org/abs/1804.07748>.

### Installation

First, install MongoDB. The current installation assumes an
unprotected Mongo (I know, will fix), so make sure it's not exposed
anywhere it shouldn't be.  Edit env.sh if you need to set it to
anywhere else than localhost.

```
sudo apt-get install mongodb
```

Then install all packages listed in
[doc/dependencies.txt](doc/dependencies.txt), using pip, apt, yum,

rpm, source packages, or any other way you prefer.

```
pip install sklearn
```
etc.

To set up a twAwler installation, clone the repository, set up
`$CRALWERDIR` shell environment variable, and add the root dir of the
project to your `$PYTHONPATH`.  You can do that once in file
[env.sh](env.sh) and then source the file whenever you use the
crawler.

Then, create a `config.py` file with the oauth keys for a twitter application.
To get twitter keys, you have to apply for a developer account at
<https://developer.twitter.com>, and create a new application at
<https://apps.twitter.com>.

To add a user to be tracked, use

```
bin/adduser.py <twitteruser>
```

or

```
bin/adduser.py --id <twitterid>
```

to crawl a user's tweets, use

```
bin/dumpall.py <twitteruser>
```


To seed the network with users to be followed, use `stream.py`.

After adding a few users, run

```
scripts/start-all.sh
```

The script will start several tmux sessions and crawl all selected
users, discovering and adding new users speaking the same language, as
configured in `config.py`.
It will load all available tweets using the API, use retweets to
discover more users, and follow them, exploring Greek-speakers in a
forest-fire way.

Intermediate files used for crawling (such as user frequency of
tweeting) will appear in the data/ directory.

