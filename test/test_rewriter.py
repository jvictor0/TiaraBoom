from ..tiara import api_handler as a
from ..tiara import rewriter as r

import twitter

def TestIterator():
    api = a.FakeApiHandler()
    tweet = twitter.Status()
    tweet.SetText("Original Tweet")
    tweet.SetInReplyToStatusId(0)
    u = twitter.User()
    u.SetId(0)
    tweet.SetUser(u)
    it = r.TweetsIterator(tweet, api)

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

