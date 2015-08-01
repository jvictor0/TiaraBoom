import random,time 
import global_data
import os, signal
import os.path
import sys, json
import data_gatherer
import Queue
import chat
import twitter
import threading

def GetConversationSymbols(g_data, tweet=None, user=None):
    symbols = {}
    if not user is None:
        g_data.dbmgr.TFIDF(user=user)
    multiplier = 1.0
    while not tweet is None:
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
        result = ar.Generate(personality, symbols, requireSymbols = (tweet is not None))
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
            g_data.TraceWarn("ArtRatReplyTo error: %s" % result["error"])
    return None

def ArtRatChat(personality):
    g_data = global_data.GlobalData()
    class ArtRatChat(chat.Chat):
        def response(self, line):
            t = twitter.Status()
            t.SetText(line)
            return str(ArtRatReplyTo(g_data, personality, tweet=t))
    ArtRatChat().cmdloop()

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

def ArticleInsertionMultiThreaded(num_threads):
    queue = Queue.Queue()
    def worker():        
        worker_dbmgr = data_gatherer.MakeFakeDataMgr()
        while True:
            try:
                nxt = queue.get(False)
            except Queue.Empty:
                return
            InsertArticle(nxt[0], nxt[1])
            worker_dbmgr.FinishArticle(nxt[0], nxt[1])
    dbmgr = data_gatherer.MakeFakeDataMgr()
    while True:
        arts = dbmgr.PopAllArticles()
        for a in arts:
            queue.put(a[0],a[1])
        if queue.empty():
            print "queue empty...  sleeping for 5 minutes"
            time.sleep(5 * 60)
        threads = [threading.Thread(target=worker) for _ in xrange(num_threads)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        assert queue.empty()
        
if __name__ == "__main__":
    if sys.argv[1] == "reset":
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + '/config.json','r') as f:
            conf = json.load(f)
            for b in conf["bots"]:
                if b["social_logic"]["reply"]["mode"] == "artrat"            :
                    ResetArticles(global_data.GlobalData(name=b["twitter_name"]))
    if sys.argv[1] == "article_rat":
        num_threads = 4 if len(sys.argv) == 2 else int(sys.argv[2])
        print "Article Rat with %d threads" % num_threads 
        ArticleInsertionMultiThreaded(num_threads)
    if sys.argv[1] == "chat":
        ArtRatChat(sys.argv[2])
