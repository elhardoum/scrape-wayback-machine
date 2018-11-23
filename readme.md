# Scrape Wayback Machine

This quick tool, originally created for a client, allows you to scrape the wayback machine (web.archive.org) for URLs and search suggested-hosts. 

It comes with proxy support and also allows you to perform scrapes in multiple threads, for quick results.

## Install

Requires Python 3, and the [`requests`](https://github.com/requests/requests) module.

```bash
pip install requests
```

## Usage

```bash
$ python3 fetch.py -h 
usage: fetch.py [-h] -u  [-ua] [-m] [-s] [-p] [-pf] [-l] [-xh]

optional arguments:
  -h, --help            show this help message and exit

required arguments:
  -u , --urls           URLs to fetch (file path)

optional arguments:
  -ua , --user-agents   User agents to use (file path)
  -m , --max-workers    Max workers to use for threading
  -s , --save-to        Distination file path
  -p , --proxy          Proxy address
  -pf , --proxies-file 
                        Use a list of proxies (file path)
  -l , --log-errors     Log errors to a file
  -xh , --exclude-hosts 
                        Exclude hosts (query-suggested domains)
```

Example use:

```bash
$ python3 fetch.py -u URLS.txt -s list.txt -m 4 -xh true
Saved to /Users/Ismail/dev/.python/scrape-wayback-machine/list.txt
```

**Generate a user-agents.txt file:**

```bash
$ virtualenv -p python3 generate-ua-file
$ cd $_
$ source bin/activate
$ pip install fake_useragent
$ python
Python 3.6.5 (default, Mar 30 2018, 06:42:10) 
[GCC 4.2.1 Compatible Apple LLVM 9.0.0 (clang-900.0.39.2)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from fake_useragent import UserAgent
>>> ua = UserAgent()
>>> max_ua = 100 # max user-agents to save
>>> with open('./user-agents.txt', 'a') as f:
...     while max_ua:
...         max_ua -= 1
...         f.write( ua.chrome + '\n' )
...
>>> exit()
$ deactivate
$ printf "Generated file: $(realpath ./user-agents.txt)\n"
```