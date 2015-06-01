#!/usr/bin/env python3

# Copyright(C) 2015 Edgar Thier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import mailbox
import feedparser
import sys
import getopt
import pickle
import time


class defaults:
    """Contains global default values"""
    maildir = os.path.expanduser("~/.mail/rss/")
    config = os.path.expanduser("~/work/projects/rss2mail/rss2mail.json")
    # cache = os.path.expanduser("~/.cache/rss2mail")
    cache = os.path.expanduser("~/work/projects/rss2mail/rss2mail.cache")
    mail_sender = "rss2mail"
    mail_recipient = "edt@localhost"


class rss_feed:
    """"""
    def __init__(self):
        self.name = ""
        self.url = ""
        self.maildir = ""
        self.feed = None
        self.cache = None


def load_config():
    """"""
    # json_data = open(defaults.config).read()
    # config = json.loads(json_data)

    x = rss_feed()
    x.name = "xkcd"
    x.url = "https://xkcd.com/rss.xml"
    # x.url = "/home/edt/work/projects/rss2mail/rss.xml"
    x.maildir = "~/.mail/rss/xkcd"

    h = rss_feed()
    h.name = "heise"
    h.url = "http://www.heise.de/newsticker/heise-atom.xml"
    # h.url = "/home/edt/work/projects/rss2mail/heise-atom.xml"
    h.maildir = "~/.mail/rss/heise"

    g = rss_feed()
    g.name = "golem"
    g.url = "http://rss.golem.de/rss.php?feed=RSS2.0"

    return [x, h, g]


def update_maildir(maildir, rss, origin):
    """
    Creates or updates the given maildir and fills it with the messages
    maildir - Maildir that shall be used
    rss - feedparser entry that shall be converted
    """
    print ("Opening {0}".format(maildir))
    mbox = mailbox.Maildir(maildir)
    mbox.lock()
    try:
        # set message time to publish time
        # feedparser has the format u'Thu, 05 Sep 2002 00:00:01 GMT'
        # "%a, %d %b %Y %H:%M:%S +0000"
        seconds = float(time.mktime(time.strptime(rss.published,
                                                  '%a, %d %b %Y %H:%M:%S %Z')))
        msg = mailbox.MaildirMessage()
        # msg.set_charset('utf-8')
        msg.set_unixfrom('{0} {1}'.format(origin, rss.published))
        msg['From'] = origin
        msg['To'] = defaults.mail_recipient
        # msg['To'] = "bla"
        msg['Subject'] = rss.title

        print ("seconds: {0} - date {1}".format(seconds, rss.published))
        msg.set_date(seconds)

        message = (rss.link
                   + "\n"
                   + rss.description)

        msg.set_payload(message.encode('utf-8'))

        mbox.add(msg)
        mbox.flush()

    finally:
        mbox.unlock()


def load_cache(rss_list):
    """Load cache file and fill rss feeds with their values"""

    for rss in rss_list:
        filename = os.path.expanduser(defaults.cache) + "/" + rss.name

        if os.path.isfile(filename):
            with open(filename, 'rb') as input_file:
                rss.cache = pickle.load(input_file)


def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def write_cache(rss_list):
    """
    rss_list - list of rss_feed objects that should be cached
    """
    if not os.path.exists(defaults.cache):
        os.makedirs(defaults.cache)

    for rss in rss_list:
        filename = os.path.expanduser(defaults.cache) + "/" + rss.name
        save_object(rss.feed, filename)


def extract_new_items(new_list, old_list):
    """"""
    has_guid = False

    new_entries = []
    for item in new_list:
        if has_guid:
            # todo
            continue
        else:
            is_new = True
            for j in old_list:
                if item.link == j.link:
                    is_new = False
            if is_new:
                new_entries.append(item)
    return new_entries


def download_feed(feed):
    """
    feed - rss_feed object
    """
    print ("=== Checking feed '{0}'".format(feed.name))

    if feed.url is None:
        print ("No viable url found! Aborting feed...")
        return False

    print ("Downloading '{0}'...".format(feed.url))
    feed.feed = feedparser.parse(feed.url)

    if feed.cache is not None:
        # diff the two lists and only use new entries
        new_entries = extract_new_items(feed.feed.entries, feed.cache.entries)

        for item in new_entries:
            print ("NEW ENTRY {0}".format(item.title))
    else:
        # it is a new feed
        new_entries = feed.feed.entries

    maildir = defaults.maildir + feed.name
    if new_entries:
        for item in new_entries:
            update_maildir(maildir, item, feed.feed['feed']['title'])

    else:
        print ("No new messages.")


def print_help():
    """Prints help text and arguments"""
    print ("""{0}

Download rss feeds and convert them to maildir entries.
Options:
\t-h print help text
\t-c define config to use [default: {1}]
\t-t define cache directory to use [default: {2}]
""").format(sys.argv[0],
            defaults.config,
            defaults.cache)


def main(argv):
    """"""

    try:
        opts, args = getopt.getopt(argv,
                                   "hc:t:",
                                   ["help", "config=", "cache="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt in ("-c", "--config"):
            defaults.config = arg
        elif opt in ("-t", "--cache"):
            defaults.cache = arg

    feeds = load_config()
    load_cache(feeds)

    for single_feed in feeds:
        download_feed(single_feed)

    write_cache(feeds)

if __name__ == "__main__":
    main(sys.argv[1:])
