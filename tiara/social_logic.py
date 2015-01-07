import os, time
import rewriter as r
import random
from util import *
import json
import persisted as p
import ticker as t

class SocialLogic:
    def __init__(self, g_data, args):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        self.max_id = p.PersistedObject("max_id", 0)
        self.g_data = g_data

        self.alliteration_mode = args["alliteration_mode"]

        self.bestNewFriend      = None
        self.bestNewFriendScore = 0
        self.tickers = []
        self.tickers.append(t.StatsLogger(g_data,15))
        self.tickers.append(t.LambdaTicker(g_data, 180, lambda: self.Follow(), "follow"))
        self.tickers.append(t.LambdaTicker(g_data, 180, lambda: self.BotherRandom(), "BotherRandom"))
        self.tickers.append(t.LambdaStraightTicker(15, lambda: self.StalkTwitter()))
        self.tickers.append(t.LambdaStraightTicker(16, lambda: self.g_data.dbmgr.Act())
        
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
                self.g_data.ApiHandler().UnFollow(user_id=t.GetUser().GetId())
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
        response = r.ChooseResponse(self.g_data, tweet=tweet, alliteration_mode=self.alliteration_mode)
        if not response is None:
            result = self.g_data.ApiHandler().Tweet(response, in_reply_to_status=tweet)
            if not result is None:
                return result
        self.g_data.TraceWarn("Failed to reply to tweet %d" % tweet.GetId())
        return None


    def RandomFollowerID(self, name):
        result = self.g_data.ApiHandler().GetFollowerIDs(screen_name=name)
        if result is None or result == []:
            return None
        return random.choice(result)

    def StalkTwitter(self):
        follower = self.RandomFollowerID(self.g_data.myName)
        if follower is None:
            return
        followers = self.g_data.ApiHandler().GetFollowers(user_id=follower)
        if followers is None:
            return
        for user in followers:
            score = self.ScoreUser(user)
            if score is None:
                self.g_data.TraceInfo("Ending StalkTwitter after ScoreUser")
                return # we might be out of api calls or something, probably should end this stalk
            if score > self.bestNewFriendScore:
                self.g_data.TraceInfo("Interested in new friend @%s with score %d" % (user.GetScreenName(), score))
                self.bestNewFriendScore = score
                self.bestNewFriend = user

    # we shall eventually replace this with a learning machine
    #
    def ScoreUser(self, user):
        numFriends = user.GetFriendsCount()
        numFollowers = user.GetFollowersCount()
        result = 0
        if 'follow' in user.GetScreenName().lower() or 'follow' in user.GetName().lower():
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
        id = self.RandomFollowerID(self.g_data.myName)
        self.Bother(user_id=id)

    def Bother(self, screen_name=None, user_id=None):
        if not screen_name is None:
            self.g_data.TraceInfo("Bothering @%s" % screen_name)
        else:
            self.g_data.TraceInfo("Bothering id = %s" % user_id)
        tweets = self.g_data.ApiHandler().ShowStatuses(screen_name = screen_name, user_id=user_id, trim_user=False)
        if tweets is None or tweets == []:
            return None
        for t in tweets:
            if self.BotherAppropriate(t):
                return self.ReplyTo(t)
        self.g_data.TraceWarn("No tweet by @%s was found botherable!" % tweets[0].GetUser().GetScreenName())
        return None
        
    def TweetFrom(self, user):
        self.g_data.TraceInfo("Tweeting from @%s" % user.GetScreenName())
        response = r.ChooseResponse(self.g_data, user=user, alliteration_mode=self.alliteration_mode)
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
        
                
    def Act(self):
        self.Reply()
        for t in self.tickers:
            t.Tick()
    
