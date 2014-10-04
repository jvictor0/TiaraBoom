from tiara import api_handler as a
from tiara import rewriter as r
from tiara import vocab as v
from tiara import global_data as g

import twitter

def FakeIterator():
    api = a.FakeApiHandler()
    tweet = twitter.Status()
    tweet.SetText("Original Tweet")
    tweet.SetInReplyToStatusId(0)
    u = twitter.User()
    u.SetId(0)
    tweet.SetUser(u)
    return r.TweetsIterator(tweet, api)

def TestIterator():
    it = FakeIterator()
    for i in xrange(2):
        print i
        while True:
            res = it.Next(False)
            if not res:
                break
            print res
        print "done"
        while True:
            res = it.Next(True)
            if not res:
                break
            print res
        it.Reset()

def TestVocab():
    g_data = g.GlobalData()
    print "loaded"
    vocab = v.Vocab(g_data)
    vocab.Add("smelled")
    print vocab["(Hfd)"]
    print vocab["(Ifd)"]
    print vocab["(It)"]
    print vocab["(Kf)"]
    vocab.Add("tasted")
    print "add"
    print vocab["(Hfd)"]
    print vocab["(Ifd)"]
    print vocab["(It)"]
    print vocab["(Kf)"]
    vocab.Register("taste")
    print "register"
    for i in xrange(10):
        print "loop"
        print vocab["(Hfd)"]
    print vocab["(Ifd)"]
    print vocab["(It)"]
    print vocab["(Kf)"]
    vocab.Add("tasted")
    print vocab.used
    print "re-add"
    for i in xrange(10):
        print "loop"
        print vocab["(Hfd)"]
    
def TestCooccuring():
    g_data = g.GlobalData()
    vocab = v.Vocab(g_data)
    vocab.Add("legging")
    vocab.Register("legging")
    for i in xrange(10):
        print vocab["(Kf)"]


def TestRewriter():
    tweets = FakeIterator()
    g_data = g.GlobalData()
    for i in xrange(10):
        tweets.Reset()
        rw = r.Rewriter(tweets, g_data.NextSentence("Original Tweet"), g_data)
        result = rw.Rewrite()
        if result:
            return result
    return False

