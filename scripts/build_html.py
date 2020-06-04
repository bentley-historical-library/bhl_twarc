import csv
import json
import os
from os.path import join
import re

# Heavily adapted from https://github.com/edsu/twarc/blob/master/utils/wall.py


def build_html_for_feed(feed_dict):
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
    elif crawl_type == "timeline":
        html_title = search_string + ' Timeline'

    crawl_time_html = feed_dict['crawl_time_html']

    media_dir = join(feed_dir, 'media')
    media_urls_csv = join(media_dir, 'tweet_images.csv')
    profile_image_csv = join(media_dir, 'profile_images.csv')

    media_urls = {}
    profile_images = {}

    if os.path.exists(media_urls_csv):
        with open(media_urls_csv, 'r', newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                url = row[0]
                media_filename = row[1]
                media_urls[url] = media_filename

    if os.path.exists(profile_image_csv):
        with open(profile_image_csv, 'r', newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                url = row[0]
                profile_dir = row[1]
                profile_filename = row[2]
                profile_images[url] = {'profile_dir': profile_dir, 'filename': profile_filename}

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
      <p><em>created with <a href="http://github.com/edsu/twarc">twarc</a></em></p>

      <div id="tweets">
      """.format(html_title, crawl_time_html)

    with open(html_file, 'a') as html_out:
        print("Writing html header information to {0}".format(html_file))
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
            "text": tweet["full_text"],
            "avatar": profile_image_path,
            "url": "http://twitter.com/" + tweet["user"]["screen_name"] + "/status/" + tweet["id_str"],
            "media": media,
        }

        if 'retweet_status' in tweet:
            t['retweet_count'] = tweet['retweet_status'].get('retweet_count', 0)
        else:
            t['retweet_count'] = tweet.get('retweet_count', 0)

        for url in tweet['entities']['urls']:
            a = '<a href="%(expanded_url)s">%(url)s</a>' % url
            start, end = url['indices']
            t['text'] = t['text'][0:start] + a + t['text'][end:]

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

        with open(html_file, 'a', encoding="utf-8") as html_out:
            html_out.write(tweet_html)

    tweet_count = feed_dict['tweet_count']
    if tweet_count == 0:
        no_new_tweets = '<p align="center">No tweets matching {0} were captured on {1}</p>'.format(search_string, crawl_time_html)
        with open(html_file, 'a', encoding="utf-8") as html_out:
            html_out.write(no_new_tweets)

    html_footer = """
        </div>

        <footer id="page">
        <hr>
        <br>
        created with <a href="http://github.com/edsu/twarc">twarc</a>.
        <br>
        <br>
        </footer>

        </body>
        </html>
        """

    with open(html_file, 'a') as html_out:
        html_out.write(html_footer)


def build_html(feeds):
    for feed in feeds:
        print("Building HTML for {0}".format(feed))
        feed_dict = feeds[feed]
        build_html_for_feed(feed_dict)
