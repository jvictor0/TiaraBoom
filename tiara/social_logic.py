import time
import rewriter as r
import re
import random
from util import *
import persisted as p
import ticker as t
import sys
import server
import os.path

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
        elif self.IsEvidence():
            path = os.path.join(os.path.dirname(__file__), "../evidence/arguments", self.params["reply"]["argument_file"])
            self.evidence_manager = g_data.dbmgr.GetEvidenceManager(path)
        else:
            print "unknown mode"
            self.invalid = True
            return
            
        if len(self.params) != 3:
            print "not 3", (len(self.params),self.params)
            self.invalid = True
            return

        self.tickers.append(t.Ticker(g_data, self.params["mean_follow_time"], lambda: self.Follow(), "Follow"))
        self.tickers.append(t.Ticker(g_data, self.params["mean_bother_time"], lambda: self.Bother(), "BotherRandom"))
        self.tickers.append(t.Ticker(g_data, 16, lambda: self.g_data.dbmgr.Act(), "ManageDb", exponential=False))

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
        elif self.IsEvidence():
            msg = self.evidence_manager.Reply(tweet)
            response = msg.Text()
        else:
            assert False, self.params["reply"]
            
        if not response is None:
            if self.params["reply"]["practice-mode"]:
                self.g_data.TraceInfo("(PRACTICE) %s" % response)
                self.g_data.TraceInfo("(PRACTICE) %s" % GetURL(tweet))
                return tweet
            result = self.g_data.ApiHandler().Tweet(response, in_reply_to_status=tweet)
            if not result is None:
                if self.IsEvidence():
                    self.evidence_manager.InsertMsg(result, msg)
                return result
        self.g_data.TraceWarn("Failed to reply to tweet %d" % tweet.GetId())
        return None
            

    def Bother(self, screen_name=None,user_id=None):
        if screen_name is not None:
            u = self.g_data.ApiHandler().ShowUser(screen_name=screen_name)
            user_id = u.GetId()
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
        elif self.IsEvidence():
            return None
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
        self.g_data.dbmgr.GCFriends(limit=2)
        return fn()
        
    def FriendBotLogics(self):
        return [g.SocialLogic() for g in self.g_data.g_datas] # silly function?

    def IsEvidence(self):
        return self.params["reply"]["mode"] == "evidence"

    def Act(self):
        self.Reply()
        for tc in self.tickers:
            tc.Tick()
    

