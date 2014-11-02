from __future__ import unicode_literals
import requests
from requests_oauthlib import OAuth1
from urlparse import parse_qs
import sys
import json

REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize?oauth_token="
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"


def setup_oauth(CONSUMER_KEY, CONSUMER_SECRET):
    """Authorize your app via identifier."""
    # Request token
    oauth = OAuth1(CONSUMER_KEY, client_secret=CONSUMER_SECRET)
    r = requests.post(url=REQUEST_TOKEN_URL, auth=oauth)
    credentials = parse_qs(r.content)

    resource_owner_key = credentials.get('oauth_token')[0]
    resource_owner_secret = credentials.get('oauth_token_secret')[0]
    
    # Authorize
    authorize_url = AUTHORIZE_URL + resource_owner_key
    print 'Please go here and authorize: ' + authorize_url
    
    verifier = raw_input('Please input the verifier: ')
    oauth = OAuth1(CONSUMER_KEY,
                   client_secret=CONSUMER_SECRET,
                   resource_owner_key=resource_owner_key,
                   resource_owner_secret=resource_owner_secret,
                   verifier=verifier)

    # Finally, Obtain the Access Token
    r = requests.post(url=ACCESS_TOKEN_URL, auth=oauth)
    credentials = parse_qs(r.content)
    token = credentials.get('oauth_token')[0]
    secret = credentials.get('oauth_token_secret')[0]

    return token, secret


if __name__ == "__main__":
    cons_key, cons_secret = sys.argv[2], sys.argv[3]
    token, secret = setup_oauth(cons_key, cons_secret)
    result = {
        "password"         : sys.argv[4],
        "twitter_name"     : sys.argv[1],
        "read_only_mode"   : False,
        "social_logic"     : {
            "name" : "SocialBotsStartup"
            },
        "authentication"   : {
            "consumer_key"        : cons_key,
            "consumer_secret"     : cons_secret,
            "access_token_key"    : token,
            "access_token_secret" : secret
            }   
        }
    print result
    with open("data/config.json","w") as f:
        print >>f, json.dumps(result)

