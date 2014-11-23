import os, time
import rewriter as r
import random
from util import *
import json
import persisted as p

class Ticker(object):
    def __init__(self, tix):
        self.time = 0
        self.last_time = time.time()
        self.limit = tix * 60
        self.avg_limit = tix * 60

    def Tick(self):
        t = time.time()
        self.time += (t - self.last_time)
        self.last_time = t
        while self.time > self.limit:
            self.Tock()
            self.time -= self.limit

    def Tock(self):
        pass

class VerboseExpTicker(object):
    def __init__(self, g_data, tix, name='action'):
        self.time = 0
        self.last_time = time.time()
        self.avg_limit = tix * 60
        self.g_data = g_data
        self.name = name
        self.limit = random.expovariate(1.0/self.avg_limit)
        self.g_data.TraceInfo("Startup! %f minutes until first %s." % (self.limit/60, name))

    def Tick(self):
        t = time.time()
        self.time += (t - self.last_time)
        self.last_time = t
        while self.time > self.limit:
            self.Tock()
            self.time -= self.limit
            self.limit = random.expovariate(1.0/self.avg_limit)
            self.g_data.TraceInfo("Action Performed! %f minutes until next %s." % (self.limit/60, self.name))
            return


    def Tock(self):
        pass

class LambdaTicker(VerboseExpTicker):
    def __init__(self, g_data, tix, fun, name='action'):
        super(LambdaTicker,self).__init__(g_data, tix, name),
        self.fun = fun

    def Tock(self):
        self.fun()

class LambdaStraightTicker(Ticker):
    def __init__(self, g_data, tix, fun):
        super(LambdaTicker,self).__init__(g_data, tix),
        self.fun = fun

    def Tock(self):
        self.fun()


class StatsLogger(Ticker):
    def __init__(self, g_data, tix):
        super(StatsLogger,self).__init__(tix)
        self.g_data = g_data
        self.logger = logging.getLogger('Status')
        self.logger.setLevel(logging.DEBUG)
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        handler = logging.FileHandler(abs_prefix + "/status_log")
        handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s', "%Y-%m-%d %H:%M:%S"))
        self.logger.addHandler(handler)

    def Tock(self):
        me = self.g_data.ApiHandler().ShowUser(self.g_data.myName)
        if me is not None:
            self.logger.info("%d %d" % (me.GetFriendsCount(), me.GetFollowersCount()))

AVERAGE_MINUTES_TO_ACT = 120
AVERAGE_MINUTES_TO_RESPOND = 120

class SocialLogic:
    def __init__(self, g_data):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        self.max_id = p.PersistedObject("max_id", 0)
        # I best set max_id from the legacy just in case
        #
        if self.max_id.Get() == 0:
            try:
                with open(abs_prefix + "/max_id","r") as f:
                    self.max_id.Set(int(f.readline()))
            except IOError as e:
                assert e[0] == 2 and e[1] == 'No such file or directory'
        self.g_data = g_data

        self.untilNextAction = int(random.expovariate(1.0/AVERAGE_MINUTES_TO_ACT))
        self.g_data.TraceInfo("%d cycles until first action." % self.untilNextAction)
        
        self.untilNextResponse = int(random.expovariate(1.0/AVERAGE_MINUTES_TO_RESPOND))
        self.g_data.TraceInfo("%d cycles until first action." % self.untilNextResponse)

        self.tix = 0

        self.bestNewFriend      = None
        self.bestNewFriendScore = 0
        self.statsLogger = StatsLogger(g_data,15)

    def SetMaxId(self, max_id):
        log_assert(self.max_id.Get() <= max_id.Get(), "Attempt to set max_id to smaller than current value, risk double-posting", self.g_data)
        self.g_data.TraceInfo("Setting max_id to %d" % max_id)
        self.max_id.Set(max_id)
                 
    def Reply(self):
        tweets = self.g_data.ApiHandler().RecentTweets(self.max_id.Get(), count=5)
        if tweets is None:
            # warning already in log, no need to warn again
            return None
        for t in tweets[-1::-1]:
            if self.ReplyTo(t):
                self.SetMaxId(t.GetId())
        return True

    def ReplyTo(self, tweet):
        self.g_data.TraceInfo("replying to tweet %d" %  tweet.GetId())
        response = r.ChooseResponse(self.g_data, tweet=tweet)
        if not response is None:
            result = self.g_data.ApiHandler().Tweet(response, in_reply_to_status=tweet)
            if not result is None:
                return True
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
                self.ReplyTo(t)
                return True
        self.g_data.TraceWarn("No tweet by @%s was found botherable!" % tweets[0].GetUser().GetScreenName())
        return None
        
    def TweetFrom(self, user):
        self.g_data.TraceInfo("Tweeting from @%s" % user.GetScreenName())
        response = r.ChooseResponse(self.g_data, user=user)
        if not response is None:
            result = self.g_data.ApiHandler().Tweet(response)
            if not result is None:
                return True
        self.g_data.TraceWarn("Failed to tweet from @%s" % user.GetScreenName())
        return None

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
        self.untilNextAction -= 1
        self.untilNextResponse -= 1
        if self.untilNextAction <= 0:
            self.untilNextAction = int(random.expovariate(1.0/AVERAGE_MINUTES_TO_ACT))
            self.g_data.TraceInfo("Performing action! %d cycles until next action." % self.untilNextAction)
            self.Follow()
        if self.untilNextResponse <= 0:
            self.untilNextResponse = int(random.expovariate(1.0/AVERAGE_MINUTES_TO_RESPOND))
            self.g_data.TraceInfo("Performing response! %d cycles until next action." % self.untilNextResponse)
            self.BotherRandom()
        self.Reply()
        if self.tix % 15 == 0:
            self.StalkTwitter()
        self.tix += 1
        self.statsLogger.Tick()
    

