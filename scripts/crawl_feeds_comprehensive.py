from twarc import Twarc
import argparse
from bs4 import BeautifulSoup
import ConfigParser
import csv
import datetime
import json
import logging
import os
from os.path import join
import re
import requests
import time

# HTML output code heavily heavily adopted from https://github.com/edsu/twarc/blob/master/utils/wall.py

def crawl_feed(feed_dict, credentials_dict):
	twarc = Twarc(credentials_dict['consumer_key'], credentials_dict['consumer_secret'], credentials_dict['access_token'], credentials_dict['access_token_secret'])
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

	log_file = join(logs_dir,'twarc.log')

	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	logger = logging.getLogger(crawl_name)
	handler = logging.FileHandler(log_file)
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.INFO)

	base_filename = short_name + '-' + crawl_time_filename
	json_file = join(json_dir, base_filename + '.json')

	print "Searching Twitter API for {0}".format(search_string)
	print "Writing JSON and HTML files..."

	logger.info("starting search for %s", search_string)
	tweet_count = 0

	for tweet in twarc.search(search_string):
		with open(json_file,'a') as json_out:
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

def deduplicate_tweets(feed_dict):
	feed_dir = feed_dict['feed_dir']
	json_dir = join(feed_dir, 'json')

	base_filename = feed_dict['new_capture']
	json_filename = base_filename + '.json'
	original_file = join(json_dir, json_filename)
	deduplicated_file = join(json_dir, json_filename.replace('.json','-dedupe.json'))

	unique_ids = {}
	duplicates = 0

	# First, check for duplicates...
	for line in open(original_file):
		tweet = json.loads(line)
		tweet_id = tweet['id']
		if tweet_id not in unique_ids:
			unique_ids[tweet_id] = True
		else:
			duplicates += 1

	if duplicates > 0:
		print "Found {0} duplicates and {1} unique ids in {2}. Deduping.".format(duplicates, len(unique_ids), original_file)
		written_ids = {}
		for line in open(original_file):
			tweet = json.loads(line)
			tweet_id = tweet['id']
			if tweet_id not in written_ids:
				written_ids[tweet_id] = True
				with open(deduplicated_file,'a') as json_out:
					json_out.write("{}\n".format(json.dumps(tweet)))
		print "Removing {0}".format(original_file)
		os.remove(original_file)
		print "Renaming {0} to {1}".format(deduplicated_file, original_file)
		os.rename(deduplicated_file, original_file)
	else:
		print "No duplicates found in {0}".format(json_filename)

