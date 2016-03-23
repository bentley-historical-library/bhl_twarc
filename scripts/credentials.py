import ConfigParser
import os

def make_credentials_dict(credentials):
    credentials_dict = {}
    credentials_dict['consumer_key'] = credentials.get('main','consumer_key')
    credentials_dict['consumer_secret'] = credentials.get('main','consumer_secret')
    credentials_dict['access_token'] = credentials.get('main','access_token')
    credentials_dict['access_token_secret'] = credentials.get('main','access_token_secret')
    return credentials_dict

def save_credentials(credentials_file, consumer_key, consumer_secret, access_token, access_token_secret):
    credentials = ConfigParser.ConfigParser()
    credentials.add_section("main")
    credentials.set("main", 'consumer_key', consumer_key)
    credentials.set("main", 'consumer_secret', consumer_secret)
    credentials.set("main", 'access_token', access_token)
    credentials.set("main", 'access_token_secret', access_token_secret)
    with open(credentials_file, 'w') as config_file:
        credentials.write(config_file)
    return credentials

def load_credentials(credentials_file):
    if os.path.exists(credentials_file):
        credentials = ConfigParser.ConfigParser()
        credentials.read(credentials_file)
    else:
        print("Please enter Twitter authentication credentials")
        consumer_key = raw_input('consumer key: ')
        consumer_secret = raw_input('consumer secret: ')
        access_token = raw_input('access_token: ')
        access_token_secret = raw_input('access token secret: ')
        credentials = save_credentials(credentials_file, consumer_key, consumer_secret, access_token, access_token_secret)
    return make_credentials_dict(credentials)