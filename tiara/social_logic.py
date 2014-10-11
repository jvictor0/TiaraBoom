import os
import rewriter as r
import random
from util import *

AVERAGE_MINUTES_TO_ACT = 120

class SocialLogic:
    def __init__(self, g_data):
        self.g_data = g_data
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + '/max_id',"r") as f:
            self.max_id = int(f.readline())
        self.untilNextAction = int(random.expovariate(1.0/AVERAGE_MINUTES_TO_ACT))
        self.tix = 0

        self.bestNewFriend      = None
        self.bestNewFriendScore = 0

    def SetMaxId(self, max_id):
        log_assert(self.max_id <= max_id, "Attempt to set max_id to smaller than current value, risk double-posting", self.g_data)
        self.g_data.TraceInfo("    Setting max_id to %d" % max_id)
        self.max_id = max_id
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + '/max_id',"w") as f:
            print >>f, str(max_id)
                 
    def Reply(self):
        tweets = self.g_data.ApiHandler().RecentTweets(self.max_id, count=5)
        if tweets is None:
            # warning already in log, no need to warn again
            return
        for t in tweets[-1::-1]:
            if self.ReplyTo(t):
                self.SetMaxId(t.GetId())
            

    def ReplyTo(self, tweet):
        self.g_data.TraceInfo("replying to tweet %d" %  tweet.GetId())
        response = r.ChooseResponse(self.g_data, tweet=tweet)
        if response:
            result = self.g_data.ApiHandler().Tweet(response, in_reply_to_status=tweet)
            if not result is None:
                return True
        self.g_data.TraceWarn("Failed to reply to tweet %d" % tweet.GetId())
        return False

    def RandomFollowerID(self, name):
        result = self.g_data.ApiHandler().GetFollowerIDs(screen_name=name)
        if result is None or result == []:
            return None
        return random.choice(result)

    def StalkTwitter(self):
        follower = self.RandomFollowerID("TiaraBoom1")
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

    def Bother(self, user):
        self.g_data.TraceInfo("Bothering @%s" % user.GetScreenName())
        tweets = self.g_data.ApiHandler().ShowStatuses(screen_name = user.GetScreenName())
        for t in tweets:
            if self.BotherAppropriate(t):
                self.ReplyTo(t)
                return
        self.g_data.TraceWarn("No tweet by @%s was found botherable!" % user.GetScreenName())
        
    def TweetFrom(self, user):
        self.g_data.TraceInfo("Tweeting from @%s" % user.GetScreenName())
        response = r.ChooseResponse(self.g_data, user=tweet)
        if response:
            result = self.g_data.ApiHandler().Tweet(response)
            if not result is None:
                return
        self.g_data.TraceWarn("Failed to tweet from @%s" % user.GetSceenName())

    def BotherAppropriate(self, tweet):
        if tweet.lang != "en":
            return False
        if len(tweet.hashtags) > 2:
            return False
        if len(tweet.media) != 0 or len(tweet.urls) != 0:
            return False
        if not tweet.GetInReplyToStatusId() is None or not tweet.GetRetweeted_status() is None:
            return False
        return True

    def Follow(self):
        if self.bestNewFriend is None:
            return
        user = self.bestNewFriend
        self.bestNewFriend = None
        self.bestNewFriendScore = 0
        result = self.g_data.ApiHandler().Follow(user.GetScreenName())
        if result is None:
            return
        fn = random.choice([lambda : self.TweetFrom(user),
                            lambda : self.Bother(user)])
        fn()
                
    def Act(self):
        self.untilNextAction -= 1
        if self.untilNextAction == 0:
            self.untilNextAction = int(random.expovariate(1.0/AVERAGE_MINUTES_TO_ACT))
            self.g_data.TraceInfo("Performing action! %d cycles until next action." % self.untilNextAction)
        self.Reply()
        if self.tix % 15 == 0:
            self.StalkTwitter()
        self.tix += 1
    
