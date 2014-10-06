import twitter
from twitterkeys import api
import os
from util import *

CACHE_SIZE = 26

class ApiHandler():
    def __init__(self, g_data):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + '/max_id',"r") as f:
            self.max_id = int(f.readline())
        self.g_data = g_data
        self.cache = {}
            
    def SetMaxId(self, max_id):
        log_assert(self.max_id <= max_id, "Attempt to set max_id to smaller than current value, risk double-posting", self.g_data)
        self.g_data.TraceInfo("    Setting max_id to %d" % max_id)
        self.max_id = max_id
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + '/max_id',"w") as f:
            print >>f, str(max_id)

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
        if g_data.read_only_mode:
            self.g_data.TraceWarn("  Tweet in Read-Only-Mode: \"%s\"" % status)
            return None
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
        
    def ShowStatuses(self, screen_name, count=500):
        return self.ApiCall("ShowStatuses",screen_name,
                            lambda: api.GetSearch(term="from:" + screen_name,
                                                  count=count,
                                                  result_type="recent",
                                                  include_entities=False,
                                                  lang="en"),
                            cache=False)

    def RecentTweets(self, count=5):
        return self.ApiCall("RecentTweets","",
                            lambda: api.GetSearch(term="to:TiaraBoom1",
                                                  count=count,
                                                  result_type="recent",
                                                  include_entities=False,
                                                  since_id=self.max_id,
                                                  lang="en"),
                            cache=False)
