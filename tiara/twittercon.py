import twitter

acces_token = "https://api.twitter.com/oauth/access_token"
request_token = "https://api.twitter.com/oauth/request_token"
auth_url = "https://api.twitter.com/oauth/authorize"
consumer_key = "38RfXBRt9mYgfSEDFEFIq54Yf"
consumer_secret = "PnQgrJsTdlzX4HAj1SfBDh37YzpwQGWZGiG9ks2sePwPhbNiBa"
access_token = "2489360282-UDuE2XKmRzBGF8k6mBOwodBmBboHnDkhWsegvId"
access_token_secret = "RagyWx2CaiVDSmrEsaipM0FDT9i6pmyYc7Jcwde5ZL2Gg"


api = twitter.Api(consumer_key=consumer_key,
                  consumer_secret=consumer_secret, 
                  access_token_key=access_token, 
                  access_token_secret=access_token_secret) 
