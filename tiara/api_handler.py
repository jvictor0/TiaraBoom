import twitter
from twitterkeys import api
import os
from util import *

CACHE_SIZE = 25

class ApiHandler():
    def __init__(self, g_data):
        self.g_data = g_data
        self.cache = {}
            
    def CacheInsert(self, key, value, old_value=None):
        self.cache[key] = (value,0)
        if old_value == None:
            old_value = CACHE_SIZE
        for k, v in self.cache.items():
            if v[1] < old_value:
                if v[1] + 1 < CACHE_SIZE:
                    self.cache[k] = (v[0],v[1]+1)
                else: 
                    del self.cache[k]
        assert len(self.cache) <= CACHE_SIZE
            
    def ApiCall(self, name, args, fun, cache=True):
        if cache and (name,args) in self.cache:
            result = self.cache[(name,args)]
            self.g_data.TraceInfo("  %s(%s) cache hit!" % (name,args))
            self.CacheInsert((name,args), result[0], result[1])
            return result[0]
        try:
            result = fun()
            self.g_data.TraceInfo("  %s(%s) success!" % (name,args))
            if cache:
                self.CacheInsert((name,args), result)
            return result
        except Exception as e:
            self.g_data.TraceWarn("  %s(%s) failure" % (name,args))
            self.g_data.TraceWarn(str(e))
            return None

    def ShowStatus(self, status_id):
        return self.ApiCall("ShowStatus", status_id, lambda: api.GetStatus(status_id))

    def Tweet(self, status, in_reply_to_status=None):
        if self.g_data.read_only_mode:
            self.g_data.TraceWarn("  Tweet in Read-Only-Mode: \"%s\"" % status)
            return False
        if (not in_reply_to_status is None) and in_reply_to_status.GetUser().GetScreenName() == "TiaraBoom1":
            self.g_data.TraceWarn("  Attempt to respond to self is a bad idea, posting general tweet")
            in_reply_to_status = None
        result = self.ApiCall("Tweet", status,
                              lambda: api.PostUpdate(status, in_reply_to_status_id=in_reply_to_status.GetId()),
                              cache=False)
        
        if not result is None:
            if not in_reply_to_status is None:
                self.g_data.LogTweet(in_reply_to_status.GetUser().GetScreenName(),
                                     in_reply_to_status.GetText(),
                                     in_reply_to_status.GetId(),
                                     in_reply_to_status.GetInReplyToStatusId())
            reply_id = None if in_reply_to_status is None else in_reply_to_status.GetId()
            self.g_data.LogTweet("TiaraBoom1", status, result.GetId(), reply_id)
        return result
        
    def ShowStatuses(self, screen_name=None, user_id=None, count=200, trim_user=True):
        return self.ApiCall("ShowStatuses",  NotNone(screen_name, user_id),
                            lambda:  api.GetUserTimeline(screen_name=screen_name,
                                                         user_id=user_id,
                                                         count=count,
                                                         include_rts=False,
                                                         trim_user=trim_user,
                                                         exclude_replies=False),
                            cache=False)

    def GetFollowerIDs(self, screen_name=None, user_id=None):
         return self.ApiCall("GetFollowerIDs", NotNone(screen_name, user_id),
                             lambda: api.GetFollowerIDs(screen_name=screen_name,user_id=user_id,cursor=-1),
                             cache=False)

    def GetFollowers(self, user_id=None, screen_name=None):
        def GFP(scn,uid):
            next,prev,data = api.GetFollowersPaged(screen_name=scn,user_id=uid,cursor=-1)
            return [twitter.User.NewFromJsonDict(x) for x in data['users']]

        return self.ApiCall("GetFollowers", NotNone(screen_name, user_id), 
                             lambda: GFP(screen_name, user_id),
                             cache=False)

    def RecentTweets(self, max_id, count=5):
        return self.ApiCall("RecentTweets","",
                            lambda: api.GetSearch(term="to:TiaraBoom1",
                                                  count=count,
                                                  result_type="recent",
                                                  include_entities=False,
                                                  since_id=max_id,
                                                  lang="en"),
                            cache=False)
    
    def Follow(self, screen_name):
        if self.g_data.read_only_mode:
            self.g_data.TraceWarn("  Follow in Read-Only-Mode: \"@%s\"" % screen_name)
            return False
        return self.ApiCall("Follow",screen_name,lambda: api.CreateFriendship(screen_name=screen_name), cache=False)
