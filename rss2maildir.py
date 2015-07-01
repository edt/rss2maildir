#!/usr/bin/env python3
"""This script downloads rss feeds and stores them in a maildir"""

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
import json
import getpass


class defaults:
    """Contains global default values"""
    maildir = os.path.expanduser("~/.mail/rss/")
    config = os.path.expanduser("~/.cache/rss2maildir.json")
    cache = os.path.expanduser("~/.cache/rss2mail/")
    maildir_cache = os.path.expanduser("~/.mail/rss/rss2maildircache")
    use_single_maildir = False
    use_maildir_cache = False
    mail_sender = "rss2mail"
    mail_recipient = getpass.getuser() + "@localhost"


class rss_feed:
    """"""
    def __init__(self):
        self.name = ""
        self.url = ""
        self.maildir = ""
        self.feed = None
        self.cache = None


def load_config():
    """Load configuration from JSON"""
    json_data = open(defaults.config).read()
    config = json.loads(json_data)

    if config["general"]["use_single_maildir"]:
        defaults.use_single_maildir = config["general"]["use_single_maildir"]
        if not isinstance(defaults.use_single_maildir, bool):
            print ("use_single_maildir has to be true or false")
            exit(1)

    if config["general"]["use_maildir_cache"]:
        defaults.use_maildir_cache = config["general"]["use_maildir_cache"]
        if not isinstance(defaults.use_maildir_cache, bool):
            print ("use_maildir_cache has to be true or false")
            exit(1)

    if config["general"]["mail_sender"]:
        defaults.mail_sender = config["general"]["mail_sender"]
        if not isinstance(defaults.mail_sender, str):
            print ("mail_sender has to be a string")
            exit(1)

    if config["general"]["cache"]:
        defaults.cache = config["general"]["cache"]
        if not isinstance(defaults.cache, str):
            print ("cache has to be a string")
            exit(1)

    feed_list = []

    for single_feed in config["feeds"]:
        feed = rss_feed()
        feed.name = single_feed["name"]
        feed.url = single_feed["url"]
        feed.maildir = defaults.maildir + "/" + feed.name

        if not feed.name:
            exit(1)
        if not feed.url:
            exit(2)
        feed_list.append(feed)

    return feed_list


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
        msg = mailbox.MaildirMessage()
        # msg.set_charset('utf-8')
        if 'published' in rss:
            msg.set_unixfrom('{0} Date: {1}'.format(origin, rss.published))
            msg.__setitem__('Date', rss.published)
        elif 'updated' in rss:
            # atom feeds use '2015-05-31T19:57:15+02:00'
            # python requires timezone offset to be without :
            time_string = rss.updated
            k = rss.updated.rfind(":")
            time_string = time_string[:k] + time_string[k+1:]

            entry_time = time.strptime(time_string, '%Y-%m-%dT%H:%M:%S%z')
            msg.__setitem__('Date',
                            time.strftime("%a, %d %b %Y %H:%M:%S %z",
                                          entry_time))
        else:
            print ("no date available")
        print (rss)

        msg['From'] = origin
        msg['To'] = defaults.mail_recipient
        msg['Subject'] = rss.title

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
    """Save object to given file"""
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


def read_mail_cache(rss_list):
    """"""
    print ("Reading mail cache")
    mbox = mailbox.Maildir(defaults.cache)
    mbox.lock()
    try:
        for message in mbox:
            byte_pickle = message.get_payload()
            for rss in rss_list:
                if rss.name is message['title']:
                    rss.cache = pickle.load(byte_pickle)

    finally:
        mbox.unlock()


def write_mail_cache(rss_list):
    """
    [yas] elisp error! Symbol's value as variable is void: text
   """
    print ("Writing mail cache")
    mbox = mailbox.Maildir(defaults.cache)
    mbox.lock()
    try:
        for f in rss_list:
            msg = mailbox.MaildirMessage()

            msg.__setitem__('Date',
                            time.strftime("%a, %d %b %Y %H:%M:%S %z",
                                          time.gmtime()))

            msg['From'] = defaults.mail_sender
            msg['To'] = defaults.mail_recipient
            msg['Subject'] = f.feed.feed.title

            byte_pickle = pickle.dump(f.feed)

            msg.set_payload(byte_pickle)

            mbox.add(msg)
            mbox.flush()

    finally:
        mbox.unlock()


def extract_new_items(new_list, old_list):
    """Extract new feed entries
    new_list - list from which new entries shall be extracted
    old_list - list whith which new_list is compared

    returns array of entries found in new_list and not in old_list
    """
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

    maildir = ""
    if defaults.use_single_maildir:
        maildir = defaults.maildir
    else:
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
""".format(sys.argv[0],
           defaults.config,
           defaults.cache))


def main(argv):
    """Entry point"""

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

    if defaults.use_maildir_cache:
        defaults.cache = defaults.maildir_cache
        read_mail_cache(feeds)
    else:
        load_cache(feeds)

    for single_feed in feeds:
        download_feed(single_feed)

    if defaults.use_maildir_cache:
        write_mail_cache(feeds)
    else:
        write_cache(feeds)

if __name__ == "__main__":
    main(sys.argv[1:])
