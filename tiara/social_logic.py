import rewriter as r

def Reply(g_data):
    tweets = g_data.ApiHandler().RecentTweets(count=5)
    if tweets is None:
        # warning already in log, no need to warn again
        return
    for t in tweets[-1::-1]:
        if ReplyTo(g_data, t):
            g_data.ApiHandler().SetMaxId(t.GetId())
            

def ReplyTo(g_data, tweet):
        g_data.TraceInfo("replying to tweet %d" %  tweet.GetId())
        response = r.ChooseResponse(tweet, g_data, inReply = True)
        if response:
            result = g_data.ApiHandler().Tweet(response, in_reply_to_status=tweet)
            if not result is None:
                return True
        g_data.TraceWarn("Failed to reply to tweet %d" % tweet.GetId())
        return False
