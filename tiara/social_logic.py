import os, time
import rewriter as r
import random
from util import *
import json
import persisted as p
import ticker as t
import vocab as v
import sys
import artrat_utils as au
import server

class SocialLogic:
    def __init__(self, g_data, args):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
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
        SKD("gravitation_parameter",     self.params, 0.0)
        SKD("gravitation_targets",       self.params, [])
        SKD("friend_score_coefficients", self.params, {})
        if len(self.params["gravitation_targets"]) == 0:
            self.params["gravitation_parameter"] = 0.0

        SKD("practice-mode", self.params["reply"], False)

        if self.params["reply"]["mode"] == "classic":
            SKD("alliteration_mode",  self.params["reply"], False)
        elif self.params["reply"]["mode"] == "artrat":
            if not "personality" in self.params["reply"] or not "sources" in self.params["reply"]:
                self.invalid = True
                return
            if len(self.params["reply"]) != 4:
                self.invalid = True
                return
        else:
            self.invalid = True
            return
            
        if len(self.params) != 6:
            self.invalid = True
            return

        fsc = self.params["friend_score_coefficients"]
        SKD("favorites"     , fsc, 0.25)
        SKD("retweets"      , fsc, 0.25)
        SKD("conversations" , fsc, 1.0)
        SKD("avg_convo_len" , fsc, 0.0)
        SKD("decayed_convo_len" , fsc, 2.0)
        SKD("response_prob" , fsc, 1.0)
        SKD("virginity"     , fsc, 1.0)
        if len(fsc) != 7:
            self.invalid = True
            return
        
        self.tickers.append(t.Ticker(g_data, self.params["mean_follow_time"], lambda: self.Follow(), "Follow"))
        self.tickers.append(t.Ticker(g_data, self.params["mean_bother_time"], lambda: self.BotherRandom(), "BotherRandom"))
        self.tickers.append(t.Ticker(g_data, 16, lambda: self.StalkTwitter(), "StalkTwitter", exponential=False))
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
        for t in tweets[-1::-1]:
            if self.SignalsStop(t):
                self.SetMaxId(t.GetId())
                continue
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
            

    def RandomFriendID(self, name):
        result = self.g_data.ApiHandler().GetFriendIDs(screen_name=name)
        if result is None or result == []:
            return None
        return random.choice(result)

    def StalkTwitter(self):
        if random.uniform(0,1) > self.params["gravitation_parameter"]:
            self.StalkTwitterGravitate()
        else:
            self.StalkTwitterHops()


    def StalkTwitterGravitate(self):
        target = random.choice(self.params["gravitation_targets"])
        followers = random.choice([self.g_data.ApiHandler().GetFollowerIDs,self.g_data.ApiHandler().GetFriendIDs])(user_id=target)
        if followers is None:
            return
        random.shuffle(followers)
        cands = []
        for i in xrange(30):
            if len(followers) == i:
                break
            u = self.g_data.ApiHandler().ShowUser(user_id = followers[i])
            if not u is None:
                cands.append(u)
        self.UpdateNewBestFriend(cands)

    def StalkTwitterHops(self):
        friends = self.g_data.ApiHandler().GetFriendIDs(screen_name=self.g_data.myName)
        if friends is None or friends == []:
            return None
        random.shuffle(friends)
        follower = random.choice(friends)
        followers = random.choice([self.g_data.ApiHandler().GetFollowers,self.g_data.ApiHandler().GetFriends])(user_id=follower)
        self.g_data.ApiHandler().ShowStatuses(user_id=follower)
        if followers is None:
            return
        self.UpdateNewBestFriend(followers)

    def UpdateNewBestFriend(self, user_list):
        random.shuffle(user_list)
        user_list = user_list[0:75]
        for user in user_list:
            if user.GetProtected():
                continue
            score = self.ScoreUser(user)
            if score > 0 and float(score)/(score + self.bestNewFriendScore) > random.uniform(0,1):
                self.bestNewFriendScore = score
                self.bestNewFriend = user
        if self.bestNewFriend is None:
            self.g_data.TraceInfo("Can't find a new friend.")
        else:
            self.g_data.TraceInfo("Interested in new friend @%s with score %d" % (self.bestNewFriend.GetScreenName(), self.bestNewFriendScore))


    # we shall eventually replace this with a learning machine
    #
    def ScoreUser(self, user):
        if self.g_data.dbmgr.EverFollowed(user.GetId()):
            return -1
        if len(self.g_data.dbmgr.GetAffliction(user.GetId())) > 0:
            return -1 
        numFriends = user.GetFriendsCount()
        numFollowers = user.GetFollowersCount()
        if numFriends > 5000 or numFollowers > 5000:
            return -1
        result = 0
        if 'follow' in user.GetScreenName().lower():
            return -1 # because fuck you, thats why
        if user.GetProtected():
            return -1 # I don't want to talk to you anyways!
        if numFriends < 100 or numFollowers < 100:
            return -1 # stay away from people with very few friends!
        statuses = self.g_data.ApiHandler().ShowStatuses(user_id=user.GetId())
        if statuses is None or len(statuses) < 10:
            return -1 # either there was a problem or he dont tweet much
        both = len([t for t in statuses if self.BotherAppropriate(t)])
        if both == 0:
            return -1
        result += 3 * (float(both) / len(statuses))
        if 400 < numFriends <= 600:
            result += 3
        elif 600 < numFriends <= 1000:
            result +=  2
        elif 200 < numFriends <= 400:
            result += 2
        elif 100 < numFriends <= 200:
            result += 1
        if 400 < numFollowers <= 600:
            result += 3
        elif 600 < numFollowers <= 1000:
            result +=  2
        elif 200 < numFollowers <= 400:
            result += 2
        elif 100 < numFollowers <= 200:
            result += 1
        if self.params["reply"]["mode"] == "artrat":
            dist = self.g_data.dbmgr.TFIDFDistance([user.GetId()])
            if user.GetId() in dist:
                result += 100 * dist[user.GetId()]
            else:
                return -1 # nothing in common with us!
        return result

    def BotherRandom(self):
        result = self.g_data.ApiHandler().GetFriendIDs(screen_name=self.g_data.myName)
        if result is None or result == []:
            return None
        random.shuffle(result)
        for uid in result[:min(30,len(result))]:
            u = self.g_data.ApiHandler().ShowUser(user_id = uid)
            if u is None:
                return None
            if self.BotherUserAppropriate(u):
                if self.Bother(user_id=uid):
                    return True

    def Bother(self, screen_name=None, user_id=None):
        if not screen_name is None:
            self.g_data.TraceInfo("Bothering @%s" % screen_name)
        else:
            self.g_data.TraceInfo("Bothering id = %s" % user_id)
        tweets = self.g_data.ApiHandler().ShowStatuses(screen_name = screen_name, user_id=user_id)
        if tweets is None or len(tweets) == 0:
            return None
        for t in tweets:
            assert not t is None, tweets
            if self.BotherAppropriate(t):
                return self.ReplyTo(t)
        self.g_data.TraceWarn("No tweet by @%s was found botherable!" % tweets[0].GetUser().GetScreenName())
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

    def BotherAppropriate(self, tweet):
        if tweet.lang != "en":
            return False
        if len(tweet.hashtags) > 2:
            return False
        if len(tweet.media) != 0:
            return False
        if len(tweet.user_mentions) != 0:
            return False
        if not tweet.GetRetweeted_status() is None:
            return False
        if "follow" in tweet.GetText().lower():
            return False
        if OlderThan(MySQLTimestampToPython(TwitterTimestampToMySQL(tweet.GetCreatedAt())), 7):
            return False
        return True

    def BotherUserAppropriate(self, user):
        if self.UserInactive(user):
            return False
        if len(self.g_data.dbmgr.GetAffliction(user.GetId())) > 0:
            return False
        stats = self.HistoryStatistics(user)
        if stats["attempts"] > 1 and stats["conversations"] == 0: # they probably aren't into it
            return False
        return True

    def UserInactive(self, user):
        ts = self.g_data.dbmgr.MostRecentTweet(user.GetId())
        return ts is None or OlderThan(ts, 7)
    
    def Follow(self):
        if self.bestNewFriend is None:
            return None
        user = self.bestNewFriend
        self.bestNewFriend = None
        self.bestNewFriendScore = 0
        result = self.g_data.ApiHandler().Follow(screen_name = user.GetScreenName())
        if result is None:
            return None
        fn = random.choice([lambda : self.TweetFrom(user),
                            lambda : self.Bother(screen_name = user.GetScreenName())])
        return fn()
        

    def HistoryStatistics(self, user=None, uid=None):
        if uid is None:
            uid = user.GetId()
        tweets = self.g_data.dbmgr.TweetHistory(uid)
        ids = set([t.GetId() for t,s in tweets] + [s.GetId() for t,s in tweets])
        roots = set([])
        rootUrls = []
        initiatesUrls = []
        initiates = 0
        for c,p in tweets:
            if not p.GetInReplyToStatusId() in ids:
                if p.GetUser().GetId() == uid and p.GetInReplyToUserId() != self.g_data.dbmgr.GetUserId():
                    rootUrls.append(GetURL(p))
                    roots.add(c.GetId())
                else:
                    initiatesUrls.append(GetURL(p))
                    initiates = initiates + 1
        responses = len([t for t,s in tweets if t.GetUser().GetId() == uid])
        favs = sum([t.GetFavoriteCount() for t,s in tweets if t.GetUser().GetScreenName() == self.g_data.myName])
        rts =  sum([t.GetRetweetCount()  for t,s in tweets if t.GetUser().GetScreenName() == self.g_data.myName])
        conversations = initiates
        for c,p in tweets:
            if p.GetId() in roots:
                conversations += 1
        return { "attempts" : len(roots),
                 "initiates" : initiates,
                 "conversations" : conversations,
                 "responses" : responses,
                 "initiatesUrls" : initiatesUrls,
                 "conversationUrls" : rootUrls,
                 "favorites" : favs,
                 "retweets"  : rts
                 }

    def ScoreFriendFeatures(self, user):
        stats = self.HistoryStatistics(user=user)
        return {
            "favorites"     : stats["favorites"],
            "retweets"      : stats["retweets"],
            "conversations" : stats["conversations"],
            "avg_convo_len" : float(stats["responses"])/stats["conversations"] if stats["conversations"] != 0 else 0.0,
            "decayed_convo_len" : Decay(float(stats["responses"])/stats["conversations"] if stats["conversations"] != 0 else 0.0),
            "response_prob" : float(stats["conversations"])/stats["attempts"]  if stats["attempts"] != 0 else 0.0,
            "virginity"     : 1.0/(2**stats["attempts"]),
            }

    def ScoreFriend(self, user):
        if not self.BotherUserAppropriate(user):
            return -1
        coefs = self.params["friend_score_coefficients"]
        features = self.ScoreFriendFeatures(user)
        return sum([coefs[k] * features[k] for k in features.keys()])

    def FriendBotLogics(self):
        return [g.SocialLogic() for g in self.g_data.g_datas] # silly function?  

    def GatherSources(self, src=None):
        if src is None:
            src = self.g_data.dbmgr.GetSource(self.params["reply"]["personality"])
        ss = self.g_data.ApiHandler().ShowStatuses(user_id=src)
        if ss is None:
            return None
        count = 0
        for s in ss:
            used = False
            for url in (s.urls if not s.urls is None else []):
                self.g_data.TraceInfo("pushing article %s" % url.expanded_url)
                used = self.g_data.dbmgr.PushArticle(url.expanded_url, s.GetId(), self.params["reply"]["personality"]) or used
            if used:
                if count < 28 and s.GetRetweetCount() > 0:
                    count = count + 1
                    retweeted = self.g_data.ApiHandler().GetRetweets(s.GetId())
                    for u in retweeted:
                        self.g_data.TraceInfo("pushing source %s" % u.GetUser().GetScreenName())                    
                        self.g_data.dbmgr.AddSource(self.params["reply"]["personality"], u.GetUser().GetId())
                
    def IsArtRat(self):
        return self.params["reply"]["mode"] == "artrat"
                
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
