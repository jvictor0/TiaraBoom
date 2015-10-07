import time
import rewriter as r
import re
import random
from util import *
import persisted as p
import ticker as t
import sys
import artrat_utils as au
import server

class SocialLogic:
    def __init__(self, g_data, args):
        self.g_data = g_data
        self.max_id = p.PersistedObject("max_id_%s" % g_data.myName, 0)

        self.bestNewFriend      = None
        self.bestNewFriendScore = 0
        self.tickers = []
        self.params = args
        self.invalid = False

        SKD("mean_follow_time",          self.params, 4 * 60)
        SKD("mean_bother_time",          self.params, 4 * 60)
        SKD("reply",                     self.params, {"mode" : "classic", "alliteration_mode" : False })

        SKD("practice-mode", self.params["reply"], False)

        if self.params["reply"]["mode"] == "classic":
            SKD("alliteration_mode",  self.params["reply"], False)
        elif self.params["reply"]["mode"] == "artrat":
            if not "personality" in self.params["reply"]:
                print "no personality"
                self.invalid = True
                return
            if len(self.params["reply"]) != 3:
                print "wrong param len"
                self.invalid = True
                return
        else:
            print "not artrat"
            self.invalid = True
            return
            
        if len(self.params) != 3:
            print "not 3", (len(self.params),self.params)
            self.invalid = True
            return

        self.tickers.append(t.Ticker(g_data, self.params["mean_follow_time"], lambda: self.Follow(), "Follow"))
        self.tickers.append(t.Ticker(g_data, self.params["mean_bother_time"], lambda: self.Bother(), "BotherRandom"))
        self.tickers.append(t.Ticker(g_data, 16, lambda: self.g_data.dbmgr.Act(), "ManageDb", exponential=False))
        if self.params["reply"]["mode"] == "artrat":
            self.tickers.append(t.Ticker(g_data, 16, lambda: self.GatherSources(), "GatherSources", exponential=False))

    def SetMaxId(self, max_id):
        log_assert(self.max_id.Get() <= max_id, "Attempt to set max_id to smaller than current value, risk double-posting", self.g_data)
        self.g_data.TraceInfo("Setting max_id to %d" % max_id)
        self.max_id.Set(max_id)
                 
    def Reply(self):
        tweets = self.g_data.ApiHandler().RecentTweets(self.max_id.Get(), count=5)
        if tweets is None:
            # warning already in log, no need to warn again
            return None
        for t in sorted(tweets, key = lambda tw: tw.GetId()):
            if self.SignalsStop(t):
                self.SetMaxId(t.GetId())
                continue
            self.g_data.dbmgr.EnqueueFollower(t.GetUser().GetId())
            if self.ReplyTo(t) or self.g_data.read_only_mode:
                self.SetMaxId(t.GetId())
        return True

    def SignalsStop(self, t):
        for w in ["stop",
                  "bye",
                  "go away",
                  "block"]:
            if w in t.GetText().lower():
                self.g_data.TraceWarn("Not responding to %d, contains '%s'" % (t.GetId(), w))
                return True
        return False

    def ReplyTo(self, tweet):
        self.g_data.TraceInfo("replying to tweet %d" %  tweet.GetId())    
        
        if self.params["reply"]["mode"] == "classic":
            response = r.ChooseResponse(self.g_data, tweet=tweet, alliteration_mode=self.params["reply"]["alliteration_mode"])
        elif self.params["reply"]["mode"] == "artrat":
            response = au.ArtRatReplyTo(self.g_data, self.params["reply"]["personality"], tweet=tweet)
        else:
            assert False, self.params["reply"]
            
        if not response is None:
            if self.params["reply"]["practice-mode"]:
                self.g_data.TraceInfo("(PRACTICE) %s" % response)
                self.g_data.TraceInfo("(PRACTICE) %s" % GetURL(tweet))
                return tweet
            result = self.g_data.ApiHandler().Tweet(response, in_reply_to_status=tweet)
            if not result is None:
                return result
        self.g_data.TraceWarn("Failed to reply to tweet %d" % tweet.GetId())
        return None
            

    def Bother(self, screen_name=None,user_id=None):
        if screen_name is not None:
            u = self.g_data.ApiHandler().ShowUser(screen_name=screen_name)
            user_id=u.GetId()
        if user_id is not None:
            self.g_data.TraceInfo("Bothering id = %s" % user_id)
        s = self.g_data.dbmgr.NextTargetStatus(user_id)
        if s is not None:
            return self.ReplyTo(s)
        self.g_data.TraceWarn("No tweet was found botherable!")
        return None
    
    def TweetFrom(self, user):
        self.g_data.TraceInfo("Tweeting from @%s" % user.GetScreenName())
        
        if self.params["reply"]["mode"] == "classic":            
            response = r.ChooseResponse(self.g_data, user=user, alliteration_mode=self.params["reply"]["alliteration_mode"])
        elif self.params["reply"]["mode"] == "artrat":
            response = au.ArtRatReplyTo(self.g_data, self.params["reply"]["personality"], user=user)
        else:
            assert False, self.params["reply"]

        if not response is None:
            if self.params["reply"]["practice-mode"]:
                self.g_data.TraceInfo("(PRACTICE) %s" % response)
                self.g_data.TraceInfo("(PRACTICE) %s" % GetURL(tweet))
                return tweet
            result = self.g_data.ApiHandler().Tweet(response)
            if not result is None:
                return result
        self.g_data.TraceWarn("Failed to tweet from @%s" % user.GetScreenName())
        return None

    def Follow(self):
        uid = self.g_data.dbmgr.NextTargetCandidate()
        if uid is None:
            return None
        user = self.g_data.ApiHandler().Follow(user_id=uid)
        if user is None:
            return None
        self.g_data.ApiHandler().ShowStatuses(user_id=user.GetId())
        fn = random.choice([lambda : self.TweetFrom(user),
                            lambda : self.Bother(user.GetId())])
        return fn()
        
    def FriendBotLogics(self):
        return [g.SocialLogic() for g in self.g_data.g_datas] # silly function?  

    def GatherSources(self, src=None):
        if src is None:
            src = self.g_data.dbmgr.GetSource(self.params["reply"]["personality"])
        ss = self.g_data.ApiHandler().ShowStatuses(user_id=src)
        if ss is None:
            return None
        count = 0
        overconfirmed = False
        precount = 0
        for s in ss:
            used = False
            for url in (s.urls if not s.urls is None else []):
                precount = precount + 1
                used = self.g_data.dbmgr.PushArticle(url.expanded_url, s.GetId(), self.params["reply"]["personality"]) or used
            if used:
                if not overconfirmed and count < 28 and s.GetRetweetCount() > 0:
                    count = count + 1
                    retweeted = self.g_data.ApiHandler().GetRetweets(s.GetId())
                    for u in retweeted:
                        overconfirmed = not self.g_data.dbmgr.AddSource(self.params["reply"]["personality"], u.GetUser().GetId())
                        if overconfirmed:
                            break
        self.g_data.TraceInfo("Inserted %d articles and added %d unconfirmed sources" % (precount, count))
                
    def IsArtRat(self):
        return self.params["reply"]["mode"] == "artrat"

    def ArtRatPersonality(self):
        return self.params["reply"]["personality"]
                
    def Act(self):
        self.Reply()
        for t in self.tickers:
            t.Tick()
    

if __name__ == "__main__":
    if sys.argv[1] == "gather_sources":        
        g_datas = server.GDatas()
        while True:
            for g_data in g_datas:
                if g_data.SocialLogic().IsArtRat():
                    g_data.SocialLogic().GatherSources()
            print "sleepy time"
            time.sleep(8 * 60)
