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
        self.tickers.append(t.LambdaTicker(g_data, 4*60, lambda: self.Follow(), "follow"))
        self.tickers.append(t.LambdaTicker(g_data, 4*60, lambda: self.BotherRandom(), "BotherRandom"))
        self.tickers.append(t.LambdaStraightTicker(16, lambda: self.StalkTwitter()))
        self.tickers.append(t.LambdaStraightTicker(16, lambda: self.g_data.dbmgr.Act()))
        
        self.followMethod = p.PersistedObject("followMethod", 'hops')
        self.followCore   = p.PersistedList("followCore")

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


    def RandomFriendID(self, name):
        result = self.g_data.ApiHandler().GetFriendIDs(screen_name=name)
        if result is None or result == []:
            return None
        return random.choice(result)

    def SetStrategy(self, args):
        if len(args) == 2 and args[0] == "target" and args[1] in ["hops","gravitate"]:
            self.followMethod.Set(args[1])
            return "ok"
        elif args == ["target","show"]:
            return self.followMethod.Get()
        elif len(args) == 3 and args[0] == "gravitate" and args[1] in ["add","remove"] and args[2][0] == '@':
            target = args[2][1:]
            if args[1] == "add" and target in self.followCore:
                self.g_data.ApiHandler().Follow(screen_name=target)
                return "already gravitating towards @%s" % target
            elif args[1] == "remove":
                self.followCore.Set([n for n in self.followCore.Get() if n != target])
                return "ok"
            else:
                self.followCore.Append(target)
                return "ok"
        elif args == ["gravitate","show"]:
            return str(self.followCore.Get())
        elif args == ["help"]:
            return "'set_strategy target <target_strategy_name>' sets the target strategy.  The strategy 'hops' targets followers of followers.  The strategy 'gravitate' follows friends and followers of individuals in a specific list.  'set_strategy gravitate (add/remove) @gbop' will add/remove @gbop to the list being gravitated towards, and 'set_strategy gravitate show' shows thes gravitate list."
        return "syntax error"
        

    def StalkTwitter(self):
        if self.followMethod.Get() == "hops":
            self.StalkTwitterHops()
        elif self.followMethod.Get() == "gravitate":
            self.StalkTwitterGravitate()
        else:
            assert False, followMethod.Get()

    def StalkTwitterGravitate(self):
        target = random.choice(self.followCore.Get())
        followers = random.choice([self.g_data.ApiHandler().GetFollowers,self.g_data.ApiHandler().GetFriends])(user_id=target)
        if followers is None:
            return
        self.UpdateNewBestFriend(followers)

    def StalkTwitterHops(self):
        friends = self.g_data.ApiHandler().GetFriendIDs(screen_name=self.g_data.myName)
        if friends is None or friends == []:
            return None
        random.shuffle(friends)
        for i in xrange(min(85,len(friends))):
            self.g_data.ApiHandler().ShowStatuses(user_id=friends[i]) 
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
            #self.g_data.ApiHandler().ShowStatuses(screen_name=user.GetScreenName())  not yet
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
        if self.g_data.dbmgr.EverFollowed(user):
            return -1
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
        result = self.g_data.ApiHandler().GetFriendIDs(screen_name=self.g_data.myName)
        if result is None or result == []:
            return None
        random.shuffle(result)
        for uid in result[:min(30,len(result))]:
            u = self.g_data.ApiHandler().ShowUser(user_id = uid)
            if self.BotherUserAppropriate(u):
                self.Bother(user_id=uid)
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
        if "follow" in tweet.GetText().lower():
            return False
        if OlderThan(MySQLTimestampToPython(TwitterTimestampToMySQL(tweet.GetCreatedAt())), 7):
            return False
        return True

    def BotherUserAppropriate(self, user):
        ts = self.g_data.dbmgr.MostRecentTweet(user.GetId())
        if not ts is None and not OlderThan(ts, 7):
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
    
