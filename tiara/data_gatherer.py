import database as db
import persisted as p
import ticker as t
import vocab as v

import random
import time
import json
import datetime
import os
import math

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
        self.logger = logging.getLogger('TiaraBoom')

    def TraceWarn(self,a):
        self.logger.warn("(FakeGData) %s" % a)

    def TraceInfo(self,a):
        self.logger.info("(FakeGData) %s" % a)

    def ApiHandler(self):
        assert False, "Dont twitter ops with FakeGData"

def MakeFakeDataMgr(name = ""):
    abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
    with open(abs_prefix + '/config.json','r') as f:
        confs = json.load(f)["bots"][0]
        dbname = confs["database"]
        dbhost = confs["dbhost"]
    return DataManager(FakeGData(name), { "database" : dbname, "dbhost" : dbhost}, no_ddl = True)

class DataManager:
    def __init__(self, g_data, config, no_ddl=False):
        self.con = None
        self.g_data = g_data
        self.shard = 0
        self.con = db.ConnectToMySQL(host=config["dbhost"])
        self.con.query("create database if not exists tiaraboom")
        self.con.query("use tiaraboom")
        self.con.query('set names "utf8mb4" collate "utf8mb4_bin"')
        if no_ddl:
            return
        if "gatherer_authentication" in config:
            self.apiHandler = api_handler.ApiHandler(config["gatherer_authentication"])
        else:
            self.apiHandler = g_data.ApiHandler()
        self.DDL()
        self.user_id = None
        self.cache = {}

    def TimedQuery(self, q, name, *largs):
        t0 = time.time()
        self.g_data.TraceInfo("Starting %s with con %s" % (name, self.con))
        result = self.con.query(q, *largs)
        self.g_data.TraceInfo("%s took %f secs" % (name, time.time() - t0))
        return result
            
    def ApiHandler(self):
        return self.apiHandler
        
    def DDL(self):
        self.con.query(("create table if not exists tweets("
                        
                        "id bigint primary key not null,"
                        "parent bigint default null,"
                        
                        "user_name varbinary(200),"
                        "user_id bigint not null,"
                        
                        "parent_name varbinary(200),"
                        "parent_id bigint default null,"
                        
                        "body blob, "
                        
                        "retweets bigint not null,"
                        "favorites bigint not null,"
                        
                        "ts datetime not null,"

                        "json /*!90619 json */ /*50509 blob */ ,"
                        
                        "index(user_id),"
                        "index(parent),"
                        "index(parent_id))"))
        self.con.query(("create table if not exists ungettable_tweets("
                        "id bigint primary key,"
                        "errorcode int)"))
        
        self.con.query(("create table if not exists user_afflictions("
                        "id bigint,"
                        "affliction int,"
                        "primary key(id, affliction))"))
        
        self.con.query(("create table if not exists users("
                        "id bigint primary key,"
                        "screen_name varbinary(200),"
                        "num_followers bigint,"
                        "num_friends bigint,"
                        "language varbinary(200),"
                        "updated timestamp default current_timestamp on update current_timestamp,"
                        "key (screen_name))"))
        self.con.query(("create table if not exists user_following_status("
                        "id bigint,"
                        "my_name varbinary(100),"
                        "following tinyint,"
                        "has_followed tinyint,"
                        "updated timestamp default current_timestamp on update current_timestamp,"
                        "primary key(id, my_name))"))
        self.con.query(("create table if not exists tweet_tokens("
                        "user_id bigint,"
                        "tweet_id bigint,"
                        "key (user_id, tweet_id),"
                        "token bigint,"
                        "key (user_id, token),"
                        "primary key(token, user_id, tweet_id))"))
        self.con.query(("create table if not exists articles("
                        "tweet_id bigint not null,"
                        "inserted datetime not null,"
                        "processed datetime,"
                        "personality varbinary(100) not null,"
                        "url blob not null, "
                        "key(tweet_id, personality),"
                        "key(personality, url /*50509 (3600) */),"
                        "key (inserted))"))
        self.con.query(("create table if not exists feature_id("
                        "id bigint primary key auto_increment,"
                        "feature varbinary(200),"
                        "unique key(feature))"))
        self.con.query(("create table if not exists token_id("
                        "id bigint primary key auto_increment,"
                        "token varbinary(200),"
                        "unique key(feature))"))
        self.con.query(("create table if not exists ignored_users("
                        "id bigint primary key)"))

        self.MakeTFIDFViews()
                
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
                   "language = %s" % language,
                   "updated = NOW()"]
        q = "insert into users values (%s) on duplicate key update %s" % (values, ",".join(updates))
        self.con.query(q)

        following = "1" if user.following else "0"
        has_followed = following

        updates = ["following = %s" % following, "updated = NOW()"]
        if following == "1":
            updates.append("has_followed = 1")
        
        q = ("insert into user_following_status values (%s,'%s',%s,%s,NOW()) "
             "on duplicate key update %s")
        q = q % (uid, self.g_data.myName, following, has_followed, ",".join(updates))
        self.con.query(q)
        if user.GetProtected():
            self.InsertAfflicted(user.GetId(), AFFLICT_PROTECTED)
        
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

    def InsertTweet(self, s, ignore_user=False):
        if s.GetRetweeted_status() is not None:
            self.InsertTweet(s.GetRetweeted_status())
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
        del jsdict["created_at"]
        del jsdict["text"]
        if "retweet_count" in jsdict:
            del jsdict["retweet_count"]
        if "favorite_count" in jsdict:
            del jsdict["favorite_count"]
        del jsdict["favorited"] # our bots dont favorite or retweet, and this is a shared table, so this data doesnt even make sense!
        del jsdict["retweeted"]
        del jsdict["id"]
        if s.GetRetweeted_status() is not None:
            jsdict["retweeted_status"] = s.GetRetweeted_status().GetId()
        self.con.query("begin")
        self.con.query(query, body.encode("utf8"), json.dumps(jsdict).encode("utf8"))
        assert len(self.con.query("show warnings")) == 0, self.con.query("show warnings")
        if not ignore_user:
            self.InsertUser(s.GetUser())
        self.InsertTweetTokens(s.GetUser().GetId(), s.GetId(), s.GetText())
        self.con.query("commit")

    def GetUnprocessed(self, user=None):
        uid = self.GetUserId()
        query = ("select tl.id, tl.parent, tl.parent_name, tl.parent_id "
                 "from tweets tl left join tweets tr "
                 "on tr.id = tl.parent "
                 "where tr.id is null and tl.parent is not null and (tl.user_id = %s or tl.parent_id = %s) " 
                 "and not exists(select * from ungettable_tweets where id = tl.parent) "
                 "limit 90")
        query = query % (uid, uid)
        return self.TimedQuery(query, "GetUnprocessed")

    def Lookup(self, tid, field = "id"):
        if self.con is None:
            return []
        res = self.con.query("select * from tweets where %s = %d" % (field,tid))
        return res

    def RowToStatus(self, row):
        if row["json"] is None:
            return None
        jsdict = json.loads(row["json"])
        jsdict["text"] = row["body"]
        jsdict["id"] = int(row["id"])
        jsdict["created_at"] = MySQLTimestampToTwitter(row["ts"])
        jsdict["favorited"] = False
        jsdict["retweeted"] = False
        if "retweeted_status" in jsdict:
            jsdict["retweeted_status"] = self.LookupStatus(jsdict["retweeted_status"])
            if jsdict["retweeted_status"] is None:
                return None
            else:
                jsdict["retweeted_status"] = jsdict["retweeted_status"].AsDict()
        s = Status.NewFromJsonDict(jsdict)
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
        rows = self.TimedQuery(q, "TweetHistory")
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
        user_id = self.GetUserId()
        q = "select * from tweets where parent_id = '%s' order by id desc limit %d" % (user_id, limit)
        statuses = [self.RowToStatus(s) for s in self.con.query(q)]
        considered = set([])
        result = []
        for s in statuses:
            nx = self.EntireConversation(s, considered)
            if len(nx) != 0:
                result.append(nx)
        return result               

    def GetUserId(self):
        if self.user_id is None:
            self.user_id = int(self.con.query("select id from users where screen_name = '%s'" % self.g_data.myName)[0]["id"])
        return self.user_id
            
    def GetBotIds(self):
        return [g.dbmgr.GetUserId() for g in self.g_data.g_datas]

    def UpdateUsers(self):
        q = ("select id from user_following_status "
             "where has_followed = 1 and my_name = '%s' and "
             "id not in (select id from user_afflictions where affliction in (%d,%d)) "
             "order by updated limit 75")
        q = q % (self.g_data.myName, AFFLICT_SUSPENDED, AFFLICT_DEACTIVATED)
        result = self.TimedQuery(q, "UpdateUsers")
        count = 0
        for r in result:
            self.ApiHandler().ShowUser(user_id=int(r["id"]), cache=False)
            stats = self.ApiHandler().ShowStatuses(user_id=int(r["id"]))
            if stats is not None:
                count += len(stats)
        self.g_data.TraceInfo("Added %d tweets" % count)
        
        

    def NormalizeArgs(self, uid, tid, tweet, user):
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
        return uid, tid, tweet, user

    def TFIDF(self, uid=None, tid=None, tweet=None, user=None):
        uid, tid, tweet, user = self.NormalizeArgs(uid, tid, tweet, user)
        if tid is None:
            q = "select * from tfidf_view where user_id = %d" % uid
        else:
            q = "select * from tfidf_tweet_view where user_id = %d and tweet_id = %d" % (uid,tid)
        rows = self.TimedQuery(q,"TFIDF")
        return [(r["token"], float(r["tfidf"])) for r in rows]

    def TFIDFLegacy(self, uid=None, tid=None, tweet=None, user=None, viewName=None, queryString=False):
        uid, tid, tweet, user = self.NormalizeArgs(uid, tid, tweet, user)
        dfQuery = ("select token, count(distinct %s) as df "
                   "from tweet_tokens "
                   "group by token")
        dfQuery = dfQuery % ("user_id" if tid is None else "user_id, tweet_id")
        tfWhere = "" if uid is None else ("where user_id = %d %s" % (uid, ("and tweet_id = %d" % tid) if not tid is None else ""))
        tfQuery = ("select token, user_id, count(*) as tf "
                   "from tweet_tokens "
                   "%s "
                   "group by token, user_id")
        tfQuery = tfQuery % (tfWhere)
        numDocsQuery = "select count(distinct %s) as val from tweet_tokens" % ("user_id" if tid is None else "user_id, tweet_id")
        q = ("select termfreq.token, termfreq.user_id, termfreq.tf as tf, docfreq.df as df, "
             "(1+log(tf)) * log((%s)/df) as tfidf "
             "from (%s) termfreq join (%s) docfreq "
             "on termfreq.token = docfreq.token")
        q = q % (numDocsQuery, tfQuery, dfQuery)
        if queryString:
            assert viewName is None
            return q
        elif viewName is None:            
            rows = self.TimedQuery(q, "TFIDF")
            return [(self.Id2Feat(int(r["token"]), "token_id"), float(r["tfidf"])) for r in rows]
        else:
            self.con.query("drop view if exists %s" % viewName)
            self.con.query("create view %s as %s" % (viewName, q))

    def MakeTFIDFViews(self):
        for v in ["tfidf_distance_view",
                  "tfidf_norm_view","tfidf_user_norm_view",
                  "tfidf_tweet_view","tfidf_view", 
                  "tfidf_tweet_view_internal","tfidf_view_internal", 
                  "num_docs_view", "num_docs_tweet_view", "tf_view", "df_view","df_tweet_view"]:
            self.con.query("drop view if exists %s" % v)
        self.con.query("create view df_view as "
                       "select token, count(distinct user_id) as df "
                       "from tweet_tokens "
                       "group by token")
        self.con.query("create view df_tweet_view as "
                       "select token, count(distinct user_id, tweet_id) as df "
                       "from tweet_tokens "
                       "group by token")

        self.con.query("create view tf_view as "
                       "select token, user_id, count(*) as tf "
                       "from tweet_tokens "
                       "group by token, user_id")     
   
        self.con.query("create view num_docs_view as "
                       "select count(distinct user_id) as val from tweet_tokens")
        self.con.query("create view num_docs_tweet_view as "
                       "select count(distinct user_id, tweet_id) as val from tweet_tokens")

        self.con.query("create view tfidf_view_internal as "
                       "select termfreq.token, termfreq.user_id, termfreq.tf as tf, docfreq.df as df, "
                       "(1+log(tf)) * log((select val from num_docs_view)/df) as tfidf "
                       "from tf_view termfreq join df_view docfreq "
                       "on termfreq.token = docfreq.token")
        self.con.query("create view tfidf_tweet_view_internal as "
                       "select termfreq.token, termfreq.user_id, termfreq.tweet_id, 1 as tf, docfreq.df as df, "
                       "log((select val from num_docs_tweet_view)/df) as tfidf "
                       "from tweet_tokens termfreq join df_tweet_view docfreq "
                       "on termfreq.token = docfreq.token")

        self.con.query("create view tfidf_view as "
                       "select tid.token, tf.user_id, tf.tf, tf.df, tf.tfidf "
                       "from tfidf_view_internal tf join token_id tid "
                       "on tf.token = tid.id")
        self.con.query("create view tfidf_tweet_view as "
                       "select tid.token, tf.user_id, tf.tweet_id, tf.tf, tf.df, tf.tfidf "
                       "from tfidf_tweet_view_internal tf join token_id tid "
                       "on tf.token = tid.id")

        self.con.query("create view tfidf_user_norm_view as "
                       "select user_id, sqrt(sum(tfidf * tfidf)) as norm "
                       "from tfidf_view_internal "
                       "group by user_id")
        self.con.query("create view tfidf_norm_view as select t.token, t.user_id, t.tfidf/u.norm as tfidf_norm "
                       "from tfidf_view_internal t join tfidf_user_norm_view u "
                       "on t.user_id = u.user_id")

        self.con.query("create view tfidf_distance_view as "
                       "select t1.user_id u1, t2.user_id u2, sum(t1.tfidf_norm * t2.tfidf_norm) as dist "
                       "from tfidf_norm_view t1 join tfidf_norm_view t2 "
                       "on t1.token = t2.token "
                       "group by t1.user_id, t2.user_id")

    def TFIDFNormQuery(self, uids=None):
        if uids is None:
            return "select * from tfidf_norm_view"
        uids = ",".join(["%d" % u for u in uids])
        return ("select t.token, t.user_id, t.tfidf/u.norm as tfidf_norm "
                "from (select * from tfidf_view_internal  where user_id in (%s)) t "
                "join (select * from tfidf_user_norm_view where user_id in (%s)) u "
                "on t.user_id = u.user_id") % (uids,uids)

    def TFIDFDistance(self, uids=None):
        q = ("select t2.user_id, sum(t1.tfidf_norm * t2.tfidf_norm) as dist "
             "from (%s) t1 join (%s) t2 "
             "on t1.token = t2.token "
             "group by t2.user_id ") % (self.TFIDFNormQuery([self.GetUserId()]),self.TFIDFNormQuery(uids))
        if uids is None:
            self.con.query("drop view if exists tfidf_distance_%s" % self.g_data.myName)
            self.con.query("drop view if exists tfidf_distance_%s_internal" % self.g_data.myName)
            self.con.query("create view tfidf_distance_%s_internal as %s" % (self.g_data.myName, q))
            self.con.query("create view tfidf_distance_%s as "
                           "select users.screen_name, td.dist "
                           "from users join tfidf_distance_%s td "
                           "on users.id = td.user_id " % (self.g_data.myName, self.g_data.myName))
        else:
            return { int(r["user_id"]) : float(r["dist"]) for r in self.TimedQuery(q, "TFIDFDistance") }

    def InsertTweetTokens(self, uid, tid, tweet):
        tokens = v.Vocab(self.g_data).Tokenize(tweet)
        q = "insert into tweet_tokens (user_id, tweet_id, token) values (%d,%d,%%s)" % (uid, tid)
        for t in tokens:
            tokid = self.Feat2Id(t.encode("utf8"),table_name="token_id")
            try:                
                self.con.query(q,tokid)
            except Exception as e:
                assert e[0] == 1062, e #dup key
                

    def InsertAllTweetTokens(self):
        self.con.query("truncate table tweet_tokens") # because fuck you thats why!
        tweets = self.con.query("select user_id, id, body from tweets")
        for i,r in enumerate(tweets): # am i insane or genious?
            if i % 100 == 0:
                print float(i)/len(tweets)
            self.InsertTweetTokens(int(r["user_id"]),int(r["id"]),r["body"])

    def FixRetweets(self):
        rts = self.con.query("select json::retweeted_status as rt from tweets where json_length(json::retweeted_status) is not null")
        for i,r in enumerate(rts):
            print float(i)/len(rts)
            s = Status.NewFromJsonDict(json.loads(r["rt"]))
            try:
                self.InsertTweet(s,ignore_user=True)        
            except Exception as e:
                print e
                print r["rt"]

    def PushArticle(self, url, tweet_id, personality):
        q = "select * from articles where personality = %s and url = %s"
        arts = self.con.query(q, personality, url)
        if len(arts) == 0:
            q = ("insert into articles values(%d, NOW(), NULL, '%s', %%s)" % (tweet_id, personality))
            self.con.query(q,url)
        else:
            assert len(arts) == 1, arts
            updates = []
            if tweet_id < int(arts[0]['tweet_id']):
                updates.append("tweet_id = %d" % tweet_id)
            if arts[0]['processed'] is None:
                updates.append("inserted = NOW()")
            if len(updates) > 0:
                q = "update articles set %s where personality = %%s and url = %%s" % (",".join(updates))
                self.con.query(q, personality, url)

    def PopArticle(self):
        q = "select * from articles where processed is null order by tweet_id desc limit 1"
        arts = self.TimedQuery(q,"PopArticle")
        if len(arts) == 0:
            return None
        assert len(arts) == 1, arts
        return arts[0]['url'], arts[0]['personality']

    def FinishArticle(self, url, personality):
        q = "update articles set processed = NOW() where personality = %s and url = %s"
        self.TimedQuery(q, "FinishArticles", personality, url)

    def Feat2Id(self, feature, allow_insert=True, table_name="token_id"):
        q = "select id from %s where token=%%s" % (table_name)
        feat = self.con.query(q, feature)
        if len(feat) == 0:
            assert allow_insert, feature
            return int(self.con.execute("insert into %s (token) values (%%s)" % table_name,feature))
        return int(feat[0]['id'])
    
    def Id2Feat(self, fid, table_name="token_id"):
        return self.con.query("select token from %s where id = %d" % (table_name, fid))[0]['token']

    def IgnoreUser(self, user_name):
        self.con.query("insert into ignored_users select id from users where screen_name like '%s'" % user_name)
    
    def SetupTargetAnalysisViews(self, tok_order=1, min_num_tweets=10):
        views = ["mtok_feats","mtoks","mtweets","musers"]
        for v in views:
            self.con.query("drop view if exists %s" % v)
        botids = self.GetBotIds()
        self.con.query("create view musers as select * from (select distinct parent_id as user_id "
                       "from tweets "
                       "where parent_id is not null and user_id in (%s) and parent_id not in (select id from ignored_users)) t_outer "
                       "where (select count(*) from tweets t_inner where t_outer.user_id = t_inner.user_id) > %d" % (",".join(["%d" % b for b in botids]),min_num_tweets))
        self.con.query("create view mtweets as select tweets.user_id, tweets.id "
                       "from musers join tweets on musers.user_id = tweets.user_id "
                       "where parent_id not in (%s) or parent_id is null" %  ",".join(["%d" % b for b in botids]))
        if tok_order == 1:
            print "tok_order ought to be 1"
            toks_q = "select * from tweet_tokens"
        else:
            print "tok_order = ", tok_order
            toks_q = ("select t1.user_id as user_id, t1.tweet_id as tweet_id, concat(t1.token, '$_$', t2.token) as token "
                      "from tweet_tokens t1 join tweet_tokens t2 "
                      "on t1.user_id = t2.user_id and t1.tweet_id = t2.tweet_id")
        print toks_q
        self.con.query("create view mtoks as select tokens.user_id, tokens.token, log(1+count(*)) as val "
                       "from (%s) tokens join mtweets "
                       "on tokens.user_id = mtweets.user_id and tokens.tweet_id = mtweets.id "
                       "group by 1, 2" % toks_q)
        
    def InsertFeatures(self, dump = False):        
        if dump:
            self.con.query("drop table feature_id")
            self.DDL()
        self.Feat2Id("avg_retweet")
        self.Feat2Id("avg_favorite")
        self.Feat2Id("num_followers")
        self.Feat2Id("num_friends")
        self.Feat2Id("num_replies")
        self.Feat2Id("tweet_freq")
        self.TimedQuery("insert ignore into feature_id (feature) select concat('token_',token) from mtoks", "inserting features into feat_id")
        
    def ComputeFeatureMatrix(self):
        import nlp_learning as nm
        reload(nm)
        tok_feats = self.TimedQuery("select mtoks.user_id, feature_id.id, mtoks.val "
                                    "from mtoks join feature_id "
                                    "on feature_id.feature=concat('token_',mtoks.token)",
                                    "tok feats")
        user_feats = self.TimedQuery("select users.id, users.num_friends, users.num_followers "
                                     "from musers join users "
                                     "on users.id = musers.user_id",
                                     "user feats")
        tweet_feats = self.TimedQuery("select tweets.user_id, "
                                      "log(1 + avg(retweets)) as rts, "
                                      "log(1 + avg(favorites)) as favs, "
                                      "avg(parent is not null) as reps, "
                                      "unix_timestamp(NOW()) - unix_timestamp(min(ts)) as oldest, "
                                      "count(*) as count "
                                      "from musers join tweets "
                                      "on musers.user_id = tweets.user_id "
                                      "group by 1",
                                      "tweet feats")
        
        avg_retweets = self.Feat2Id("avg_retweet")
        avg_favorites = self.Feat2Id("avg_favorite")
        num_followers = self.Feat2Id("num_followers")
        num_friends = self.Feat2Id("num_friends")
        num_replies = self.Feat2Id("num_replies")
        tweet_freq = self.Feat2Id("tweet_freq")

        result = [(int(r["user_id"]), int(r["id"]), float(r["val"])) for r in tok_feats]
        result.extend([(int(r["id"]), num_followers, float(r["num_followers"])) for r in user_feats])
        result.extend([(int(r["id"]), num_friends, float(r["num_friends"])) for r in user_feats])
        result.extend([(int(r["user_id"]), avg_retweets, float(r["rts"])) for r in tweet_feats])
        result.extend([(int(r["user_id"]), avg_favorites, float(r["favs"])) for r in tweet_feats])
        result.extend([(int(r["user_id"]), num_replies, float(r["reps"])) for r in tweet_feats])
        result.extend([(int(r["user_id"]), tweet_freq, float(r["count"])/float(r["oldest"])) for r in tweet_feats])
        return nm.NLPMatrix(result)

    def ComputeResponseVector(self):
        rows = {}
        for gd in self.g_data.g_datas:
            us = self.con.query(("select musers.user_id, us.following from musers join user_following_status us "
                                 "on us.id = musers.user_id "
                                 "where us.my_name='%s' and us.has_followed = 1") % gd.myName)
            for i,u in enumerate(us):
                if i % 100 == 0:
                    print float(i)/len(us)
                uid = int(u["user_id"])
                if uid not in rows:
                    rows[uid] = 0.0
                if int(u["following"]) != 1:
                    rows[uid] = -1
                if rows[uid] < 0:
                    continue
                stats = gd.SocialLogic().HistoryStatistics(uid=uid)
                if stats["attempts"] == 0:
                    continue
                rows[uid] += math.log(1 + (stats["responses"] + stats["favorites"] * 0.125 + stats["retweets"] * 0.25)/stats["attempts"])
        for u in self.con.query("select * from musers"):
            uid = int(u["user_id"])
            if uid not in rows:
                rows[uid] = -1
        return rows
            
        
    def ExtractForTargetTraining(self, tok_order=1, min_num_tweets=10):
        self.SetupTargetAnalysisViews(tok_order=tok_order,min_num_tweets=min_num_tweets)
        self.InsertFeatures(dump=True)
        mat = self.ComputeFeatureMatrix()
        return mat, mat.ToVector(self.ComputeResponseVector())

    def GarbageCollectTweets(self):
        while True:
            usg = self.con.query("show databases extended like %s")["Memory (MBs)"]
            if int(usg) < 10000: # ten gigs is a lot
                return
            q = ("delete from tweets "
                 "where user_id not in (select id from user_following_status where has_followed = 1) "
                 "and (parent_id not in (%s) or parent_id is null) "
                 "limit 200" % ",".join(["%d" % b for b in botids]))
            deld = self.con.execute(q)
            self.con.query("delete from tweet_tokens where (user_id,tweet_id) not in (select user_id, id from tweets)")
            self.g_data.TraceInfo("Deleted %s rows" % deld)
            if int(deld) < 200:
                return
        
        
    def Act(self):
        if self.shard % MODES == 0:
            self.UpdateUsers()
        elif self.shard % MODES == 1:
            self.UpdateTweets()
        elif self.shard % MODES == 2:
            self.ProcessUnprocessedTweets()
        self.shard += 1
        
