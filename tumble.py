#!/usr/bin/env python

"""Read a feed and post its entries to tumblr.com"""

import sys, urllib, urllib2, netrc
import feedparser

from datetime import datetime
from calendar import timegm

HOST = 'www.tumblr.com'
BLOG = None		# or set it to a sub-blog of your account

DEBUG = False

def tumble(feed):
    auth = netrc.netrc().authenticators(HOST)
    if auth is not None:
        auth = {'email': auth[0], 'password': auth[2]}
        feed = feedparser.parse(feed)
        return [post(auth, e) for e in feed.entries]

def post(auth, entry):
    enc = entry.get('enclosures', [])
    if enc: enc = enc[0]
    if enc and enc.type.startswith('image/'):
        data = {
            'type': 'photo', 'source': enc.href,
            'caption': entry.title, 'click-through-url': entry.link
        }
    elif enc and enc.type.startswith('audio/'):
        data = {
            'type': 'audio', 'caption': entry.title, 'externally-hosted-url': enc.href
        }
    elif enc and enc.type.startswith('video/'):
        data = {
            'type': 'video', 'caption': entry.title, 'embed': enc.href
        }
    elif 'link' in entry:
        data = {'type': 'link', 'url': entry.link, 'name': entry.title}
        if 'content' in entry:
            data['description'] = entry.content[0].value
        elif 'summary' in entry:
            data['description'] = entry.summary
    elif 'content' in entry:
        data = {'type': 'regular', 'title': entry.title, 'body': entry.content[0].value}
    elif 'summary' in entry:
        data = {'type': 'regular', 'title': entry.title, 'body': entry.summary}
    else:
        return 'unknown', entry
    if 'tags' in entry:
        data['tags'] = ','.join('"%s"' % t.term for t in entry.tags)
    for d in ('published_parsed', 'updated_parsed'):
        if d in entry:
            pub = datetime.fromtimestamp(timegm(entry.get(d)))
            data['date'] = pub.isoformat(' ')
            break
    if BLOG:
        data['group'] = BLOG

    if DEBUG:
        return 'debug', entry.id, data

    data.update(auth)
    for k in data:
        if type(data[k]) is unicode:
            data[k] = data[k].encode('utf-8')

    try:
        return 'ok', urllib2.urlopen('http://' + HOST + '/api/write', urllib.urlencode(data)).read()
    except Exception, e:
        return 'error', e

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '-d':
        DEBUG = True
    result = tumble(sys.stdin)
    if result:
        import pprint
        pprint.pprint(result)
