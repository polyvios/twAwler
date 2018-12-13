# twAwler

## A lightweight twitter crawler

twAwler is a twitter crawler that can run on a single machine and
fully discover a medium-sized language-based community.  This
criterion is programmable, so it should be able to discover and track
any community recognized by a programmable filter.

The crawler uses the Twitter API exclusively and does not scrape
information.  As such, all datasets generated comply with the Twitter
ToS.

Dynamic compliance may take some manual curation: if for example an
installation needs to purge deleted tweets or users every so often,
this is currently not automated, but there are tools to help.

For guidelines on how to extend it with new non-language based filters
contact the author.


### Documentation

This repository includes tools for twitter crawling and analytics
* Directory twkit/ includes python modules for crawling, analytics, and data curation
* Directory scripts/ includes bash scripts for setting up the crawler

For a list of all the features extracted from the graph, see the
ongoing report draft at <https://arxiv.org/abs/1804.07748> or [doc/crawler](doc/crawler).


### Installation

First, install and start MongoDB. The current installation assumes an
unprotected Mongo (I know, planning to fix soon), so make sure it's
not exposed anywhere it shouldn't be.  Edit env.sh if you need to set
it to anywhere else than localhost.  For example, on Ubuntu you can use:

```bash
sudo apt install mongodb
```

Then install all packages listed in
[doc/dependencies.txt](doc/dependencies.txt), using pip, apt, yum,
rpm, source packages, or any other way you prefer.  For example:
```bash
pip install sklearn
```
etc.

To set up a twAwler installation, clone the repository
```bash
git clone git@github.com:polyvios/twAwler.git
```

Then set up the `$CRALWERDIR` shell environment variable, and add the
root dir of the project to your `$PYTHONPATH`.  You can do that once
in file [env.sh](env.sh)
```bash
vim env.sh
```

and then source the file whenever you use the crawler
```bash
. env.sh
```

Then, run the installation script that creates empty directories for
crawler data and avatar images.
```bash
scripts/install.sh
```

You also need to populate the submodule repositories, and install
`greekdict`, a POS tagger and stemmer for Greek.
```bash
git submodule init
git submodule update
cd greekdict
```

To train the greek POS tagger, you need a recent XML dump of the
<https://el.wiktionary.org> dictionary.  Follow the installation instructions
for <https://github.com/polyvios/el-wiktionary-parser> to get the data and
train it, and place the resulting `word_graph.json` file in the
`data/` directory created by the installation script.

Then, create a `config.py` file with the oauth keys for a twitter application.
To get twitter keys, you have to apply for a developer account at
<https://developer.twitter.com>, and create a new application at
<https://apps.twitter.com>.


### Starting the crawler

To add a user to be tracked, use
```bash
bin/adduser.py <twitteruser>
```

or
```bash
bin/adduser.py --id <twitterid>
```

to get a specific user's tweets, after you have added that user, use
```bash
bin/dumpall.py <twitteruser>
```

To seed the network with users to be followed, you can also use `stream.py`.

After adding a few users, run
```bash
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

### Stopping the crawler

To stop the crawler, you can use `scripts/stop.py`. The script will
signal all crawler processes to stop (using lock files) and then wait
15 more minutes.  You can also just kill the crawler processes, as
there is no risk of creating a corrupt state.  To kill any of the
crawler processes, check their PIDs stored into corresponding files in
the `data/` directory.  If one or more of the crawler processes die
for any reason, you can re-run `scripts/start-all.sh` to re-start all
missing crawler processes.

### Querying the data

To extract crawled graphs, use the modules in the `twkit/curation`
directory. They are all runnable as standalone command-line tools.

For the follow graph:
```
twkit/curation/exportfollow.py
```

