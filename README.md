
# rss2maildir

## What does it do?

It downloads newsfeeds and stores them in a local maildir,
so that you can read them with your mail client.

## How to install?

Assuming rss2maildir.py is in your PATH and you use the default config location
install the script by adding

0    *    *    *    *    rss2maildir.py > /dev/null

into you crontab.

## Dependencies

The python3 modules that are required are:

feedparser
mailbox

All other modules should be part of the standard library.
This script is python 3 only.

## Configuration

rss2maildir takes a configuration file that is located at ~/.config/rss2maildir.json.
For situations where your config is located else where use the '-c' parameter.

### The configuration file

An annotated config lookes like this:

    {
        # General options
        "general": {
            # The "base" directory for all feeds
            "maildir": "~/.mail/rss",
            # Where to store information between script runs
            "cache": "~/.cache/rss2maildir/",
            # Use mails as a cache instead of local files
            "use_maildir_cache": true,
            # Should all mails be stored in a single Maildir
            "use_single_maildir": true,
            # Under what name should the script send mails
            "mail_sender": "rss2emaildir"
        },
        # list of subscriptions
        "feeds": [
            {
                # used to identify feeds, Maildir name under "base" directory
                "name": "rss2maildir",
                "url": "https://github.com/edt-devel/rss2maildir/commits/master.atom"
            },
            {
                "name": "HackerNews",
                "url": "https://news.ycombinator.com/rss"
                # store this feed explicitly in this Maildir
                "maildir": "~/.mail/rss/news"
            }
        ]
    }

### Options

All general settings and the feeds:maildir setting overwrite the internal default values.
If you like the defaults, simply omit these parameters.

#### general:maildir
The "base" folder under which all feed Maildirs will be created. If you have 'use\_single\_maildir' set to true this directory will function ass the Maildir.

**default:** ~/.mail/rss

#### general:cache

**default:** ~/.cache/rss2maildir/

#### general:use\_maildir\_cache

If set to true all cache files will be stored as mails in a Maildir. general:cache will then be interpreted as that Maildir, or (~/.mail/rss/rss2maildircache if not set).

**default:** false

#### general:use\_single\_maildir

Drop all mails into a single Maildir (defined via general:maildir), unless a feed defines its own Maildir.

**default:** false

#### general:sender

Content of the "From" field

**default:** rss2maildir

#### general:recipient

Content of the "To" field

**default:** ${USER}@localhost

#### feeds:name

Identifying name of your feed. It will also be used to create a Maildir with equal name under general:maildir

#### feeds:url
URL of the feed that shall be downloaded.

#### feeds:maildir
Specific Maildir for this feed. Overwrites all other Maildir settings.

## License

This script is released under the GPLv3.
