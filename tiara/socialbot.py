import persisted as p
import social_logic as sl
import baked_tweets as bt
import frontlines as fl
import random

class SocialBotLogic:
    def __init__(self, g_data, args):
        self.g_data = g_data
        self.max_id = p.PersistedObject("max_id", 0)
        self.reachable    = p.PersistedSet("reachable")
        self.following    = p.PersistedSet("following")
        self.targets      = p.PersistedDict("targets")
        self.tweeted      = p.PersistedSet("tweeted")
        self.attacked     = p.PersistedSet("attacked")

        self.toReachQueue = p.PersistedList("toReachQueue")
        if not self.toReachQueue.initializedFromCache:
            for f in self.following.Get():
                self.toReachQueue.Get().append((f,-1))

        self.hash_bucket = args["hash_bucket"]
        assert len(self.targets) != 0

        self.tickers = []

        self.tickers.append(sl.StatsLogger(g_data,15))
        self.tickers.append(sl.LambdaTicker(g_data, 60, lambda: self.FollowBack(), "followback"))
        self.tickers.append(sl.LambdaTicker(g_data, 60, lambda: self.StalkReachable(), "stalk"))
        self.tickers.append(sl.LambdaStraightTicker(20, lambda: self.ProcessToReachQueue()))
        self.tickers.append(sl.LambdaTicker(g_data, 60*24, lambda : self.Tweet(), "tweet"))
        self.tickers.append(sl.LambdaTicker(g_data, 60, lambda : self.Attack(), "attack"))

                
    def Follow(self, user_id):
        if user_id in self.following:
            return False
        if not self.g_data.ApiHandler().Follow(user_id=user_id):
            return None
        self.following.Insert(user_id)
        self.toReachQueue.Append((user_id,-1))
        return True

    def ProcessToReachQueue(self):
        self.g_data.TraceInfo("Processing queue, len = %d" % len(self.toReachQueue))
        for i in xrange(10):
            if len(self.toReachQueue) == 0:
                return True
            uid, page = self.toReachQueue.Front()
            self.toReachQueue.PopFront()
            result = self.g_data.ApiHandler().GetFollowerIDsPaged(user_id = uid, cursor = page)
            if result is None:
                self.g_data.TraceWarn("throwing away page %d,%d" % (uid,page))
                continue
            followers,next_page = result 
            if next_page != 0:
                self.toReachQueue.Append((uid,next_page))
            for f in followers:
                if f in self.targets:
                    self.reachable.Insert(f)
        return True

    def FollowBack(self):
        followers = self.g_data.ApiHandler().GetFollowerIDs(screen_name=self.g_data.myName)
        if followers is None:
            return None
        count = 0
        for f in followers:
            if f in self.targets:
                if self.Follow(f):
                    count = count + 1
                    if count > 5:
                        self.g_data.TraceWarn("POSSIBLE BACKLOG OF TARGETED FOLLOWBACKERS!")
                        return True
        return True
    
    def SetMaxId(self, max_id):
        log_assert(self.max_id.Get() <= max_id.Get(), "Attempt to set max_id to smaller than current value, risk double-posting", self.g_data)
        self.g_data.TraceInfo("Setting max_id to %d" % max_id)
        self.max_id.Set(max_id)
                 
    def Reply(self):
        tweets = self.g_data.ApiHandler().RecentTweets(self.max_id.Get(), count=5)
        if tweets is None:
            return None
        for t in tweets[-1::-1]:
            if self.ReplyTo(t):
                self.SetMaxId(t.GetId())
        return True

    def ReplyTo(self, tweet):
        return None # this is like, the most important thing!

    def ScoreUser(self, i):
        if i % 15 != self.hash_bucket:
            return 0
        if i in self.targets:
            return self.targets.Lookup(i)["score"][self.g_data.myName]
        return 0

    def StalkReachable(self):
        best_score = -1
        best = -1
        reachables = list(self.reachable.Get())
        random.shuffle(reachables)
        for i in reachables:
            if not i in self.following:
                score = self.ScoreUser(i)
                if score > best_score:
                    best = i
                    best_score = score
        if best != -1:
            return self.Follow(best)
        self.g_data.TraceWarn("No followable reachables")
        targets = list(self.targets.Get().keys())
        random.shuffle(targets)
        for i in targets:
            if not i in self.following:
                score = self.ScoreUser(i)
                if score > best_score:
                    best = i
                    best_score = score
        if best != -1:
            return self.Follow(best)
        self.g_data.TraceWarn("No followable targets")
        return None


    def Tweet(self):
        possible_tweets = [t for t in bt.socialbots[self.g_data.myName] if t not in self.tweeted]
        if len(possible_tweets) == 0:
            self.g_data.TraceWarn("OUT OF TWEETS!")
            return None
        tweet = random.choice(possible_tweets)
        self.tweeted.Insert(tweet)
        return self.g_data.ApiHandler().Tweet(tweet)

    def Attack(self):
        self.g_data.TraceInfo("ATTACK! choosing frontline")
        timeline = self.g_data.ApiHandler().GetHomeTimeline()
        if timeline is None:
            return None
        timeline = [t for t in timeline if t.GetUser().GetId() in self.targets and t.GetUser().GetFollowersCount() < 1500]
        timeline = [t for t in timeline if not t.GetId() in self.attacked]
        response, target = fl.TargetAndRespond(self.g_data, timeline, fl.socialbots_frontlines)
        if not target is None:
            self.attacked.Insert(target.GetId())
            result = self.g_data.ApiHandler().Tweet(response, in_reply_to_status=target)
            if not result is None:
                return True
            self.g_data.TraceWarn("Failed to reply to tweet %d" % tweet.GetId())
            return None
        self.g_data.TraceWarn("Failed to find someone to ATTACK!  Length of timeline = %d.  Shall find another." % len(timeline))
        users = list(self.following.Get())
        random.shuffle(users)
        users = users[:min(len(users),30)]
        for user in users:
            tweets = self.g_data.ApiHandler().ShowStatuses(user_id=user)
            response, target = fl.TargetAndRespond(self.g_data, timeline, fl.socialbots_frontlines)
            if not target is None:
                self.attacked.Insert(target.GetId())
                result = self.g_data.ApiHandler().Tweet(response, in_reply_to_status=target)
                if not result is None:
                    return True
                self.g_data.TraceWarn("Failed to reply to tweet %d" % tweet.GetId())
                return None
        self.g_data.TraceWarn("Couldnt find a tweet from %d users" % len(users))
        return None
            
    def Act(self):
        for t in self.tickers:
            t.Tick()