def build_html(feed_dict):
	feed_dir = feed_dict['feed_dir']
	json_dir = join(feed_dir, 'json')
	html_dir = join(feed_dir, 'html')
	base_filename = feed_dict['new_capture']
	json_file = join(json_dir, base_filename + '.json')
	html_file = join(html_dir, base_filename + '.html')

	search_string = feed_dict['search_string']

	crawl_type = feed_dict['crawl_type']
	if crawl_type == 'hashtag':
		html_title = search_string + ' Tweets'
	elif crawl_type == 'mentions':
		html_title = search_string + ' Twitter Mentions'

	crawl_time_html = feed_dict['crawl_time_html']

	media_dir = join(feed_dir,'media')
	media_urls_csv = join(media_dir, 'tweet_images.csv')
	profile_image_csv = join(media_dir, 'profile_images.csv')

	media_urls = {}
	profile_images = {}

	if os.path.exists(media_urls_csv):
		with open(media_urls_csv,'rb') as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				url = row[0]
				media_filename = row[1]
				media_urls[url] = media_filename

	if os.path.exists(profile_image_csv):
		with open(profile_image_csv,'rb') as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				url = row[0]
				profile_dir = row[1]
				profile_filename = row[2]
				profile_images[url] = {'profile_dir':profile_dir, 'filename':profile_filename}

	html_header = """
	<!doctype html>
	<html>

	<head>
	  <meta charset="utf-8">
	  <title>Archive of {0}</title>
	  <style>
	    body {{
	      font-family: Arial, Helvetica, sans-serif;
	      font-size: 12pt;
	      margin-left: auto;
	      margin-right: auto;
	      width: 95%;
	    }}

	    article.tweet {{
	      /*position: relative;
	      float: left;*/
	      border: thin #eeeeee solid;
	      margin: 10px;
	      width: 300px;
	      padding: 10px;
	      display: inline-block;
	      vertical-align:top;
	      /*height: 170px;*/
	    }}

	    .name {{
	      font-weight: bold;
	    }}

	    img.avatar {{
	        vertical-align: middle;
	        float: left;
	        margin-right: 10px;
	        border-radius: 5px;
	        height: 45px;
	    }}

	    time {{
	    	font-size: small;
	    }}

	    .tweet footer {{
	      position: relative;
	      bottom: 5px;
	      left: 10px;
	      font-size: smaller;
	    }}

	    .tweet a {{
	      text-decoration: none;
	    }}

	    footer#page {{
	      margin-top: 15px;
	      clear: both;
	      width: 100%;
	      text-align: center;
	      font-size: 20pt;
	      font-weight: heavy;
	    }}

	    header {{
	      text-align: center;
	      margin-bottom: 20px;
	    }}

	    .media {{
	        max-width: 300px;
	        border: none;
	    }}

	  </style>
	</head>

	<body>

	  <header>
	  <h1>Archive of {0}</h1>
	  <p>Collected on {1}</p>
	  </header>
	  <p><em>created on the command line with <a href="http://github.com/edsu/twarc">twarc</a></em></p>

	  <div id="tweets">
	  """.format(html_title, crawl_time_html)

  	with open(html_file, 'a') as html_out:
  		print "Writing html header information to {0}".format(html_file)
  		html_out.write(html_header)

	for line in open(json_file):
		tweet = json.loads(line)

		if 'media' in tweet['entities']:
			original_url = tweet["entities"]["media"][0]["media_url"]
			media_filename = media_urls[original_url]
			media_path = '../media/tweet_images/' + media_filename
			media = '<a href="' + media_path +'"><img class="media" src=\"' + tweet["entities"]["media"][0]["media_url"] +'"></a>'
		else:
			media = ''

		profile_image_url = tweet["user"]["profile_image_url"]
		profile_dir = profile_images[profile_image_url]['profile_dir']
		profile_image_file = profile_images[profile_image_url]['filename']
		profile_image_path = '../media/profile_images/' + profile_dir + '/' + profile_image_file

		t = {
			"created_at": tweet["created_at"],
			"name": tweet["user"]["name"],
			"username": tweet["user"]["screen_name"],
			"user_url": "http://twitter.com/" + tweet["user"]["screen_name"],
			"text": tweet["text"],
			"avatar": profile_image_path,
			"url": "http://twitter.com/" + tweet["user"]["screen_name"] + "/status/" + tweet["id_str"],
			"media":media,
		}

		if 'retweet_status' in tweet:
			t['retweet_count'] = tweet['retweet_status'].get('retweet_count', 0)
		else:
			t['retweet_count'] = tweet.get('retweet_count', 0)

		for url in tweet['entities']['urls']:
			a = '<a href="%(expanded_url)s">%(url)s</a>' % url
			start, end = url['indices']
			t['text'] = t['text'][0:start] + a + tweet['text'][end:]

			t['text'] = re.sub(' @([^ ]+)', ' <a href="http://twitter.com/\g<1>">@\g<1></a>', t['text'])
			t['text'] = re.sub(' #([^ ]+)', ' <a href="https://twitter.com/search?q=%23\g<1>&src=hash">#\g<1></a>', t['text'])

		tweet_html = """
			<article class="tweet">
			<img class="avatar" src="%(avatar)s">
			<a href="%(user_url)s" class="name">%(name)s</a><br>
			<span class="username">%(username)s</span><br>
			<br>
			<span class="text">%(text)s</span><br>
			<span class="media">%(media)s</span><br>
			<footer>
			%(retweet_count)s Retweets<br>
			<a href="%(url)s"><time>%(created_at)s</time></a>
			</footer>
			</article>
			""" % t

		with open(html_file,'a') as html_out:
			html_out.write(tweet_html.encode('utf-8'))

	tweet_count = feed_dict['tweet_count']
	if tweet_count == 0:
		no_new_tweets = '<p align="center">No tweets matching {0} were captured on {1}</p>'.format(search_string, crawl_time_html)
		with open(html_file,'a') as html_out:
			html_out.write(no_new_tweets.encode('utf-8'))

	html_footer = """
		</div>

		<footer id="page">
		<hr>
		<br>
		created on the command line with <a href="http://github.com/edsu/twarc">twarc</a>.
		<br>
		<br>
		</footer>

		</body>
		</html>
		"""

	with open(html_file,'a') as html_out:
		html_out.write(html_footer)


