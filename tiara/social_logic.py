import os, time
import rewriter as r
import random
from util import *
import json
import persisted as p
import ticker as t
import vocab as v
import artrat_utils as au

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
        for user in user_list:
            if user.GetProtected():
                continue
            score = self.ScoreUser(user)
            if score > 0 and float(score)/(score + self.bestNewFriendScore) > random.uniform(0,1):
                self.g_data.TraceInfo("Interested in new friend @%s with score %d" % (user.GetScreenName(), score))
                self.bestNewFriendScore = score
                self.bestNewFriend = user

    # we shall eventually replace this with a learning machine
    #
    def ScoreUser(self, user):
        if self.g_data.dbmgr.EverFollowed(user.GetId()):
            return -1
        if len(self.g_data.dbmgr.GetAffliction(user.GetId())) > 0:
            return -1 
        numFriends = user.GetFriendsCount()
        numFollowers = user.GetFollowersCount()
        result = 0
        if 'follow' in user.GetScreenName().lower():
            return -1 # because fuck you, thats why
        if user.GetProtected():
            return -1 # I don't want to talk to you anyways!
        if numFriends < 100 or numFollowers < 100:
            return -1 # stay away from people with very few friends!
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

        return result

    def BotherRandom(self):
        result = self.g_data.ApiHandler().GetFriendIDs(screen_name=self.g_data.myName)
        if result is None or result == []:
            return None
        random.shuffle(result)
        for uid in result[:min(30,len(result))]:
            u = self.g_data.ApiHandler().ShowUser(user_id = uid)
            if self.BotherUserAppropriate(u):
                if self.Bother(user_id=uid):
                    return True

    def Bother(self, screen_name=None, user_id=None):
        if not screen_name is None:
            self.g_data.TraceInfo("Bothering @%s" % screen_name)
        else:
            self.g_data.TraceInfo("Bothering id = %s" % user_id)
        tweets = self.g_data.ApiHandler().ShowStatuses(screen_name = screen_name, user_id=user_id)
        if tweets is None or tweets == []:
            return None
        for t in tweets:
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
        ts = self.g_data.dbmgr.MostRecentTweet(user.GetId())
        if not ts is None and not OlderThan(ts, 7):
            return False
        if len(self.g_data.dbmgr.GetAffliction(user.GetId())) > 0:
            return False
        stats = self.HistoryStatistics(user)
        if stats["attempts"] > 1 and stats["conversations"] == 0: # they probably aren't into it
            return False
        return True

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
        

    def HistoryStatistics(self, user):
        tweets = self.g_data.dbmgr.TweetHistory(user.GetId())
        ids = set([t.GetId() for t,s in tweets] + [s.GetId() for t,s in tweets])
        roots = set([])
        rootUrls = []
        initiatesUrls = []
        initiates = 0
        for c,p in tweets:
            if not p.GetInReplyToStatusId() in ids:
                if p.GetUser().GetId() == user.GetId() and p.GetInReplyToScreenName() != self.g_data.myName:
                    rootUrls.append(GetURL(p))
                    roots.add(c.GetId())
                else:
                    initiatesUrls.append(GetURL(p))
                    initiates = initiates + 1
        responses = len([t for t,s in tweets if t.GetUser().GetId() == user.GetId()])
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
        stats = self.HistoryStatistics(user)
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

    def GatherSources(self):
        src = random.choice(self.params["reply"]["sources"])
        ss = self.g_data.ApiHandler().ShowStatuses(screen_name=src)
        if ss is None:
            return None
        for s in ss:
            for url in (s.urls if not s.urls is None else []):
                self.g_data.dbmgr.PushArticle(url.expanded_url, s.GetId(), self.params["reply"]["personality"])
    
    def Act(self):
        self.Reply()
        for t in self.tickers:
            t.Tick()
    
