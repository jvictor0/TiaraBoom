import database as db
import persisted as p
import ticker as t
import random
import json
from twitter.status import Status
from twitter.user import User
import datetime
from util import *
import corenlp

MODES=3

AFFLICT_FOLLOWBACK = 1
AFFLICT_DELETER = 2
AFFLICT_PROTECTED = 3
AFFLICT_SUSPENDED = 4
AFFLICT_BLOCKER = 5
AFFLICT_DEACTIVATED = 6

class DataManager:
    def __init__(self, g_data, config):
        self.con = None
        self.nlp = None
        self.InitCoreNLP()
        self.tweets_to_process = p.PersistedSet('tweets_to_process')
        self.g_data = g_data
        self.shard = 0
        if 'database' in config:
            self.con = db.ConnectToMySQL()
            self.con.query("create database if not exists %s" % config["database"])
            self.con.query("use %s" % config["database"])
            self.con.query('set names "utf8mb4" collate "utf8mb4_bin"')
            if "gatherer_authentication" in config:
                self.apiHandler = api_handler.ApiHandler(config["gatherer_authentication"])
            else:
                self.apiHandler = g_data.ApiHandler()
            self.DDL()
 
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
                        "following tinyint,"
                        "has_followed tinyint,"
                        "updated timestamp default current_timestamp on update current_timestamp)"))

        self.con.query(("create table if not exists depends("
                        "id bigint,"
                        "type varchar(50) character set utf8mb4 default null,"
                        "arg1 varchar(512) character set utf8mb4 default null,"
                        "arg2 varchar(512) character set utf8mb4 default null,"
                        "key(arg1),key(arg2), key(id))"))
                        
                        
                
    def UpdateTweets(self):
        if self.con is None:
            return
        max_id = None
        count = 0
        while True:
            count += 1
            assert count <= 30
            statuses = self.apiHandler.ShowStatuses(screen_name=self.g_data.myName,
                                                    max_id=max_id)
            if statuses is None:
                self.g_data.TraceWarn("Failed to update tweets")
                return None
            if len(statuses) == 0:
                break
            max_id = min([s.GetId() for s in statuses]) - 1
                       
            for s in statuses:
                assert not self.LookupStatus(s.GetId()) is None

    def RemoveProcessedTweets(self):
        for tid in list(self.tweets_to_process.Get()):
            if (len(self.Lookup(tid,"parent")) != 0) or (len(self.Lookup(tid)) != 0):
                print "deleting %d" % tid
                self.tweets_to_process.Delete(tid)
            else:
                print "keeping %d" % tid

    def ProcessUnprocessedTweets(self):
        if self.con is None:
            return
        count = 85
        while len(self.tweets_to_process) > 0 and count > 0:
            tid = self.tweets_to_process.Random()
            count -= 1
            if not self.InsertTweetById(tid) is None:
                self.tweets_to_process.Delete(tid)
                
        if count == 0:
            return
        tweets = self.GetUnprocessed()
        self.g_data.TraceInfo("There are currently %d unprocessed tweets" % len(tweets))
        for i in xrange(count):
            if len(tweets) == 0:
                return
            self.InsertTweetById(long(random.choice(tweets)["parent"]))
            
    def InsertTweetById(self, tid):
        s = self.apiHandler.ShowStatus(tid, cache=False)
        if not s is None:
            self.InsertTweet(s)
            return True
        else:
            if self.apiHandler.errno in [34,179,63,144]: # not found, not allowed, suspended, not existing
                self.InsertUngettable(tid, self.apiHandler.errno)
                return True
            self.g_data.TraceWarn("Unhandled error in InsertTweetById %d" % self.apiHandler.errno)
            assert False
            return None
        
    def InsertUser(self, user):
        uid = str(user.GetId())
        sn  = "'%s'" % user.GetScreenName().encode("utf8")
        folls = str(user.GetFollowersCount())
        friens = str(user.GetFriendsCount())
        following = "1" if user.following else "0"
        has_followed = following
        values = ",".join([uid, sn, folls, friens, following, has_followed, "NOW()"])
        updates = ["num_followers = %s" % folls,
                   "num_friends = %s" % friens,
                   "screen_name = %s" % sn,
                   "following = %s" % following]
        if user.following:
            updates.append("has_followed = 1")
        q = "insert into users values (%s) on duplicate key update %s" % (values, ",".join(updates))
        self.con.query(q)
        
    def InsertUngettable(self, tid, errno):
        if self.con is None:
            return
        self.con.query("insert into ungettable_tweets values (%d,%d) on duplicate key update errorcode=errorcode" % (tid,errno))

    def InsertAfflicted(self, uid, errno):
        if self.con is None:
            return
        self.con.query("insert into user_afflictions values (%d,%d) on duplicate key update affliction=affliction" % (uid,errno))
        if errno in [AFFLICT_DEACTIVATED, AFFLICT_SUSPENDED]:
            self.con.query("delete from users where id = %d and num_followers is null" % uid)

    def GetAffliction(self, uid):
        if self.con is None:
            return None
        rows = self.con.query("select * from users where id = %d and has_followed = 1 and following = 0" % uid)
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
        s = Status.NewFromJsonDict(json.loads(row["json"]))
        s.SetRetweetCount(int(row["retweets"]))
        s.SetFavoriteCount(int(row["favorites"]))
        if s.urls is None:
            s.urls = []
        assert s.GetUser() is None, row
        u = self.LookupUser(int(row["user_id"]))
        if u is None:
            s.SetUser(User())
            s.GetUser().SetScreenName(row['user_name'])
            s.GetUser().SetId(long(row['user_id']))
        else:
            s.SetUser(u)
        return s

    def LookupStatuses(self, tid, field = "id"):
        rows = self.Lookup(tid,field)
        return [self.RowToStatus(r) for r in rows if not r["json"] is None]

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
        user = User()
        user.SetScreenName(row[0]["screen_name"])
        user.SetId(uid)
        user.SetFollowersCount(row[0]["num_followers"])
        user.SetFriendsCount(row[0]["num_friends"])
        user.following = True if row[0]["following"] == "1" else False
        return user

    def EverFollowed(self, uid):
        res = self.con.query("select has_followed from users where id = %d" % uid)
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
 
    def UpdateUsers(self):
        q = "select id from users order by updated limit 30"
        result = self.con.query(q)
        for r in result:
            self.apiHandler.ShowUser(user_id=int(r["id"]), cache=False)

    def InitCoreNLP(self):
        if not self.nlp:
            self.nlp = corenlp.StanfordNLP()
        
    def InsertDependencies(self, tid, body):
        deps = self.nlp.parse(body)
        for s in deps["sentences"]:
            for a,b,c in s["dependencies"]:
                self.con.query("insert into depends values(%d,'%s',%%s,%%s)" % (tid, a.encode("utf8")), b.encode("utf8"), c.encode("utf8"))
    
    def TrollDependencies(self):
        maxid = self.con.query("select max(id) as a from depends")[0]['a']
        rows = self.con.query("select id, body from tweets where id > %s order by id limit 100" % maxid)
        for r in rows:
            print r["body"]
            try:
                self.InsertDependencies(int(r["id"]), r["body"])
            except Exception as e:
                print r["id"]
                print e
    
    def TrollAllDependencies(self):
        while True:
            self.TrollDependencies()

    def Act(self):
        if self.shard % MODES == 0:
            self.UpdateTweets()
        elif self.shard % MODES == 1:
            self.ProcessUnprocessedTweets()
        elif self.shard % MODES == 2:
            self.UpdateUsers()
        self.shard += 1