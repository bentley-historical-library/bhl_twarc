import csv
import os
from os.path import join
import requests
import time

def fetch_media_for_feed(feed_dict):
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

def fetch_media(feeds):
	for feed in feeds:
		print "Fetching media for {0}".format(feed)
		feed_dict = feeds[feed]
		fetch_media_for_feed(feed_dict)