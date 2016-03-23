# BHL TWARC
Bentley Historical Library's implementation of [twarc](https://github.com/edsu/twarc), used to capture searches of hashtags and mentions using the Twitter API

## Requirements
* [Python 2.7](https://www.python.org/)
* [twarc](https://github.com/edsu/twarc)
* [requests](http://docs.python-requests.org/en/master/)

## BHL TWARC Set Up
* Clone the repository
* `cd bhl_twarc`
* Create a configuration file called `feeds.txt`
* Entries in the configuration file should look like this:
```
[examplehashtag]
crawl:True
name:Example Hashtag (#examplehashtag)
crawl_type:hashtag
search_string:#examplehashtag

[examplementions]
crawl:False
name: Example Mentions (@examplementions)
crawl_type:mentions
search_string:@examplementions
```

## Twitter API Set Up
* Create an application at [apps.twitter.com](http://apps.twitter.com)
* Note the consumer key, consumer secret, access token, and access token secret associated with the application

## Use
* Run `bhl_twarc.py`
* The script will parse entries in `feeds.txt` and initiate a Twitter search for all that have a `crawl` setting of `True`
* `bhl_twarc` will create the following directory structure (using the example configuration above as an example), if it does not exist:
```
feeds
  examplehashtag
    html
    json
    logs
    media
      profile_images
      tweet_images
```

* The raw JSON returned by the Twitter API will be saved to the feed's `json` directory
* Logs for the API search will be stored to a `twarc.log` file in the `logs` directory
* An HTML file created using the Twitter JSON will be stored in the `html` directory 
** (based heavily off of [twarc's wall.py](https://github.com/edsu/twarc/blob/master/utils/wall.py))
* Profile images and embedded images from tweets will be fetched and stored in the corresponding folders in the `media` directory
** The paths to images in the converted HTML files will point to the images stored in the `media` directory
** Several CSV files will also be created and stored in the `media` directory, indicating each image's original URL and download location
* An `index.html` file will be created in the feed's root directory containing a table pointing to the raw JSON and converted HTML for each crawl
* The README.txt from `bhl_twarc\lib` will be copied to the feed's root directory


### First time use
The first time `bhl_twarc.py` is run, it will prompt you for your consumer key, consumer secret, access token, and access token secret, which will then be stored in a file called `.twarc`

### Options
Several command line arguments can be passed to `bhl_twarc.py`. 
* To perform a search of a particular feed:
```
bhl_twarc.py -f examplehashtag
```

* To exclude feeds from a crawl:
```
bhl_twarc.py -e examplehashtag
```

* To run a test crawl, using a configuration file called `feeds_test.txt`, the results of which will be saved to a directory called `test_crawls`
```
bhl_twarc.py -t
```
