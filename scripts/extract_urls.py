import csv
import json
import os
from os.path import join


def extract_urls_for_feed(feed_dict):
    feed_dir = feed_dict['feed_dir']
    short_name = feed_dict['short_name']
    base_filename = feed_dict['new_capture']

    json_dir = join(feed_dir, 'json')
    html_dir = join(feed_dir, 'html')
    media_dir = join(feed_dir, 'media')
    media_urls_csv = join(media_dir, 'tweet_images.csv')
    profile_image_csv = join(media_dir, 'profile_images.csv')
    master_csv = join(media_dir, 'image_urls_and_download_locations.csv')

    media_urls = []
    new_media_urls = {}

    profile_image_urls = []
    new_profile_image_urls = {}

    master_csv_urls = []
    new_master_csv_urls = {}

    if os.path.exists(media_urls_csv):
        with open(media_urls_csv, 'r', newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                media_url = row[0]
                if media_url not in media_urls:
                    media_urls.append(media_url)

    if os.path.exists(profile_image_csv):
        with open(profile_image_csv, 'r', newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                profile_image_url = row[0]
                if profile_image_url not in profile_image_urls:
                    media_urls.append(profile_image_url)

    if os.path.exists(master_csv):
        with open(master_csv, 'r', newline="") as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)
            for row in reader:
                original_url = row[0]
                master_csv_urls.append(original_url)
    else:
        with open(master_csv, 'w', newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Original URL', 'Download Location'])

    json_file = join(json_dir, base_filename + '.json')

    for line in open(json_file):
        status = json.loads(line)
        if 'media' in status['entities']:
            media_url = status['entities']['media'][0]['media_url']
            media_filename = os.path.split(media_url)[-1]
            if (media_url not in media_urls) and (media_url not in new_media_urls):
                new_media_urls[media_url] = media_filename
            if media_url not in master_csv_urls:
                new_media_path = short_name + '/media/tweet_images/' + media_filename
                new_master_csv_urls[media_url] = new_media_path

        profile_image_url = status['user']['profile_image_url']
        profile_image_directory = profile_image_url.split('/')[-2]
        profile_image_filename = os.path.split(profile_image_url)[-1]
        if (profile_image_url not in profile_image_urls) and (profile_image_url not in new_profile_image_urls):			
            new_profile_image_urls[profile_image_url] = {'profile_dir': profile_image_directory, 'filename': profile_image_filename}
        if profile_image_url not in master_csv_urls:
            new_profile_path = short_name + '/media/profile_images/' + profile_image_directory + '/' + profile_image_filename
            new_master_csv_urls[profile_image_url] = new_profile_path

    new_media_data = []
    for media_url in new_media_urls:
        new_media_data.append([media_url, new_media_urls[media_url]])
    with open(media_urls_csv, 'a', newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(new_media_data)

    new_profile_data = []
    for profile_image_url in new_profile_image_urls:
        profile_image_directory = new_profile_image_urls[profile_image_url]['profile_dir']
        profile_image_filename = new_profile_image_urls[profile_image_url]['filename']
        new_profile_data.append([profile_image_url, profile_image_directory, profile_image_filename])
    with open(profile_image_csv, 'a', newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(new_profile_data)

    new_master_data = []
    for url in new_master_csv_urls:
        new_master_data.append([url, new_master_csv_urls[url]])
    with open(master_csv, 'a', newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(new_master_data)


def extract_urls(feeds):
    for feed in feeds:
        print("Extracting tweet and profile image urls for {0}".format(feed))
        feed_dict = feeds[feed]
        extract_urls_for_feed(feed_dict)