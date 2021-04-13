# ungi-bots

Bots, scrapers and whatever to collect data goes here.

#### Prerequisites
A working Elastic search install

A linux host
 

### Bots/CLI setup

1. clone this repo:

`git clone https://gitea.gretagangbang.biz:nsaspy/ungi-bots.git`

2. install requirments

` cd ungi-bots && pip install --user -r requirements.txt`

3. run ungi.py and type "init"

this will configure the backend, make the required indexes, etc.





### Discord Logger setup
To get the Discord loggers you will need tokens, you can obtain
them in a cookie or via tampermonkey. 

Just Search on the web 
"How to obtain discord token". 

Once you have the token you will place it in a file

**NOTE**: You can Have as many bots as you need, just input more tokens


Once you have the tokens: 

`export UNGI_CONFIG="path to config ini"`

`bash start.sh <token file>`


### Reddit Setup

To setup the reddit scraper you will need a api token from Reddit. 

You can search the web for how to obtain them.

Place the Credientails in the config file

to start:

`export UNGI_CONFIG="path to config`

for full scrape of the subbreddits

`python reddit.py -f`

**NOTE**: if you want it to have it perodically watch a subreddit you will have to make a cron tab

Heres some help on that:

https://stackoverflow.com/questions/19972713/run-cron-job-every-5-min
