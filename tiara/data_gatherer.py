import database as db
import persisted as p
import ticker as t
import vocab as v

import random
import json
import datetime

from twitter.status import Status
from twitter.user import User

from util import *

MODES=3

AFFLICT_FOLLOWBACK = 1
AFFLICT_DELETER = 2
AFFLICT_PROTECTED = 3
AFFLICT_SUSPENDED = 4
AFFLICT_BLOCKER = 5
AFFLICT_DEACTIVATED = 6
AFFLICT_NON_ENGLISH = 7

class FakeGData:
    def __init__(self, name):
        self.myName = name

    def TraceWarn(self,a):
        print a

    def TraceInfo(self,a):
        print a

    def ApiHandler(self,):
        assert False, "Dont twitter ops with FakeGData"

def MakeFakeDataMgr(name, dbname):
    return DataManager(FakeGData(name), { "database" : dbname}, no_ddl = True)

class DataManager:
    def __init__(self, g_data, config, no_ddl=False):
        self.con = None
        self.g_data = g_data
        self.shard = 0
        if 'database' in config:
            self.con = db.ConnectToMySQL()
            self.con.query("create database if not exists %s" % config["database"])
            self.con.query("use %s" % config["database"])
            self.con.query('set names "utf8mb4" collate "utf8mb4_bin"')
            if no_ddl:
                return
            if "gatherer_authentication" in config:
                self.apiHandler = api_handler.ApiHandler(config["gatherer_authentication"])
            else:
                self.apiHandler = g_data.ApiHandler()
            self.DDL()
            
    def ApiHandler(self):
        return self.apiHandler
        
    def DDL(self):
        self.con.query(("create table if not exists tweets("
                        
                        "id bigint primary key not null,"
                        "parent bigint default null,"
                        
                        "user_name varchar(200) character set utf8mb4 not null ,"
                        "user_id bigint not null,"
                        
                        "parent_name varchar(200) character set utf8mb4 default null,"
                        "parent_id bigint default null,"
                        
                        "body text character set utf8mb4 not null,"
                        
                        "retweets bigint not null,"
                        "favorites bigint not null,"
                        
                        "ts datetime not null,"

                        "json text character set utf8mb4 default null,"
                        
                        "index(user_id),"
                        "index(parent),"
                        "index(parent_id))"
                        "default charset = utf8mb4"))
        
        self.con.query(("create table if not exists ungettable_tweets("
                        "id bigint primary key,"
                        "errorcode int)"))
        
        self.con.query(("create table if not exists user_afflictions("
                        "id bigint,"
                        "affliction int,"
                        "primary key(id, affliction))"))
        
        self.con.query(("create table if not exists users("
                        "id bigint primary key,"
                        "screen_name varchar(200) character set utf8mb4 default null,"
                        "num_followers bigint,"
                        "num_friends bigint,"
                        "language varchar(200) default null,"
                        "updated timestamp default current_timestamp on update current_timestamp,"
                        "key (screen_name))"))
        self.con.query(("create table if not exists user_following_status("
                        "id bigint,"
                        "my_name varchar(100) character set utf8mb4 default null,"
                        "following tinyint,"
                        "has_followed tinyint,"
                        "updated timestamp default current_timestamp on update current_timestamp,"
                        "primary key(id, my_name))"))
        self.con.query(("create table if not exists tweet_tokens("
                        "user_id bigint,"
                        "tweet_id bigint,"
                        "key (user_id, tweet_id),"
                        "token varchar(100) character set utf8mb4 default null,"
                        "primary key(token, user_id, tweet_id))"))
                        

                
    def UpdateTweets(self):
        if self.con is None:
            return
        max_id = None
        count = 0
        while True:
            count += 1
            assert count <= 30
            statuses = self.ApiHandler().ShowStatuses(screen_name=self.g_data.myName,
                                                    max_id=max_id)
            if statuses is None:
                self.g_data.TraceWarn("Failed to update tweets")
                return None
            if len(statuses) == 0:
                break
            max_id = min([s.GetId() for s in statuses]) - 1
                       
            for s in statuses:
                assert not self.LookupStatus(s.GetId()) is None

    def ProcessUnprocessedTweets(self):
        if self.con is None:
            return
        count = 30
        if count == 0:
            return
        tweets = self.GetUnprocessed()
        self.g_data.TraceInfo("There are currently %d unprocessed tweets" % len(tweets))
        for i in xrange(count):
            if len(tweets) == 0:
                return
            self.InsertTweetById(long(random.choice(tweets)["parent"]))
            
    def InsertTweetById(self, tid):
        s = self.ApiHandler().ShowStatus(tid, cache=False)
        if not s is None:
            self.InsertTweet(s)
            return True
        else:
            if self.ApiHandler().errno in [34,179,63,144]: # not found, not allowed, suspended, not existing
                self.InsertUngettable(tid, self.ApiHandler().errno)
                return True
            self.g_data.TraceWarn("Unhandled error in InsertTweetById %d" % self.ApiHandler().errno)
            assert False
            return None
        
    def InsertUser(self, user):
        uid = str(user.GetId())
        sn  = "'%s'" % user.GetScreenName().encode("utf8")
        folls = str(user.GetFollowersCount())
        friens = str(user.GetFriendsCount())
        language = "'%s'" % user.GetLang()
        values = ",".join([uid, sn, folls, friens, language, "NOW()"])
        updates = ["num_followers = %s" % folls,
                   "num_friends = %s" % friens,
                   "screen_name = %s" % sn,
                   "language = %s" % language]
        q = "insert into users values (%s) on duplicate key update %s" % (values, ",".join(updates))
        self.con.query(q)

        following = "1" if user.following else "0"
        has_followed = following

        updates = ["following = %s" % following]
        if following == "1":
            updates.append("has_followed = 1")
        
        q = ("insert into user_following_status values (%s,'%s',%s,%s,NOW()) "
             "on duplicate key update %s")
        q = q % (uid, self.g_data.myName, following, has_followed, ",".join(updates))
        self.con.query(q)
        
    def InsertUngettable(self, tid, errno):
        if self.con is None:
            return
        self.con.query("insert into ungettable_tweets values (%d,%d) on duplicate key update errorcode=errorcode" % (tid,errno))

    def InsertAfflicted(self, uid, errno):
        if self.con is None:
            return
        self.con.query("insert into user_afflictions values (%d,%d) on duplicate key update affliction=affliction" % (uid,errno))

    def GetAffliction(self, uid):
        if self.con is None:
            return None
        rows = self.con.query(("select * from user_following_status "
                               "where my_name = '%s' and id = %d and has_followed = 1 and following = 0")
                              % (self.g_data.myName, uid))
        if len(rows) == 1:
            self.InsertAfflicted(uid, AFFLICT_BLOCKER)
        elif self.EverFollowed(uid):
            self.con.query("delete from user_afflictions where id = %d and affliction = %d" % (uid, AFFLICT_BLOCKER))
        return [r["affliction"] for r in self.con.query("select * from user_afflictions where id = %d" % uid)]

    def InsertTweet(self, s):
        if self.con is None:
            return
        parent = "null"
        parent_name = "null"
        parent_id  = "null"
        if not s.GetInReplyToStatusId() is None:
            parent = str(s.GetInReplyToStatusId())
            if not s.GetInReplyToUserId() is None:
                parent_name = "'%s'" % s.GetInReplyToScreenName()
                parent_id = str(s.GetInReplyToUserId())
        sid = str(s.GetId())
        name = "'%s'" % s.GetUser().GetScreenName()
        uid = str(s.GetUser().GetId())
        body = s.GetText()
        timestamp = "'%s'" % TwitterTimestampToMySQL(s.GetCreatedAt())
        likes = str(s.GetFavoriteCount())
        retweets = str(s.GetRetweetCount())
        values = [sid, parent, name.encode("utf8"), uid,
                  parent_name.encode("utf8"), parent_id,
                  "%s",
                  retweets, likes,
                  timestamp.encode("utf8"),
                  "%s"]
        values = " , ".join(values)
        query = "insert into tweets values (%s) on duplicate key update favorites = %s, retweets = %s" % (values, likes, retweets)
        jsdict = s.AsDict()
        if "user" in jsdict:
            del jsdict["user"]
        self.con.query(query, body.encode("utf8"), json.dumps(jsdict).encode("utf8"))
        assert len(self.con.query("show warnings")) == 0, self.con.query("show warnings")
        self.InsertUser(s.GetUser())
        self.InsertTweetTokens(s.GetUser().GetId(), s.GetId(), s.GetText())

    def GetUnprocessed(self, user=None):
        query = ("select tl.id, tl.parent, tl.parent_name, tl.parent_id "
                 "from tweets tl left join tweets tr "
                 "on tr.id = tl.parent "
                 "where tr.id is null and tl.parent is not null and (tl.user_name = '%s' or tl.parent_name = '%s') " 
                 "and not exists(select * from ungettable_tweets where id = tl.parent) "
                 "limit 90")
        query = query % (self.g_data.myName,self.g_data.myName)
        if not user is None:
            query = query + " and tl.parent_id = %d" % user
        return self.con.query(query)

    def Lookup(self, tid, field = "id"):
        if self.con is None:
            return []
        res = self.con.query("select * from tweets where %s = %d" % (field,tid))
        return res

    def RowToStatus(self, row):
        if row["json"] is None:
            return None
        s = Status.NewFromJsonDict(json.loads(row["json"]))
        s.SetRetweetCount(int(row["retweets"]))
        s.SetFavoriteCount(int(row["favorites"]))
        if s.urls is None:
            s.urls = []
        assert s.GetUser() is None, row
        u = self.LookupUser(int(row["user_id"]))
        if u is None:            
            return None
        else:
            s.SetUser(u)
        return s

    def LookupStatuses(self, tid, field = "id"):
        rows = self.Lookup(tid,field)
        return filter(lambda x: not x is None,
                      [self.RowToStatus(r) for r in rows])

    def LookupStatus(self, tid, field = "id"):
        statuses = self.LookupStatuses(tid, field)
        if len(statuses) == 0:
            return None
        return statuses[0]

    def LookupUser(self, uid, days_old = None):
        q = "select * from users where id = %d" % uid
        if not days_old is None:
            q = q + " and updated > timestampadd(day, -%d, now())" % days_old
        row = self.con.query(q)
        if len(row) == 0:
            return None
        assert len(row) == 1
        if row[0]["num_followers"] is None:
            return None
        if row[0]["language"] is None:
            return None
        user = User()
        user.SetScreenName(row[0]["screen_name"])
        user.SetId(uid)
        user.SetFollowersCount(int(row[0]["num_followers"]))
        user.SetFriendsCount(int(row[0]["num_friends"]))
        user.SetLang(row[0]["language"])
        q = "select * from user_following_status where my_name = '%s' and id = %d" % (self.g_data.myName,uid)
        if not days_old is None:
            q = q + " and updated > timestampadd(day, -%d, now())" % days_old
        row = self.con.query(q)
        if len(row) == 0:
            return None
        user.following = True if row[0]["following"] == "1" else False
        return user

    def EverFollowed(self, uid):
        res = self.con.query("select has_followed from user_following_status where my_name = '%s' and id = %d" % (self.g_data.myName,uid))
        if len(res) == 0:
            return False
        return res[0]["has_followed"] == "1"
           
    def MostRecentTweet(self, uid):
        q = "select max(ts) as a from tweets where parent_id = %d and user_name = '%s'" % (uid, self.g_data.myName)
        result = self.con.query(q)
        if result[0]["a"] is None:
            return None
        assert len(result) == 1
        return MySQLTimestampToPython(result[0]["a"])

    def TweetHistory(self, uid):
        q = ("select ch.id as chid, pa.id as paid from tweets ch join tweets pa "
             "on ch.parent = pa.id "
             "where (ch.user_id = %d and pa.user_name = '%s') "
             " or (ch.parent_id = %d and ch.user_name = '%s')")
        q = q % (uid, self.g_data.myName, uid, self.g_data.myName)
        rows = self.con.query(q)
        result = []
        for r in rows:
            left = self.LookupStatus(int(r["chid"]))
            right = self.LookupStatus(int(r["paid"]))
            result.append((left,right))
        return result

    def EntireConversation(self, tweet, considered = set([])):
        result = []
        while not tweet is None:
            if tweet.GetId() in considered:
                break
            result.append(tweet)
            considered.add(tweet.GetId())
            q = "select * from tweets where parent = %d" % tweet.GetId()
            statuses = [self.RowToStatus(s) for s in self.con.query(q)]
            for s in statuses:
                result.extend(self.EntireConversation(s, considered))
            if not tweet.GetInReplyToStatusId() is None:
                tweet = self.LookupStatus(tweet.GetInReplyToStatusId())
            else:
                break
        return result

    def RecentConversations(self, limit):
        user_id = self.con.query("select id from users where screen_name = '%s'" % self.g_data.myName)[0]["id"]
        q = "select * from tweets where parent_id = '%s' order by id desc limit %d" % (user_id, limit)
        statuses = [self.RowToStatus(s) for s in self.con.query(q)]
        considered = set([])
        result = []
        for s in statuses:
            nx = self.EntireConversation(s, considered)
            if len(nx) != 0:
                result.append(nx)
        return result               
            
    def UpdateUsers(self):
        q = "select id from users order by updated limit 30"
        result = self.con.query(q)
        for r in result:
            self.ApiHandler().ShowUser(user_id=int(r["id"]), cache=False)

    def TFIDF(self, uid=None, tid=None, tweet=None, user=None):
        if not tweet is None:
            assert uid is None
            assert tid is None
            assert user is None
            uid = tweet.GetUser().GetId()
            tid = tweet.GetId()
        if not user is None:
            assert uid is None
            assert tid is None
            assert tweet is None
            uid = user.GetId()
        dfQuery = ("select token, count(distinct %s) as df "
                   "from tweet_tokens "
                   "group by token")
        dfQuery = dfQuery % ("user_id" if tid is None else "user_id, tweet_id")
        tfQuery = ("select token, count(*) as tf "
                   "from tweet_tokens "
                   "where user_id = %d %s "
                   "group by token")
        tfQuery = tfQuery % (uid, ("and tweet_id = %d" % tid) if not tid is None else "")
        numDocsQuery = "select count(distinct %s) from tweet_tokens" % ("user_id" if tid is None else "user_id, tweet_id")
        q = ("select termfreq.token, termfreq.tf as tf, docfreq.df as df, "
             "(1+log(tf)) * log((%s)/df) as tfidf "
             "from (%s) termfreq join (%s) docfreq "
             "on termfreq.token = docfreq.token")
        q = q % (numDocsQuery, tfQuery, dfQuery)
        rows = self.con.query(q)
        return [(r["token"], float(r["tfidf"])) for r in rows]

    def InsertTweetTokens(self, uid, tid, tweet):
        tokens = v.Vocab(self.g_data).Tokenize(tweet)
        q = "insert into tweet_tokens (user_id, tweet_id, token) values (%d,%d,%%s)" % (uid, tid)
        for t in tokens:
            try:                
                self.con.query(q,t.encode("utf8"))
            except Exception as e:
                assert e[0] == 1062 #dup key
                return

    def InsertAllTweetTokens(self):
        self.con.query("delete from tweet_tokens") # because fuck you thats why!
        tweets = self.con.query("select user_id, id, body from tweets")
        for i,r in enumerate(tweets): # am i insane or genious?
            if i % 100 == 0:
                print float(i)/len(tweets)
            print "   ", r["id"]
            self.InsertTweetTokens(int(r["user_id"]),int(r["id"]),r["body"])

    def Act(self):
        if self.shard % MODES == 0:
            self.UpdateTweets()
        elif self.shard % MODES == 1:
            self.ProcessUnprocessedTweets()
        elif self.shard % MODES == 2:
            self.UpdateUsers()
        self.shard += 1
