import argparse
import os
from os.path import join

from scripts.build_html import build_html
from scripts.build_index import build_index
from scripts.config import parse_config
from scripts.copy_readme import copy_readme
from scripts.crawl_feeds import crawl_feeds
from scripts.credentials import load_credentials
from scripts.extract_urls import extract_urls
from scripts.fetch_media import fetch_media

# A lot of code heavily adapted from https://github.com/edsu/twarc

root_dir = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('-f','--feed', default='all', help='Specify which feed to crawl')
parser.add_argument('-e','--exclude',nargs="*",help='Specify which feeds to exclude from a crawl')
parser.add_argument('-t','--test',action="store_true",help="Run the script using test config")
args = parser.parse_args()

if args.test:
	feeds_dir = join(root_dir, 'test_crawls')
	config_file = join(root_dir, 'feeds_test.txt')
else:
	feeds_dir = join(root_dir, 'feeds')
	config_file = join(root_dir, 'feeds.txt')

if not os.path.exists(feeds_dir):
	os.makedirs(feeds_dir)

readme_file = join(root_dir, 'lib','README.txt')
credentials_file = join(root_dir, '.twarc')

credentials = load_credentials(credentials_file)

feeds = parse_config(config_file, feeds_dir, args)
crawled_feeds = crawl_feeds(feeds, credentials)
copy_readme(crawled_feeds, readme_file)
extract_urls(crawled_feeds)
build_html(crawled_feeds)
build_index(crawled_feeds)
fetch_media(crawled_feeds)


