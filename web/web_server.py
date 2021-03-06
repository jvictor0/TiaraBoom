from flask import Flask, render_template, jsonify, request
import tiara.data_gatherer as dg
import sys, pickle

reload(sys)
sys.setdefaultencoding("utf-8")

app = Flask(__name__)

# returns a list of lists of tweets, representing recent conversations between bots and the outside world
def GetConversations(limit, offset):
    all_args = { k: len(v) == 0 or v[0] for k,v in request.args.lists() } 
    return dg.MakeFakeDataMgr("").RecentConversations(limit, offset, all_args)

@app.route('/')
def hello_world():
    #with open('convos2.p', 'rb') as f:
    #  convos = pickle.load(f)
    convos = GetConversations(10, 0)

    jconvos = {}

    for i in range(len(convos)):
        tweets = []
        for tweet in convos[i].tweets:
            t = {}
            t['sn'] = tweet.user.screen_name
            t['pic'] = tweet.user.profile_image_url
            t['text'] = tweet.text
            t['tweet_id'] = str(tweet.id)
            tweets.append(t)
        jconvos['convo' + str(i)] = tweets  
    return render_template('bots.html', convos=jconvos)

def run():
    app.debug = True
    app.run()
