from tiara import api_handler as a
from tiara import rewriter as r
from tiara import vocab as v
from tiara import global_data as g

import twitter

g_data = None

def InitializeGlobalData():
    global g_data
    if g_data is None:
        g_data = g.GlobalData()
    

def HurshalIterator():
    InitializeGlobalData()
    tweet = g_data.ApiHandler().ShowStatus(516828410635489280)
    return r.TweetsIterator(g_data, tweet=tweet)

def TestIterator():
    it = HurshalIterator()
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
    InitializeGlobalData()
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
    InitializeGlobalData()
    vocab = v.Vocab(g_data)
    vocab.Add("legging")
    vocab.Register("legging")
    for i in xrange(10):
        print vocab["(Kf)"]


def TestRewriter():
    InitializeGlobalData()
    tweet = g_data.ApiHandler().ShowStatus(516828410635489280)
    print r.ChooseResponse(g_data, tweet=tweet)