def extract_urls(feed_dict):
	feed_dir = feed_dict['feed_dir']
	base_filename = feed_dict['new_capture']

	json_dir = join(feed_dir, 'json')
	html_dir = join(feed_dir, 'html')
	media_dir = join(feed_dir, 'media')
	media_urls_csv = join(media_dir, 'tweet_images.csv')
	profile_image_csv = join(media_dir,'profile_images.csv')

	media_urls = []
	new_media_urls = {}

	profile_image_urls = []
	new_profile_image_urls = {}


	if os.path.exists(media_urls_csv):
		with open(media_urls_csv,'rb') as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				media_url = row[0]
				if media_url not in media_urls:
					media_urls.append(media_url)

	if os.path.exists(profile_image_csv):
		with open(profile_image_csv,'rb') as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				profile_image_url = row[0]
				if profile_image_url not in profile_image_urls:
					media_urls.append(profile_image_url)


	json_file = join(json_dir, base_filename + '.json')

	for line in open(json_file):
		status = json.loads(line)
		if 'media' in status['entities']:
			media_url = status['entities']['media'][0]['media_url']
			if (media_url not in media_urls) and (media_url not in new_media_urls):
				new_media_filename = os.path.split(media_url)[-1]
				new_media_urls[media_url] = new_media_filename

		profile_image_url = status['user']['profile_image_url']
		if (profile_image_url not in profile_image_urls) and (profile_image_url not in new_profile_image_urls):
			profile_image_directory = profile_image_url.split('/')[-2]
			profile_image_filename = os.path.split(profile_image_url)[-1]
			new_profile_image_urls[profile_image_url] = {'profile_dir':profile_image_directory,'filename':profile_image_filename}

	with open(media_urls_csv,'ab') as csvfile:
		writer = csv.writer(csvfile)
		for media_url in new_media_urls:
			writer.writerow([media_url, new_media_urls[media_url]])

	with open(profile_image_csv, 'ab') as csvfile:
		writer = csv.writer(csvfile)
		for profile_image_url in new_profile_image_urls:
			profile_image_directory = new_profile_image_urls[profile_image_url]['profile_dir']
			profile_image_filename = new_profile_image_urls[profile_image_url]['filename']
			writer.writerow([profile_image_url, profile_image_directory, profile_image_filename])