AVERAGE_MINUTES_TO_FOLLOW_BACK = 60

class FollowBacker(VerboseExpTicker):
    def __init__(self, g_data, tix):
        super(FollowBacker,self).__init__(g_data,tix)
        self.g_data = g_data
        
    def Tock(self):
        random.choice([lambda: self.g_data.SocialLogic().FollowBack(),
                       lambda: self.g_data.SocialLogic().FindFollowBacker()])()
        

class UserSnooper(Ticker):
    def __init__(self, g_data, hash_bucket):
        super(UserSnooper,self).__init__(16)
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        self.targets = []
        self.g_data = g_data
        with open(abs_prefix + "/targets","r") as f:
            for line in f:
                uid = int(line)
                if uid % 15 == hash_bucket:
                    self.targets.append(uid)
        with open(abs_prefix + "/targets_data","r") as f:
            for line in f:
                uid = int(line.split()[0])
                assert self.targets[-1] == uid
                print "pop " + str(uid)
                self.targets.pop()

    def Tock(self):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + "/targets_data","a") as f:
            for i in xrange(min(90,len(self.targets))):
                uid = self.targets.pop()
                data = self.g_data.ApiHandler().ShowStatuses(user_id = uid)
                if data is None:
                    f.write("%d []\n" % uid)
                else:
                    f.write("%d %s\n" % (uid,json.dumps([s.AsDict() for s in data])))
            
        

class FollowBackLogic:
    def __init__(self, g_data, config):
        self.g_data = g_data
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        self.friends = []
#        with open(abs_prefix + "/friendbots","r") as f:
#            for line in f:
#                self.friends.append(line.strip().split())
#        assert len(self.friends) == 15
        self.hash_bucket = int(config["hash_bucket"])
        self.pem  = abs_prefix + "/" + config["pem"]

        self.statsLogger  = StatsLogger (g_data, 15)
        self.snooper      = UserSnooper (g_data, self.hash_bucket)
        

    def Act(self):
        self.statsLogger.Tick()
        self.snooper.Tick()

    def Hashes(self, i):
        #return list(set([i*13 % 15, i * 17 % 15, i * 19 % 15]))
        return [self.hash_bucket]

    def FindFollowBacker(self):
        tweets = self.g_data.ApiHandler().Search("lang:en " + random.choice(["#follow",
                                                                             "#followback",
                                                                             "#followtrain",
                                                                             "#anotherfollowtrain",
                                                                             "#teamfollowback",
                                                                             "#tfb",
                                                                             "#mgwv"]))
        if tweets is None or len(tweets) == 0:
            return
        tweet = random.choice(tweets)
        self.Follow(tweet.GetUser())
        for u in tweet.user_mentions:
            if random.choice([True,False]):
                self.Follow(u)
        

    def Follow(self, f):
        uid = f.GetId()
        for h in self.Hashes(uid):
            if h == self.hash_bucket:
                if self.g_data.ApiHandler().Follow(screen_name=f.GetScreenName()) is None:
                    return False
                return True
            else:
                try:
                    QueryFriendBot("follow @%s" % f.GetSceenName(),
                                   self.friends[h][1],
                                   self.g_data.password,
                                   pem=self.pem)
                except Exception as e:
                    self.g_data.TraceWarn(str(e))
                    return False
        return True

    def FollowBack(self):
        followers = self.g_data.ApiHandler().GetFollowers(screen_name=self.g_data.myName)
        if followers is None:
            followers = []
        found = False
        for f in followers[:min(len(followers),4)]:
            if not self.Follow(f):
                break
            found = True
        if not found:
            self.FindFollowBacker()

    def RandomFriendID(self, name):
        result = self.g_data.ApiHandler().GetFollowerIDs(screen_name=name)
        if result is None or result == []:
            return None
        return random.choice(result)
