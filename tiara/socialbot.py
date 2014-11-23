import persisted as p
import social_logic as sl
import smart_sentence as ss
import charicatures as ch
import random

class SocialBotLogic:
    def __init__(self, g_data):
        self.g_data = g_data
        self.max_id = p.PersistedObject("max_id", 0)
        self.reachable    = p.PersistedSet("reachable")
        self.following    = p.PersistedSet("following")
        self.targets      = p.PersistedDict("targets")
        self.toReachQueue = p.PersistedObject("toReachQueue")
        if self.toReachQueue.Get() == None:
            self.toReachQueue.Set([])
            for f in self.following.Get():
                self.toReachQueue.Get().append((f,-1))
            self.toReachQueue.Update()
        assert len(self.targets.Get()) != 0

        self.statsLogger = sl.StatsLogger(g_data,15)
        self.followbacker = sl.LambdaTicker(g_data, 60, lambda: self.FollowBack(), "followback")
        self.stalker = sl.LambdaTicker(g_data, 120, lambda: self.StalkReachable(), "stalk")
        self.toReacher = sl.LambdaStraightTicker(20, lambda: self.ProcessToReachQueue())
        
    def Follow(self, user_id):
        if self.following.Contains(user_id):
            return False
        if not self.g_data.ApiHandler().Follow(user_id=user_id):
            return None
        self.following.Insert(user_id)
        self.toReachQueue.Get().append((user_id,-1))
        self.toReachQueue.Update()
        return True

    def ProcessToReachQueue(self):
        self.g_data.TraceInfo("Processing queue, len = %d" % len(self.toReachQueue.Get()))
        for i in xrange(10):
            if len(self.toReachQueue.Get()) == 0:
                return True
            uid, page = self.toReachQueue.Get()[0]
            self.toReachQueue.Get().pop(0)
            self.toReachQueue.Update()
            result = self.g_data.ApiHandler().GetFollowerIDsPaged(user_id = uid, cursor = page)
            if result is None:
                self.g_data.TraceWarn("throwing away page %d,%d" % (uid,page))
                continue
            followers,next_page = result 
            if page != 0:
                self.toReachQueue.Get().append((uid,next_page))
                self.toReachQueue.Update()
            for f in followers:
                if self.targets.Contains(f):
                    self.reachable.Insert(f)
        return True

    def FollowBack(self):
        followers = self.g_data.ApiHandler().GetFollowerIDs(screen_name=self.g_data.myName)
        if followers is None:
            return None
        count = 0
        for f in followers:
            if self.targets.Contains(f):
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
        return self.targets.Lookup(i)["score"][self.g_data.myName]

    def StalkReachable(self):
        best_score = -1
        best = -1
        reachables = list(self.reachable.Get())
        random.shuffle(reachables)
        for i in reachables:
            if not self.following.Contains(i):
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
            if not self.following.Contains(i):
                score = self.ScoreUser(i)
                if score > best_score:
                    best = i
                    best_score = score
        if best != -1:
            return self.Follow(best)
        self.g_data.TraceWarn("No followable targets")
        return None


    def Tweet(self):
        tweet = ss.RunCharicature(ch.socialbots[self.g_data.myName])
        return self.g_data.ApiHandler.Tweet(tweet)
            
    def Act(self):
        self.toReacher.Tick()
        self.statsLogger.Tick()
        self.followbacker.Tick()
        self.stalker.Tick()
