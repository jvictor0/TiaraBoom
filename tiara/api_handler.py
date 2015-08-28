import twitter
import os
import data_gatherer as d
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
                insert_user = True
                self.g_data.dbmgr.Begin()
                for t in result:
                    self.g_data.dbmgr.InsertTweet(t, single_xact=False, insert_user=insert_user)
                    insert_user=False
                self.g_data.dbmgr.Commit()
            if tp == "LOU":
                for u in result:
                    self.g_data.dbmgr.InsertUser(u)
            return result
        except twitter.TwitterError as e:
            self.g_data.TraceWarn("%s(%s) failure" % (name,args))
            self.g_data.TraceWarn(str(e))
            try:
                self.errno = e.message[0]['code']
            except Exception as e:
                pass
            return None

    def ShowStatus(self, status_id, user_id=None, cache=True):
        if user_id is None:
            assert not cache
        if cache:
            cached = self.g_data.dbmgr.LookupStatus(status_id, user_id)
            if not cached is None:
                self.g_data.TraceDebug("Cache hit!")
                return cached
        s = self.ApiCall("ShowStatus", status_id, lambda: self.ShowStatusInternal(status_id))
        if not s is None:
            self.g_data.dbmgr.InsertTweet(s)
            return s
        else:
            self.g_data.dbmgr.InsertUngettable(status_id, self.errno)
            return None

    def ShowUser(self, screen_name=None, user_id = None, cache=True):
        if cache and not user_id is None:
            cached = self.g_data.dbmgr.LookupUser(user_id, 1)
            if not cached is None:
                self.g_data.TraceDebug("Cache hit!")
                return cached
        u = self.ApiCall("ShowUser", NotNone(screen_name, user_id), lambda: self.ShowUserInternal(user_id=user_id, screen_name=screen_name))
        if not u is None:
            self.g_data.dbmgr.InsertUser(u)
            return u
        elif not self.errno in [130, 131]: # over capacity, internal error
            affliction = LKD({ 63  : d.AFFLICT_SUSPENDED,
                               34  : d.AFFLICT_DEACTIVATED},
                             self.errno, None)
            if not affliction is None and not user_id is None:
                self.g_data.dbmgr.InsertAfflicted(user_id, affliction)
            elif affliction is None:
                self.g_data.TraceWarn("Unrecognized affliction!")
            return None 
        else:
            return None

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
                assert not self.g_data.dbmgr.LookupStatus(in_reply_to_status.GetId(), in_reply_to_status.GetUser().GetId()) is None, (in_reply_to_status.AsDict(),in_reply_to_status.GetId())
            result.GetUser().following = False #not following myself!
            self.g_data.dbmgr.InsertTweet(result)
        return result

    def ShowStatuses(self, screen_name=None, user_id=None, count=200, trim_user=False, max_id=None):
        return self.ApiCall("ShowStatuses",  NotNone(screen_name, user_id),
                            lambda:  self.GetUserTimelineInternal(screen_name = screen_name,
                                                                  user_id = user_id,
                                                                  count = count,
                                                                  max_id = max_id),
                            tp="LOT")

    def GetFollowerIDs(self, screen_name=None, user_id=None):
         return self.ApiCall("GetFollowerIDs", NotNone(screen_name, user_id),
                             lambda: self.api.GetFollowerIDs(screen_name=screen_name,user_id=user_id,cursor=-1,count=5000))

    def GetFriendIDs(self, screen_name=None, user_id=None):
         return self.ApiCall("GetFollowerIDs", NotNone(screen_name, user_id),
                             lambda: self.api.GetFriendIDs(screen_name=screen_name,user_id=user_id,cursor=-1,count=5000))

    def GetFollowerIDsPaged(self, screen_name=None, user_id=None, cursor=-1):
         return self.ApiCall("GetFollowerIDsPaged", (NotNone(screen_name, user_id),cursor),
                             lambda: self.GetFollowerIDsPagedInternal(user_id,screen_name,cursor))

    def GetFollowers(self, user_id=None, screen_name=None, count=200):
        return self.ApiCall("GetFollowers", NotNone(screen_name, user_id), 
                            lambda: self.GetRelatedInternal("followers",
                                                            user_id = user_id,
                                                            screen_name = screen_name, 
                                                            count = count),
                            tp="LOU")

    def GetFriends(self, user_id=None, screen_name=None, count = 200):
        return self.ApiCall("GetFriends", NotNone(screen_name, user_id), 
                            lambda: self.GetRelatedInternal("friends",
                                                            user_id = user_id,
                                                            screen_name = screen_name, 
                                                            count = count),
                            tp="LOU")

    def RecentTweets(self, max_id, count=5):
        return self.ApiCall("RecentTweets","",
                            lambda: self.GetSearchInternal(term="to:%s" % self.g_data.myName,
                                                           count=count,
                                                           result_type="recent",
                                                           since_id=max_id),
                            tp="LOT")

    def Search(self, term, count=100, result_type="recent"):
        return self.ApiCall("Search",term,lambda : self.GetSearchInternal(term=term,count=count), tp="LOT")

    def GetRetweets(self, tweet_id):
        return self.ApiCall("GetRetweets",tweet_id,lambda : self.GetRetweetsInternal(tweet_id), tp="LOT")
    
    def Follow(self, screen_name=None, user_id=None):
        if self.g_data.read_only_mode:
            self.g_data.TraceWarn("Follow in Read-Only-Mode: \"@%s\"" % screen_name)
            return None
        u = self.ApiCall("Follow",NotNone(user_id,screen_name),lambda: self.api.CreateFriendship(screen_name=screen_name,user_id=user_id))
        if not u is None:
            u.following = True
            self.g_data.dbmgr.InsertUser(u)
            return u
        return None

    def UnFollow(self, screen_name=None, user_id=None):
        if self.g_data.read_only_mode:
            self.g_data.TraceWarn("UnFollow in Read-Only-Mode: \"@%s\"" % screen_name)
            return None
        u = self.ApiCall("UnFollow",NotNone(user_id,screen_name),lambda: self.api.DestroyFriendship(screen_name=screen_name,user_id=user_id))
        if not u is None:
            u.following = False
            self.g_data.dbmgr.InsertUser(u)
            return u
        return None

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

    def ApiCallInternal(self, url, data, request="GET"):
        url = "%s/%s" % (self.api.base_url, url)
        json_data = self.api._RequestUrl(url, request, data=data)
        self.g_data.TraceDebug("rate limit remaining = %s" % json_data.headers["x-rate-limit-remaining"])
        self.last_call_rate_limit_remaining =  int(json_data.headers["x-rate-limit-remaining"])
        assert int(json_data.headers["x-rate-limit-remaining"]) > 0, "lets just not cause ourselves problems"
        data = self.api._ParseAndCheckTwitter(json_data.content)
        return data
        
    def ShowUserInternal(self, user_id, screen_name):
        if user_id:
            param = str(user_id)
        else:
            param = screen_name
        data = self.ApiCallInternal("users/show/%s.json" % param, {})
        return self.UserFromJson(data) 

    def GetRelatedInternal(self, relation, user_id, screen_name, count):
        parameters = {"count":count, "include_user_entities":True}
        if user_id:
            parameters["user_id"] = user_id
        else:
            parameters["screen_name"] = screen_name
        data = self.ApiCallInternal("%s/list.json" % relation,parameters)
        return [self.UserFromJson(u) for u in data["users"]]

    def GetSearchInternal(self,term,count,result_type="mixed",since_id=None):
        args = {"q" : term, "count" : count, "result_type" : result_type, "include_entities" : True}
        if not since_id is None:
            args["since_id"] = since_id
        data = self.ApiCallInternal("search/tweets.json",args)
        return [self.StatusFromJson(s) for s in data["statuses"]]

    def ShowStatusInternal(self, status_id):
        s = self.ApiCallInternal("statuses/show/%s.json" % status_id, {})
        return self.StatusFromJson(s)

    def GetUserTimelineInternal(self, screen_name,user_id,count,max_id):
        parameters = {"trim_user" : False, "count" : count}
        if user_id:
            parameters['user_id'] = user_id
        if screen_name:
            parameters['screen_name'] = screen_name
        if max_id:
            parameters['max_id'] = long(max_id)
        data = self.ApiCallInternal("statuses/user_timeline.json",parameters)
        return [self.StatusFromJson(s) for s in data]

    def GetRetweetsInternal(self, tweet_id):
        parameters = {"trim_user" : False}
        data = self.ApiCallInternal("statuses/retweets/%d.json" % tweet_id, parameters)
        return [self.StatusFromJson(s) for s in data]

    def UserFromJson(self, json):
        u = twitter.user.User.NewFromJsonDict(json)
        if "following" in json:
            u.following = json["following"]
        return u

    def StatusFromJson(self, json):
        s = twitter.status.Status.NewFromJsonDict(json)
        if "user" in json:
            s.SetUser(self.UserFromJson(json["user"]))
        if "retweeted_status" in json:
            s.SetRetweeted_status(self.StatusFromJson(json["retweeted_status"]))
        return s
