import configparser
import os
import sys


def load_config(config_file):
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        return config
    else:
        print("Config file {0} not found".format(config_file))
        sys.exit()


def parse_config(config_file, feeds_dir, args):
    config = load_config(config_file)

    if args.feed == 'all':
        feeds = config.sections()
    else:
        feeds = [args.feed]

    if args.exclude:
        for feed in args.exclude:
            feeds.remove(feed)

    feeds_dict = {}
    for feed in feeds:
        crawl_status = config.get(feed, 'crawl')
        crawl_name = config.get(feed, 'name')
        crawl_type = config.get(feed, 'crawl_type')
        search_string = config.get(feed, 'search_string')
        feed_dir = os.path.join(feeds_dir, feed)
        feeds_dict[feed] = {'feed_dir': feed_dir,
                            'crawl_status': crawl_status,
                            'crawl_name': crawl_name,
                            'crawl_type': crawl_type,
                            'search_string': search_string,
                            'short_name': feed}

    return feeds_dict
