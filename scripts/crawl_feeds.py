import datetime
import json
import logging
import os
from os.path import join
from twarc import Twarc


def crawl_feed(feed_dict, credentials):
    twarc = Twarc(credentials['consumer_key'], credentials['consumer_secret'], credentials['access_token'], credentials['access_token_secret'])
    crawl_time = datetime.datetime.now()
    crawl_time_filename = crawl_time.strftime('%Y%m%d%I%M%S')
    crawl_time_html = crawl_time.strftime('%B %d, %Y')
    crawl_name = feed_dict['crawl_name']
    crawl_type = feed_dict['crawl_type']
    short_name = feed_dict['short_name']
    search_string = feed_dict['search_string']

    feed_dir = feed_dict['feed_dir']
    json_dir = join(feed_dir, 'json')
    html_dir = join(feed_dir, 'html')
    media_dir = join(feed_dir, 'media')
    logs_dir = join(feed_dir, 'logs')

    for directory in [feed_dir, json_dir, html_dir, media_dir, logs_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    log_file = join(logs_dir, 'twarc.log')

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    logger = logging.getLogger(crawl_name)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    base_filename = short_name + '-' + crawl_time_filename
    json_file = join(json_dir, base_filename + '.json')

    print("Searching Twitter API for {0}".format(search_string))
    print("Writing JSON and HTML files...")

    logger.info("starting search for %s", search_string)
    tweet_count = 0

    if crawl_type == "timeline":
        for tweet in twarc.timeline(screen_name=search_string):
            with open(json_file, 'a') as json_out:
                json_out.write("{}\n".format(json.dumps(tweet)))

            if "id_str" in tweet:
                logger.info("archived https://twitter.com/%s/status/%s", tweet['user']['screen_name'], tweet["id_str"])
            elif 'limit' in tweet:
                logger.warn("%s tweets undelivered", tweet["limit"]["track"])
            elif 'warning' in tweet:
                logger.warn(tweet['warning']['message'])
            else:
                logger.warn(json.dumps(tweet))

            tweet_count += 1

    else:
        for tweet in twarc.search(search_string):
            with open(json_file, 'a') as json_out:
                json_out.write("{}\n".format(json.dumps(tweet)))

            if "id_str" in tweet:
                logger.info("archived https://twitter.com/%s/status/%s", tweet['user']['screen_name'], tweet["id_str"])
            elif 'limit' in tweet:
                logger.warn("%s tweets undelivered", tweet["limit"]["track"])
            elif 'warning' in tweet:
                logger.warn(tweet['warning']['message'])
            else:
                logger.warn(json.dumps(tweet))

            tweet_count += 1

    if tweet_count == 0:
        logger.info("no new tweets matching %s", search_string)

        # Write an empty json file. Maybe don't do this?
        with open(json_file, 'w') as json_out:
            json_out.close()

    return base_filename, tweet_count, crawl_time_html


def crawl_feeds(feeds, credentials):
    crawled_feeds = {}
    for feed in feeds:
        print("Checking crawl status for {0}".format(feed))
        feed_dict = feeds[feed]
        crawl_status = feed_dict['crawl_status']
        print("Crawl status for {0} is {1}".format(feed, crawl_status))
        if crawl_status.lower() == 'true':
            print("Crawling {0}".format(feed))
            new_capture, tweet_count, crawl_time_html = crawl_feed(feed_dict, credentials)
            feed_dict['new_capture'] = new_capture
            feed_dict['tweet_count'] = tweet_count
            feed_dict['crawl_time_html'] = crawl_time_html
            crawled_feeds[feed] = feed_dict
    return crawled_feeds
