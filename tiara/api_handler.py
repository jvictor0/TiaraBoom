import twitter
import os
from util import *

class ApiHandler():
    def __init__(self, g_data, authentication):
        self.g_data = g_data
        self.api = twitter.Api(consumer_key=authentication["consumer_key"],
                               consumer_secret=authentication["consumer_secret"], 
                               access_token_key=authentication["access_token_key"], 
                               access_token_secret=authentication["access_token_secret"]) 
        self.errno = 0
            
    def ApiCall(self, name, args, fun, tp=None):
        self.errno = 0
        try:
            result = fun()
            self.g_data.TraceInfo("%s(%s) success!" % (name,args))
            if tp == "LOT":
                for t in result:
                    self.g_data.dbmgr.InsertTweet(t)
            return result
        except Exception as e:
            self.g_data.TraceWarn("%s(%s) failure" % (name,args))
            self.g_data.TraceWarn(str(e))
            try:
                self.errno = e.message[0]['code']
            except Exception as e:
                pass
            return None

    def ShowStatus(self, status_id, cache=True):
        if cache:
            cached = self.g_data.dbmgr.LookupStatus(status_id)
            if not cached is None:
                return cached
        s = self.ApiCall("ShowStatus", status_id, lambda: self.api.GetStatus(status_id))
        if not s is None:
            self.g_data.dbmgr.InsertTweet(s)
            return s
        else:
            self.g_data.dbmgr.InsertUngettable(status_id, self.errno)
            return None

    def ShowUser(self, screen_name):
        return self.ApiCall("ShowUser", screen_name, lambda: self.api.GetUser(screen_name=screen_name))

    def Tweet(self, status, in_reply_to_status=None):
        if (not in_reply_to_status is None) and in_reply_to_status.GetUser().GetScreenName() == self.g_data.myName:
            self.g_data.TraceWarn("Attempt to respond to self is a bad idea, posting general tweet")
            in_reply_to_status = None
            if status[:len(self.g_data.myName)+3] == ("@%s: " % self.g_data.myName):
                status = status[len(self.g_data.myName)+3:]
        if self.g_data.read_only_mode:
            self.g_data.TraceWarn("Tweet in Read-Only-Mode: \"%s\"" % status)
            return None
        irtsi = in_reply_to_status.GetId() if not in_reply_to_status is None else None
        result = self.ApiCall("Tweet", status,
                              lambda: self.api.PostUpdate(status, in_reply_to_status_id=irtsi))
        
        if not result is None:
            if not in_reply_to_status is None:
                assert not self.g_data.dbmgr.LookupStatus(in_reply_to_status.GetId()) is None
            self.g_data.dbmgr.InsertTweet(result.GetId())
        return result

    def GetHomeTimeline(self):
        return self.ApiCall("GetHomeTimeline", "",
                            lambda: self.api.GetHomeTimeline(exclude_replies=True), tp="LOT")
        
    def ShowStatuses(self, screen_name=None, user_id=None, count=200, trim_user=False, max_id=None):
        return self.ApiCall("ShowStatuses",  NotNone(screen_name, user_id),
                            lambda:  self.api.GetUserTimeline(screen_name=screen_name,
                                                              user_id=user_id,
                                                              count=count,
                                                              include_rts=False,
                                                              trim_user=trim_user,
                                                              exclude_replies=False,
                                                              max_id = max_id),
                            tp="LOT")

    def GetFollowerIDs(self, screen_name=None, user_id=None):
         return self.ApiCall("GetFollowerIDs", NotNone(screen_name, user_id),
                             lambda: self.api.GetFollowerIDs(screen_name=screen_name,user_id=user_id,cursor=-1,count=5000))

    def GetFollowerIDsPaged(self, screen_name=None, user_id=None, cursor=-1):
         return self.ApiCall("GetFollowerIDsPaged", (NotNone(screen_name, user_id),cursor),
                             lambda: self.GetFollowerIDsPagedInternal(user_id,screen_name,cursor))

    def GetFollowers(self, user_id=None, screen_name=None):
        def GFP(scn,uid):
            next,prev,data = self.api.GetFollowersPaged(screen_name=scn,user_id=uid,cursor=-1)
            return [twitter.User.NewFromJsonDict(x) for x in data['users']]

        return self.ApiCall("GetFollowers", NotNone(screen_name, user_id), 
                             lambda: GFP(screen_name, user_id))

    def RecentTweets(self, max_id, count=5):
        return self.ApiCall("RecentTweets","",
                            lambda: self.api.GetSearch(term="to:%s" % self.g_data.myName,
                                                  count=count,
                                                  result_type="recent",
                                                  include_entities=True,
                                                  since_id=max_id),
                            tp="LOT")

    def Search(self, term, count=100, result_type="recent"):
        return self.ApiCall("Search",term,lambda : self.api.GetSearch(term=term,count=count), tp="LOT")
    
    def Follow(self, screen_name=None, user_id=None):
        if self.g_data.read_only_mode:
            self.g_data.TraceWarn("Follow in Read-Only-Mode: \"@%s\"" % screen_name)
            return None
        return self.ApiCall("Follow",NotNone(user_id,screen_name),lambda: self.api.CreateFriendship(screen_name=screen_name,user_id=user_id))

    def UnFollow(self, screen_name=None, user_id=None):
        if self.g_data.read_only_mode:
            self.g_data.TraceWarn("UnFollow in Read-Only-Mode: \"@%s\"" % screen_name)
            return None
        return self.ApiCall("UnFollow",NotNone(user_id,screen_name),lambda: self.api.DestroyFriendship(screen_name=screen_name,user_id=user_id))


    def GetFollowerIDsPagedInternal(self, user_id, screen_name, cursor):
        url = '%s/followers/ids.json' % self.api.base_url
        parameters = {}
        if user_id is not None:
            parameters['user_id'] = user_id
        if screen_name is not None:
            parameters['screen_name'] = screen_name
        parameters['count'] = 5000
        parameters['cursor'] = cursor
        json = self.api._RequestUrl(url, 'GET', data=parameters)
        data = self.api._ParseAndCheckTwitter(json.content)
        result = [x for x in data['ids']]
        if 'next_cursor' not in data or data['next_cursor'] == 0 or data['next_cursor'] == data['previous_cursor']:
            next_cursor = 0
        else:
            next_cursor = data['next_cursor']
        sec = self.api.GetSleepTime('/followers/ids')
        return result, next_cursor

