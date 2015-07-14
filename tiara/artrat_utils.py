import random,time 
import global_data
import os, signal
import os.path
import database
import sys, json
import data_gatherer

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
        tweet = g_data.ApiHandler().ShowStatus(tweet.GetInReplyToStatusId(), tweet.GetInReplyToUserId())
    for k in symbols.keys():
        for w2 in g_data.WordFamily(k):
            if not w2 in symbols:
                symbols[w2] = symbols[k]
    return symbols

def ArtRatReplyTo(g_data, personality, tweet=None, user=None, retries=10):
    import artrat.public as ar
    symbols = GetConversationSymbols(g_data, tweet=tweet,user=user)
    for i in xrange(retries):
        result = ar.Generate(personality, symbols, requireSymbols = tweet is not None)
        if result["success"]:
            g_data.TraceInfo("The symbol we used is %s" % result["symbols"])
            result = result["body"]
            if not tweet is None:
                result = '@' + tweet.GetUser().GetScreenName() + " " + result
            if len(result) <= 140:
                return result
            else:
                g_data.TraceWarn("Failing long tweet \"%s\"" % result)
        else:
            g_data.TraceWarn(result["error"])
    return None

def RefreshArticles(g_data):
    import artrat.article_rat as atc
    abs_prefix = os.path.join(os.path.dirname(__file__), "../artrat_data")
    sl = g_data.SocialLogic()
    directory = os.path.join(abs_prefix, sl.params["reply"]["personality"])
    if not os.path.isdir(directory):
        os.makedirs(directory)
    for source in sl.params["reply"]["sources"]:
        print directory
        atc.RefreshArticles(source, directory, sl.params["reply"]["personality"], g_data.TraceInfo)
        
def ResetArticles(g_data):
    import artrat.article_rat as atc
    abs_prefix = os.path.join(os.path.dirname(__file__), "../artrat_data")
    sl = g_data.SocialLogic()
    directory = os.path.join(abs_prefix, sl.params["reply"]["personality"])
    if not os.path.isdir(directory):
        os.makedirs(directory)
    atc.Reset(directory, sl.params["reply"]["personality"], g_data.TraceInfo)

def ArticleRat(personalities, logfn):
    import artrat.article_rat as atc
    abs_prefix = os.path.join(os.path.dirname(__file__), "../artrat_data")
    for p,_ in personalities:
        directory = os.path.join(abs_prefix, p)
        if not os.path.isdir(directory):
            os.makedirs(directory)
    atc.ArticleRat(abs_prefix, personalities, log=logfn)

def InsertArticle(url, personality, logfn):
    import artrat.article_rat as atc
    abs_prefix = os.path.join(os.path.dirname(__file__), "../artrat_data")
    directory = os.path.join(abs_prefix, personality)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    atc.DownloadAndProcess(url,
                           directory,
                           personality,
                           log=logfn)

def ArticleInsertionThread(logfn):
    dbmgr = data_gatherer.MakeFakeDataMgr()
    count = 0
    while True:
        nxt = dbmgr.PopArticle()
        if nxt is None:
            count += 1
            logfn("Queue empty?  Thats %d times in a row! Going to sleep until it fills" % count)
            time.sleep(60 * 60)
            continue
        count = 0
        InsertArticle(nxt[0], nxt[1], logfn)
        dbmgr.FinishArticle(nxt[0], nxt[1])

if __name__ == "__main__":
    if sys.argv[1] == "reset":
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + '/config.json','r') as f:
            conf = json.load(f)
            for b in conf["bots"]:
                if b["social_logic"]["reply"]["mode"] == "artrat"            :
                    ResetArticles(global_data.GlobalData(name=b["twitter_name"]))
    
