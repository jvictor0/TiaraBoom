import artrat.public as ar
import artrat.article_rat as atc
import os
import os.path

def GetConversationSymbols(g_data, tweet=None, user=None):
    symbols = {}
    if not user is None:
        g_data.dbmgr.TFIDF(user=user)
    multiplier = 1.0
    while not tweet is None:
        print tweet.GetId()
        tfidfs = g_data.dbmgr.TFIDF(tweet = tweet)
        for t, sc in tfidfs:
            if not t in symbols:
                symbols[t] = 0
            symbols[t] += multiplier * sc
        if tweet.GetInReplyToStatusId() is None:
            break
        multiplier = multiplier * 0.5
        tweet = g_data.ApiHandler().ShowStatus(tweet.GetInReplyToStatusId())
    for k in symbols.keys():
        for w2 in g_data.WordFamily(k):
            if not w2 in symbols:
                symbols[w2] = symbols[k]
    return symbols

def ArtRatReplyTo(g_data, personality, tweet=None, user=None, retries=10):
    symbols = GetConversationSymbols(g_data, tweet=tweet,user=user)
    for i in xrange(retries):
        result = ar.Generate(personality, symbols)
        if result["success"]:
            result = result["body"]
            if not tweet is None:
                result = '@' + tweet.GetUser().GetScreenName() + " " + result
            if len(result) <= 140:
                return result
            else:
                g_data.TraceWarn("Failing long tweet \"%s\"" % result)
    return None

def RefreshArticles(g_data):
    assert False, "NO REFRESH!"
    abs_prefix = os.path.join(os.path.dirname(__file__), "../artrat_data")
    sl = g_data.SocialLogic()
    directory = os.path.join(abs_prefix, sl.params["reply"]["personality"])
    if not os.path.isdir(directory):
        os.makedirs(directory)
    for source in sl.params["reply"]["sources"]:
        atc.RefreshArticles(source, directory, sl.params["reply"]["personality"], g_data.TraceInfo)
        
def ResetArticles(g_data):
    abs_prefix = os.path.join(os.path.dirname(__file__), "../artrat_data")
    sl = g_data.SocialLogic()
    directory = os.path.join(abs_prefix, sl.params["reply"]["personality"])
    if not os.path.isdir(directory):
        os.makedirs(directory)
    atc.Reset(directory, sl.params["reply"]["personality"], g_data.TraceInfo)