def fetch_media(feed_dict):
	feed_dir = feed_dict['feed_dir']
	media_dir = join(feed_dir, 'media')
	short_name = feed_dict['short_name']

	image_dir = join(media_dir,'tweet_images')
	profile_images_dir = join(media_dir,'profile_images')

	if not os.path.exists(image_dir):
		os.makedirs(image_dir)
	if not os.path.exists(profile_images_dir):
		os.makedirs(profile_images_dir)

	media_urls_csv = join(media_dir,'tweet_images.csv')
	profile_image_csv = join(media_dir,'profile_images.csv')

	media_urls = {}
	profile_image_urls = {}

	with open(media_urls_csv,'rb') as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			url = row[0]
			filename = row[1]
			media_urls[url] = filename

	with open(profile_image_csv,'rb') as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			url = row[0]
			profile_dir = row[1]
			filename = row[2]
			profile_image_urls[url] = {'profile_dir':profile_dir,'filename':filename}

	with requests.Session() as s:
		for url in media_urls:
			if media_urls[url] not in os.listdir(image_dir):
				print "{0} Media URLs: Fetching {1}".format(short_name, url)
				media = s.get(url)
				media_file = join(image_dir, media_urls[url])
				with open(media_file, 'wb') as media_out:
					media_out.write(media.content)
				time.sleep(1)
			else:
				print "{0} Media URLs: {1} has already been fetched".format(short_name, url)

	with requests.Session() as s:
		for url in profile_image_urls:
			profile_dir_name = profile_image_urls[url]['profile_dir']
			filename = profile_image_urls[url]['filename']
			profile_dir = join(profile_images_dir, profile_dir_name)
			if not os.path.exists(profile_dir):
				os.makedirs(profile_dir)
			if filename not in os.listdir(profile_dir):
				print "{0} Profile Images: Fetching {1}".format(short_name, url)
				profile_image = s.get(url)
				profile_image_file = join(profile_dir, filename)
				with open(profile_image_file,'wb') as profile_image_out:
					profile_image_out.write(profile_image.content)
				time.sleep(1)
			else:
				print "{0} Profile Images: {1} has already been fetched".format(short_name, url)

def replace_media_urls(feed_dict):
	feed_dir = feed_dict['feed_dir']

	html_dir = join(feed_dir, 'html')

	base_filename = feed_dict['new_capture']

	html_filename = base_filename + '.html'

	html_file = join(html_dir,html_filename)

	media_dir = join(feed_dir, 'media')
	media_urls_csv = join(media_dir, 'tweet_images.csv')
	profile_image_csv = join(media_dir, 'profile_images.csv')

	media_urls = {}
	profile_images = {}

	if os.path.exists(media_urls_csv):
		with open(media_urls_csv,'rb') as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				url = row[0]
				media_filename = row[1]
				media_urls[url] = media_filename

	if os.path.exists(profile_image_csv):
		with open(profile_image_csv,'rb') as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				url = row[0]
				profile_dir = row[1]
				profile_image_filename = row[2]
				profile_images[url] = {'profile_dir':profile_dir, 'filename':profile_image_filename}

	print "Replacing urls in {0}".format(html_filename)
	soup = BeautifulSoup(open(html_file),'html.parser')

	medias = soup.find_all('span',{'class':'media'})
	avatars = soup.find_all('img',{'class':'avatar'})

	for media in medias:
		if media.a:
			original_url = media.a['href']
			if original_url in media_urls:
				media_filename = media_urls[original_url]
				new_path = '../media/tweet_images/' + media_filename
				media.a['href'] = new_path
				media.a.img['src'] = new_path

	for avatar in avatars:
		original_url = avatar['src']
		if original_url in profile_images:
			profile_dir = profile_images[original_url]['profile_dir']
			profile_image_file = profile_images[original_url]['filename']
			new_path = '../media/profile_images/' + profile_dir + '/' + profile_image_file
			avatar['src'] = new_path


	html_out = soup.prettify('utf-8')
	with open(html_file,'wb') as html_out_file:
		html_out_file.write(html_out)

