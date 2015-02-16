import artrat.public as ar

def GetConversationSymbols(g_data, tweet):
    symbols = {}
    multiplier = 1.0
    while True:
        tfidfs = g_data.dbmgr.TDIDF(tweet = tweet)
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

def ArtRatReplyTo(g_data, tweet, personality, retries=10):
    symbols = GetConversationSymbols(g_data, tweet)
    for i in xrange(retries):
        result = ar.Generate(personality, symbols)
        if result["success"]:
            return result["body"]
    return None