def make_master_download_csv(feed_dict):
	feed_dir = feed_dict['feed_dir']
	short_name = feed_dict['short_name']

	media_dir = join(feed_dir, 'media')

	tweet_images_csv = join(media_dir, 'tweet_images.csv')
	profile_images_csv = join(media_dir, 'profile_images.csv')
	master_csv = join(media_dir, 'image_urls_and_download_locations.csv')

	# These have already been written to the master csv
	old_and_new_urls_existing = {}
	# These are new and have not been written
	old_and_new_urls_new = {}

	if os.path.exists(master_csv):
		with open(master_csv, 'rb') as csvfile:
			reader = csv.reader(csvfile)
			next(reader,None)
			for row in reader:
				original_url = row[0]
				new_path = row[1]
				old_and_new_urls_existing[original_url] = new_path
	else:
		with open(master_csv, 'ab') as csvfile:
			writer = csv.writer(csvfile)
			writer.writerow(['Original URL','Download Location'])

	with open(tweet_images_csv, 'rb') as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			original_url = row[0]
			new_filename = row[1]
			new_path = short_name + '/media/tweet_images/' + new_filename
			if original_url not in old_and_new_urls_existing:
				old_and_new_urls_new[original_url] = new_path

	with open(profile_images_csv, 'rb') as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			original_url = row[0]
			profile_dir = row[1]
			new_filename = row[2]
			new_path = short_name + '/media/profile_images/' + profile_dir + '/' + new_filename
			if original_url	not in old_and_new_urls_existing:
				old_and_new_urls_new[original_url] = new_path

	with open(master_csv, 'ab') as csvfile:
		writer = csv.writer(csvfile)
		# Only write the new urls to the master csv
		for original_url in old_and_new_urls_new:
			new_path = old_and_new_urls_new[original_url]
			writer.writerow([original_url, new_path])

def build_index(feed_dict):
	feed_dir = feed_dict['feed_dir']

	crawl_name = feed_dict['crawl_name']
	crawl_type = feed_dict['crawl_type']
	short_name = feed_dict['short_name']

	print "Building HTML index for {0}".format(short_name)

	header_types = {'mentions':'Twitter Mentions','hashtag':'Tweets','user':'Tweets'}
	header_text = crawl_name + ' ' + header_types[crawl_type]

	index = join(feed_dir, 'index.html')

	index_html = """ 
		<html>
		<head>
		<meta charset='utf-8'>
		<title>{0} Twitter Archive</title>
		<style type='text/css'>
		body {{
			font-family: Arial, Helvetica, sans-serif;
			font-size: 12px;
		}}
		h1, h2 {{
			text-align: center;
		}}
		table {{
			border: 0;
			border-collapse:collapse;
			margin: auto;
			border-spacing: 0;
		}}
		td, th {{
			margin: 0px;
			border: 1px solid #333;
			border-collapse:collapse;
			padding-top: 3px;
			padding-right: 8px;
			padding-bottom: 3px;
			padding-left: 8px;
		}}
		</style>
		</head>

		<body>
		<h1>Bentley Historical Library</h1>
		<h2>Archive of {1}</h2>
		<table>
		<thead>
			<tr>
				<th>Capture Date</th>
				<th>Tweet Wall</th>
				<th>Raw JSON Data</th>
			</tr>
		</thead>
		<tbody>
		""".format(crawl_name, header_text)

	with open(index, 'w') as index_out:
		index_out.write(index_html)

	html_dir = join(feed_dir, 'html')
	json_dir = join(feed_dir, 'json')

	for filename in os.listdir(html_dir):
		json_filename = filename.replace('html','json')
		json_filepath = join(json_dir, json_filename)
		if os.path.exists(json_filepath):
			json_data_row = "<td><a href=\"json/{0}\">{0}</a></td>".format(json_filename)
		else:
			json_data_row = "<td>No Tweets Captured</td>"
		crawl_date_string = filename.split('-')[1].replace('.html','')
		crawl_date_object = datetime.datetime.strptime(crawl_date_string, "%Y%m%d%H%M%S")
		crawl_date = datetime.datetime.strftime(crawl_date_object, "%B %d, %Y")
		table_row = """
			<tr>
			<td>{0}</td>
			<td><a href="html/{1}">{1}</a></td>
			{2}
			</tr>
			""".format(crawl_date, filename, json_data_row)
		with open(index, 'a') as index_out:
			index_out.write(table_row)

	html_end = """
		</tbody>
		</table>
		</body>
		</html>
		"""

	with open(index,'a') as index_out:
		index_out.write(html_end)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-f','--feed', default='all', help='Specify which feed to crawl')
	parser.add_argument('-e','--exclude',nargs="*",help='Specify which feeds to exclude from a crawl')
	parser.add_argument('-t','--test',action="store_true",help="Run the script using test config")
	args = parser.parse_args()

	root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	if args.test:
		feeds_dir = join(root_dir, 'test_crawls')
		config_file = join(root_dir, 'feeds_test.txt')
	else:
		feeds_dir = join(root_dir, 'feeds')
		config_file = join(root_dir,'feeds.txt')

	README_file = join(root_dir, 'README.txt')
	README_text = open(README_file).read()


	credentials_file = join(root_dir,'.twarc')
	credentials = ConfigParser.ConfigParser()
	credentials.read(credentials_file)

	credentials_dict = {}
	credentials_dict['consumer_key'] = credentials.get('main','consumer_key')
	credentials_dict['consumer_secret'] = credentials.get('main','consumer_secret')
	credentials_dict['access_token'] = credentials.get('main','access_token')
	credentials_dict['access_token_secret'] = credentials.get('main','access_token_secret')

	config = ConfigParser.ConfigParser()
	config.read(config_file)

	if args.feed == 'all':
		feeds = config.sections()
	else:
		feeds = [args.feed]

	if args.exclude:
		for feed in args.exclude:
			feeds.remove(feed)

	feeds_dict = {}

	crawled = []

	for feed in feeds:
		crawl_status = config.get(feed, 'crawl')
		crawl_name = config.get(feed,'name')
		crawl_type = config.get(feed,'crawl_type')
		search_string = config.get(feed,'search_string')
		feed_dir = join(feeds_dir, feed)
		feeds_dict[feed] = {'feed_dir':feed_dir,'crawl_status':crawl_status,'crawl_name':crawl_name,'crawl_type':crawl_type,'search_string':search_string,'short_name':feed}

	for feed in feeds_dict:
		print "Checking crawl status for {0}".format(feed)
		feed_dict = feeds_dict[feed]
		crawl_status = feed_dict['crawl_status']
		print "Crawl status for {0} is {1}".format(feed, crawl_status)
		if crawl_status == 'True':
			print "Crawling {0}".format(feed)
			new_capture, tweet_count, crawl_time_html = crawl_feed(feed_dict, credentials_dict)
			feed_dict['new_capture'] = new_capture
			feed_dict['tweet_count'] = tweet_count
			feed_dict['crawl_time_html'] = crawl_time_html
			feeds_dict[feed] = feed_dict
			crawled.append(feed)

			feed_dir = feed_dict['feed_dir']
			feed_README = join(feed_dir,'README.txt')
			if not os.path.exists(feed_README):
				with open(feed_README,'w') as README:
					README.write(README_text)


	for feed in crawled:
		feed_dict = feeds_dict[feed]
		#print "Deduplicating tweets for {0}".format(feed)
		#deduplicate_tweets(feed_dict)
		print "Extracting tweet and profile image urls for {0}".format(feed)
		extract_urls(feed_dict)
		print "Building HTML for {0}".format(feed)
		build_html(feed_dict)
		#print "Replacing media urls for {0}".format(feed)
		#replace_media_urls(feed_dict)
		print "Making master download csv for {0}".format(feed)
		make_master_download_csv(feed_dict)
		print "Building index.html for {0}".format(feed)
		build_index(feed_dict)

	for feed in crawled:
		feed_dict = feeds_dict[feed]
		print "Fetching media for {0}".format(feed)
		fetch_media(feed_dict)

if __name__ == "__main__":
	main()