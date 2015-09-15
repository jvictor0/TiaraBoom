import database as db
import vocab as v

import random
import time
import json
import datetime
import os
import math

import union_find 

from twitter.status import Status
from twitter.user import User

from util import *

import threading

MODES=4

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
        self.user_id = None
        self.horde = {}
        self.hordeUpserts = {}
        self.needsUpdateBotTweets = False
        self.xact = False
        self.timedQueryLimit = 1.0
        if no_ddl:
            return
        if "gatherer_authentication" in config:
            self.apiHandler = api_handler.ApiHandler(config["gatherer_authentication"])
        else:
            self.apiHandler = g_data.ApiHandler()
        self.DDL()
        self.updatedArtratTFIDF = False

    def Begin(self):
        assert not self.xact
        self.xact = True
        self.con.query("begin")

    def Commit(self):
        assert self.xact
        self.xact = False        
        try:
            for k,val in self.horde.iteritems():
                q = "insert into %s values %s" % (k,",".join(val))
                if k in self.hordeUpserts:
                    q = q + " on duplicate key update " + self.hordeUpserts[k]
                self.con.query(q)   
            if self.needsUpdateBotTweets:
                self.UpdateConversationIds()
            self.con.query("commit")            
            self.horde = {}
            self.hordeUpserts = {}
            self.needsUpdateBotTweets = False
        except Exception as e:
            self.horde = {}
            self.hordeUpserts = {}
            self.needsUpdateBotTweets = False
            self.con.query("rollback")
            raise e

    def Rollback(self):
        assert self.xact
        self.xact = False        
        self.horde = {}
        self.needsUpdateBotTweets = False
        self.hordeUpserts = {}
        self.con.query("rollback")
    
    def Horde(self, table, values, *parameters):
        parameters = [unidecode(p) if isinstance(p,unicode) else p for p in parameters]
        if parameters != None and parameters != ():
            values = values % tuple([self.con._db.escape(p, self.con.encoders) for p in parameters])
        if table not in self.horde:
            self.horde[table] = []
        self.horde[table].append(values)

    def HordeUpsert(self, table, upsert):
        self.hordeUpserts[table] = upsert

    def TimedQuery(self, q, name, *largs):
        t0 = time.time()
        result = self.con.query(q, *largs)
        if time.time() - t0 > self.timedQueryLimit:
            self.g_data.TraceInfo("%s took %f secs" % (name, time.time() - t0))
        return result
            
    def ApiHandler(self):
        return self.apiHandler
        
    def DDL(self):
        self.con.query(("create table if not exists tweets("                        
                        "id bigint not null,"
                        "user_id bigint not null,"                        
                        "retweets bigint not null,"
                        "favorites bigint not null,"
                        "parent bigint default null,"
                        "primary key(user_id, id),"
                        "key(id),"
                        "key(parent))"))
        self.con.query(("create columnar table if not exists tweets_storage("                        
                        "id bigint not null,"
                        "parent bigint default null,"                        
                        "user_id bigint not null,"                        
                        "parent_id bigint default null,"                        
                        "body blob, "                        
                        "ts datetime not null,"
                        "json json ,"            
                        "num_hashtags as ifnull(json_length(json::hashtags),0) persisted bigint, "
                        "num_media as ifnull(json_length(json::media),0) persisted bigint, "
                        "num_user_mentions as ifnull(json_length(json::user_mentions),0) persisted bigint, "
                        "is_retweet as not isnull(json::retweeted_status) persisted boolean, "
                        "language as json::$lang persisted varbinary(200), "
                        "shard key(user_id, id),"
                        "index(user_id, id) using clustered columnar)"))
        self.con.query(("create table bot_tweets ("
                        "id bigint not null,"
                        "parent bigint default null,"                        
                        "user_id bigint not null,"                        
                        "parent_id bigint default null,"                        
                        "body blob, "                        
                        "ts datetime not null,"
                        "json json ,"
                        "conversation_id bigint not null, "
                        "key (conversation_id), "
                        "key (parent_id,parent), "
                        "primary key(user_id, id))"))

        self.con.query("drop view if exists tweets_joined_no_json")
        self.con.query("drop view if exists tweets_joined")
        self.con.query("drop view if exists bot_tweets_joined")
        self.con.query(("create view tweets_joined as "
                        "select ts.id, ts.user_id, ts.parent_id, tweets.parent, tweets.favorites, tweets.retweets, ts.body, ts.json, ts.ts "
                        "from tweets_storage ts join tweets "
                        "on ts.user_id = tweets.user_id and ts.id = tweets.id "))
        self.con.query(("create view bot_tweets_joined as "
                        "select ts.id, ts.user_id, ts.parent_id, tweets.parent, tweets.favorites, tweets.retweets, ts.body, ts.json, ts.ts "
                        "from bot_tweets ts join tweets "
                        "on ts.user_id = tweets.user_id and ts.id = tweets.id "))
        self.con.query(("create view tweets_joined_no_json as "
                        "select ts.id, ts.user_id, ts.parent_id, tweets.parent, tweets.favorites, tweets.retweets, ts.body, ts.ts, '{}' as json, ts.conversation_id "
                        "from tweets_storage ts join tweets "
                        "on ts.user_id = tweets.user_id and ts.id = tweets.id "))

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
        self.con.query(("create table if not exists user_token_frequency("
                        "user_id bigint,"
                        "token bigint,"
                        "count bigint,"
                        "shard(token),"
                        "primary key(user_id, token))"))
        self.con.query(("create reference table if not exists user_document_frequency("
                        "token bigint,"
                        "count bigint,"
                        "primary key(token))"))
        self.con.query(("create table if not exists tweet_document_frequency("
                        "token bigint,"
                        "count bigint,"
                        "primary key(token))"))
        self.con.query(("create table if not exists articles("
                        "tweet_id bigint not null,"
                        "inserted datetime not null,"
                        "processed datetime,"
                        "personality varbinary(100) not null,"
                        "url blob not null, "
                        "key(tweet_id, personality),"
                        "key(personality, url),"
                        "key (inserted),"                    
                        "shard())"))
        self.con.query(("create reference table if not exists token_id("
                        "id bigint primary key auto_increment,"
                        "token varbinary(200),"
                        "unique key(token))"))
        self.con.query(("create reference table if not exists token_representatives("
                        "id bigint not null,"
                        "token varbinary(200) primary key)"))
        self.con.query(("create reference table if not exists artrat_tfidf("
                        "user_id bigint,"
                        "token bigint,"
                        "primary key(user_id, token),"
                        "tfidf_norm double)"))
        self.con.query(("create table if not exists ignored_users("
                        "id bigint primary key)"))
        self.con.query(("create table if not exists sources("
                        "personality varbinary(100),"
                        "user_id bigint,"
                        "primary key(personality, user_id),"
                        "confirmed tinyint,"
                        "updated timestamp default current_timestamp on update current_timestamp)"))
        self.con.query(("create reference table if not exists target_candidates("
                        "id bigint not null,"
                        "bot_id bigint not null,"
                        "primary key(bot_id, id),"
                        "processed datetime default null)"))
        self.con.query(("create reference table if not exists follower_cursors("
                        "id bigint not null,"
                        "bot_id bigint not null,"
                        "cursr bigint not null,"                        
                        "primary key(bot_id, id, cursr),"
                        "processed datetime default null)"))
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
        tweets = self.GetUnprocessed()
        self.g_data.TraceInfo("There are currently %d unprocessed tweets" % len(tweets))
        count = min(30,len(tweets))
        random.shuffle(tweets)
        for i in xrange(count):
            self.InsertTweetById(tweets[i]["parent"])
            
    # NOTE: this requires running RepareDocFreq eventually
    #
    def PurgeTweet(self, uid, tid, body):
        self.Begin()
        try:
            assert self.con.query("delete from tweets where user_id = %d and id = %d" % (uid,tid)) == 1
            assert self.con.query("delete from tweets_storage where user_id = %d and id = %d" % (uid,tid)) == 1
            tokens = [self.Feat2Id(a) for a in set(v.Vocab(self.g_data).Tokenize(body))]
            for t in tokens:
                assert self.con.query("update user_token_frequency set count = count - 1 where user_id = %d and token = %s" % (uid, t)) == 1
        except Exception as e:
            self.g_data.TraceWarn("Rollback in PurgeTweet")
            self.Rollback()
            raise e
        self.Commit()

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
        try:
            self.con.query("insert into ungettable_tweets values (%d,%d)" % (tid,errno))
        except Exception as e:
            assert e[0] == 1062, e # dup key        

    def InsertAfflicted(self, uid, errno):
        if self.con is None:
            return
        try:
            self.con.query("insert into user_afflictions values (%d,%d)" % (uid,errno))
        except Exception as e:
            assert e[0] == 1062, e # dup key

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

    def InsertTweet(self, s, single_xact=True, insert_user=True):
        if s.GetRetweeted_status() is not None:
            self.InsertTweet(s.GetRetweeted_status(), single_xact=single_xact)
        parent = "null"
        parent_id  = "null"
        if not s.GetInReplyToStatusId() is None:
            parent = str(s.GetInReplyToStatusId())
            if not s.GetInReplyToUserId() is None:
                parent_id = str(s.GetInReplyToUserId())
        sid = s.GetId()
        uid = s.GetUser().GetId()
        body = s.GetText()
        timestamp = "'%s'" % TwitterTimestampToMySQL(s.GetCreatedAt())
        likes = s.GetFavoriteCount()
        retweets = s.GetRetweetCount()
        values = [str(sid), parent, str(uid), parent_id,
                  "%s",
                  timestamp.encode("utf8"),
                  "%s"]
        values = " , ".join(values)
        values = "(%s)" % (values)
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
            jsdict["retweeted_user_id"] = s.GetRetweeted_status().GetUser().GetId()
            jsdict["retweeted_status"] = s.GetRetweeted_status().GetId()
        try:
            if single_xact:
                self.Begin()
            inserted = self.con.query("insert into tweets(id,user_id,retweets,favorites,parent) values (%d,%d,%d,%d,%s) "
                                      "on duplicate key update "
                                      "favorites=values(favorites), retweets=values(retweets)" % (sid,uid,retweets, likes, parent))
            assert inserted in [0,1,2], (inserted, sid)
            if inserted == 1:
                if s.GetUser().GetId() in self.GetBotIds() or s.GetInReplyToUserId() in self.GetBotIds():
                    self.needsUpdateBotTweets = True
                self.Horde("tweets_storage", values, body.encode("utf8"), json.dumps(jsdict).encode("utf8"))
                self.InsertTweetTokens(s.GetUser().GetId(), s.GetText(), single_xact=False)
            if insert_user:
                self.InsertUser(s.GetUser())
            if single_xact:
                self.Commit()
        except Exception:
            self.g_data.TraceWarn("Rollback in InsertTweet")
            self.Rollback()
            raise

    def GetUnprocessed(self, user=None):
        uid = self.GetUserId()
        query = ("select tl.parent "
                 "from tweets_storage tl left join tweets tr "
                 "on tr.id = tl.parent and tr.user_id = tl.parent_id " 
                 "where tr.id is null and tl.parent is not null and (tl.user_id = %s or tl.parent_id = %s) " 
                 "and not exists(select * from ungettable_tweets where id = tl.parent) "
                 "limit 90")
        query = query % (uid, uid)
        return self.TimedQuery(query, "GetUnprocessed")

    def Lookup(self, tid, uid=None):
        assert not uid is None, uid
        if tid is not None:
            res = self.con.query("select t.id, t.user_id, ts.parent, ts.parent_id, ts.body, ts.json, ts.ts, t.retweets, t.favorites "
                                 "from tweets_storage ts join tweets t "
                                 "on ts.user_id = t.user_id and ts.id = t.id "
                                 "where ts.id = %d and ts.user_id = %d" % (tid, uid))
        else:
            res = self.con.query("select t.id, t.user_id, ts.parent, ts.parent_id, ts.body, ts.json, ts.ts, t.retweets, t.favorites "
                                 "from tweets_storage ts join tweets t "
                                 "on ts.user_id = t.user_id and ts.id = t.id "
                                 "where ts.user_id = %d" % (uid))
        return res
    
    def RowToStatus(self, row, user, skip_rts=False):
        if row["json"] is None:
            return None
        jsdict = json.loads(row["json"])
        jsdict["text"] = row["body"]
        jsdict["id"] = int(row["id"])
        jsdict["created_at"] = MySQLTimestampToTwitter(row["ts"])
        jsdict["favorited"] = False
        jsdict["retweeted"] = False
        if row["parent"] is not None:
            jsdict["in_reply_to_status_id"] = int(row["parent"])
            jsdict["in_reply_to_user_id"] = int(row["parent_id"])
        if "retweeted_status" in jsdict:
            if skip_rts:
                return None
            if "retweeted_user_id" not in jsdict:
                the_id = self.con.query("select user_id from tweets_storage where id = %d" % int(jsdict["retweeted_status"]))
                if len(the_id) == 0:
                    return None
                assert len(the_id) == 1
                the_id = int(the_id[0]['user_id'])
                jsdict["retweeted_user_id"] = the_id
                rows = self.con.query("update tweets_storage set json = json_set_string(json,'retweeted_user_id',%d) where user_id = %d and id = %d" % (the_id, int(row["user_id"]), jsdict["id"]))
                assert rows == 1, (jsdict,rows)
            jsdict["retweeted_status"] = self.LookupStatus(int(jsdict["retweeted_status"]), int(jsdict["retweeted_user_id"]))
            del jsdict["retweeted_user_id"]
            if jsdict["retweeted_status"] is None:
                return None
            else:
                jsdict["retweeted_status"] = jsdict["retweeted_status"].AsDict()
        assert 'entities' not in jsdict, jsdict
        jsdict['entities'] = {}
        jsdict['entities']['hashtags'] = [{"text":h} for h in jsdict['hashtags']] if 'hashtags' in jsdict else []
        jsdict['entities']['urls'] = [{"url": u, "expanded_url" : v} for u,v in jsdict['urls'].iteritems()] if 'urls' in jsdict else []
        jsdict['entities']['media'] = jsdict['media'] if 'media' in jsdict else []
        jsdict['entities']['user_mentions'] = jsdict['user_mentions'] if 'user_mentions' in jsdict else []
        s = Status.NewFromJsonDict(jsdict)
        s.SetRetweetCount(int(row["retweets"]))
        s.SetFavoriteCount(int(row["favorites"]))
        s.SetUser(user)
        return s

    def LookupStatuses(self, tid=None, uid = None, skip_rts=False):
        assert not uid is None, uid
        rows = self.Lookup(tid,uid)
        user = self.LookupUser(uid)
        if user is None:
            return []
        return filter(lambda x: not x is None,
                      [self.RowToStatus(r, user, skip_rts=skip_rts) for r in rows])

    def LookupStatus(self, tid, uid=None):
        statuses = self.LookupStatuses(tid, uid)
        if len(statuses) == 0:
            return None
        return statuses[0]

    def LookupStatusesFromUsers(self, uids=None, skip_rts=False, filters = [], json = True):
        jscol = "ts.json" if json else "json_set_string('{}','lang',ts.language) as json"
        filters = "".join([" and " + f for f in filters])
        rows = self.con.query("select t.id, t.user_id, ts.parent, ts.parent_id, ts.body, %s, ts.ts, t.retweets, t.favorites "
                              "from tweets_storage ts join tweets t "
                              "on ts.user_id = t.user_id and ts.id = t.id "
                              "where ts.user_id in (%s)%s" % (jscol, ",".join(["%d"%u for u in uids]), filters))
        users = {uid: self.LookupUser(uid) for uid in uids}
        return filter(lambda x: not x is None,
                      [self.RowToStatus(r, users[int(r["user_id"])], skip_rts=skip_rts) 
                       for r in rows 
                       if not users[int(r["user_id"])] is None])

    def LookupUser(self, uid, days_old = None, ignore_following_status=False):
        q = "select * from users where id = %d" % uid
        if not days_old is None:
            q = q + " and updated > timestampadd(day, -%d, now())" % days_old
        row = self.con.query(q)
        if len(row) == 0:
            return None
        assert len(row) == 1
        return self.RowToUser(row[0], days_old, ignore_following_status)

    def LookupUsers(self, uids, days_old=None, ignore_following_status=False):
        uidstr = ",".join([str(u) for u in set(uids)])
        q = "select * from users where id in (%s)" % uidstr
        if not days_old is None:
            q = q + " and updated > timestampadd(day, -%d, now())" % days_old
        rows = self.con.query(q)
        users = {int(row["id"]) : self.RowToUser(row, days_old, ignore_following_status) for row in rows}
        for u in uids:
            if int(u) not in users:
                users[int(u)] = None
        return users
        
    def RowToUser(self, row, days_old=None, ignore_following_status=False):        
        if row["num_followers"] is None:
            return None
        if row["language"] is None:
            return None
        user = User()
        user.SetScreenName(row["screen_name"])
        user.SetId(int(row["id"]))
        user.SetFollowersCount(int(row["num_followers"]))
        user.SetFriendsCount(int(row["num_friends"]))
        user.SetLang(row["language"])
        if not ignore_following_status:
            q = "select * from user_following_status where my_name = '%s' and id = %d" % (self.g_data.myName,user.GetId())
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
        q = "select max(ts) as a from tweets_storage where user_id = %s" % (uid)
        result = self.con.query(q)
        if result[0]["a"] is None:
            return None
        assert len(result) == 1
        return MySQLTimestampToPython(result[0]["a"])

    def UnixTimes(self, uid):
        q = "select unix_timestamp(ts) as ts from tweets_storage where user_id = %s order by user_id, id" % (uid)
        return [int(r["ts"]) for r in self.con.query(q)]

    def MostRecentTweetAt(self, uid):
        myuid = self.GetUserId()
        q = "select max(ts) as a from tweets_storage where user_id = %s and parent_id=%s" % (myuid, uid)
        result = self.con.query(q)
        if result[0]["a"] is None:
            return None
        assert len(result) == 1
        return MySQLTimestampToPython(result[0]["a"])

    def TweetHistory(self, uid):
        myuid = self.GetUserId()
        q = ("select id as chid, parent as paid, user_id as chu, parent_id as pau from tweets_storage "
             "where (user_id = %d and parent_id = %d) "
             " or (parent_id = %d and   user_id = %d)")
        q = q % (uid, myuid, uid, myuid)
        rows = self.TimedQuery(q, "TweetHistory")
        uids = list(set([(r["chu"]) for r in rows] + [(r["pau"]) for r in rows]))
        tids = list(set([(r["chid"]) for r in rows] + [(r["paid"]) for r in rows]))
        if len(tids) == 0:
            return []
        assert len(uids) > 0, uid
        q = ("select t.id, ts.parent_id, ts.parent, t.user_id, '' as body, '0000-00-00 00:00:00' as ts, '{}' as json, t.retweets, t.favorites "
             "from tweets_storage ts join tweets t "
             "on ts.user_id = t.user_id and ts.id = t.id "
             "where ts.id in (%s) and ts.user_id in (%s)" % (",".join(tids),",".join(uids)))
        status_rows = {int(r["id"]) : r for r in self.TimedQuery(q,"fetch tweet history rows")}
        users = {int(u) : self.LookupUser(int(u)) for u in uids}
        result = []
        for r in rows:
            left  = self.RowToStatus(status_rows[int(r["chid"])], users[int(r["chu"])])
            assert left is not None, r
            try:
                right = self.RowToStatus(status_rows[int(r["paid"])], users[int(r["pau"])])
                assert right is not None
            except Exception as e:
                assert len(self.con.query("select * from ungettable_tweets where id = %s" % r["paid"])) > 0, r 
                continue
            result.append((left,right))
        return result

    def InitializeConversation(self, uid, tid, parent_uid=None, parent_tid=None):
        if parent_uid is None:            
            cid = tid
        else:
            row = self.con.query("select id, user_id, parent, parent_id, conversation_id from tweets_storage where user_id = %d and id = %d" % (parent_uid, parent_tid))
            assert len(rows) <= 1            
            if len(rows) == 0:
                s = None
                if len(self.con.query("select * from ungettable_tweets where id = %s" % parent_tid)) == 0:
                    s = self.ApiHandler().ShowStatus(parent_tid, cache=False)
                    assert s is not None or len(self.con.query("select * from ungettable_tweets where id = %s" % parent_id)) > 0, (parent_uid, parent_tid)
                    if s is not None:
                        row = [{"conversation_id" : None, "id" : s.GetId(), "user_id" : s.GetUser().GetId(), "parent_id" : s.GetInReplyTouserId(), "parent" : s.GetInReplyToStatusId() }]
                if s is None:
                    row = [{"conversation_id" : tid}]
            if row[0]['conversation_id'] is None:
                cid = self.InitializeConversation(int(row[0]["user_id"]), int(row[0]["id"]), Int(row[0]["parent_id"]), Int(row[0]["parent"]))
            else:
                cid = int(row[0]['conversation_id'])
        self.con.query("update tweets_storage set conversation_id = %d where user_id = %d and id = %d" % (cid, uid, tid)) 
        return cid


    def MoveBotTweets(self, rows, reason=None):
        if len(rows) > 0:
            if reason is not None:
                self.g_data.TraceInfo("MoveBotTweets: Moving %d rows which are %s" % (len(rows), reason))
            uids = ",".join([str(a) for a in set([r["user_id"] for r in rows])])
            tids = ",".join([str(a) for a in set([r["id"] for r in rows])])
            self.con.query(("insert into bot_tweets "
                            "select id, parent, user_id, parent_id, body, ts, json, ifnull(parent, id) "
                            "from tweets_storage where user_id in (%s) and id in (%s)") % (uids,tids))
            return True
        return False
        

    def LoadBotTweets(self):
        while True:
            # we first find all reachable tweets not in the bot_tweets table
            # obvious bot tweets must move!
            #
            bot_ids = ",".join([str(a) for a in self.GetBotIds()])
            q = (("select ts.user_id, ts.id "
                  "from tweets_storage ts "
                  "where (user_id in (%s) or parent_id in (%s)) "
                  "and not exists (select * from bot_tweets bs_inner where ts.user_id = bs_innser.user_id and ts.id = bs_inner.id)" % (bot_ids, bot_ids)))
            rows = self.con.query(q)
            self.MoveBotTweets(rows, "which by a bot or for a bot")
            
            # we find tweets whose parent is in the bot_tweets, but not it
            #
            q = (("select ts.user_id, ts.id "
                  "from tweets_storage ts join bot_tweets bt "
                  "on ts.parent = bt.id and ts.parent_id = bt.user_id "
                  "where not exists (select * from bot_tweets bs_inner where ts.user_id = bs_innser.user_id and ts.id = bs_inner.id)"))
            rows = self.con.query(q)
            if self.MoveBotTweets(rows, "which are replies to bot_tweets"):
                continue
            
            # we find bot_tweets which reply to tweets
            # we find tweets whose parent is in the bot_tweets, but not it
            #
            q = (("select t.user_id, t.id "
                  "from tweets t join bot_tweets bt "
                  "on bt.parent = t.id and bt.parent_id = t.user_id"
                  "where not exists (select * from bot_tweets bs_inner where t.user_id = bs_innser.user_id and t.id = bs_inner.id)"))
            rows = self.con.query(q)
            if self.MoveBotTweets(rows, "which are replies from bot_tweets"):
                continue
            
            break

    def UpdateConversationIds(self):
        multstmt = not self.xact
        if multstmt:
            self.Begin()
        try:
            self.UpdateBotTweets()

            while True:
                # find all bot_tweets with conversation_id having a parent
                # we could use a Union Find and be all fancy pantsy, but fuck it
                # this loop will be executed only log(conversation_length) times if each bot_tweet just points to its direct parent
                # the vast majority of conversations are short enough that they won't be picked up by this.  
                #
                q = (("select bt1.user_id, bt1.id, bt2.conversation_id "
                      "from bot_tweets bt1 join bot_tweets bt2 "
                      "on bt1.conversation_id = bt2.id "
                      "where bt2.conversation_id != bt2.id "))
                rows = self.con.query(q)
                if len(rows) > 0:
                    print "moving %d conversation_ids" % len(rows)
                    for i,r in enumerate(rows):
                        if i % 100 == 0:
                            print float(i)/len(rows)
                        self.con.query("update bot_tweets set conversation_id = %s where user_id = %s and id = %s" % (r["conversation_id"], r["user_id"],r["bot_id"]))
                    continue
                break
            if multstmt:
                assert not self.needsUpdateBotTweets, "needsUpdateBotTweets set in multstmt call to UpdateConversationId"
                self.Commit()
        except Exception as e:
            if multstmt:
                self.Rollback()
            raise e
        
    # Int -> [[Status]]
    def RecentConversations(self, limit, min_length=2, bots=None):
        q = ("select * from bot_tweets_joined "
             "where conversation_id in "
             "   (select conversation_id from bot_tweets group by 1 having count(*) > %d order by 1 desc limit %d) "
             "order by -conversation_id, id ")
        q = q % (min_length, limit)
        rows = self.con.query(q)
        users = self.LookupUsers([r["user_id"] for r in rows], ignore_following_status=True)        
        result = []
        conversation_id = ""
        for r in rows:
            status = self.RowToStatus(r, users[int(r["user_id"])])
            if r["conversation_id"] != conversation_id:
                result.append([])
                conversation_id = r["conversation_id"]
            result[-1].append(status)
        return result


    def GetUserId(self, screen_name = None):
        if screen_name is None:
            screen_name = self.g_data.myName
        if self.user_id is None or screen_name != self.g_data.myName:
            rows = self.con.query("select id from users where screen_name = '%s'" % screen_name)
            if len(rows) == 0:
                return self.ApiHandler().ShowUser(screen_name=screen_name).GetId()
            self.user_id = int(rows[0]["id"])
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
        
        

    def TFIDF(self, uid=None, tweet=None, user=None):
        if user is not None:
            uid = user.GetId()
        if tweet is None:
            q = "select token, tfidf from tfidf_view where user_id = %d" % uid
            rows = self.TimedQuery(q,"TFIDF_user")
        else:
            params = list(set(v.Vocab(self.g_data).Tokenize(tweet.GetText())))
            q = ("select token_id.token, log((select max(count) from tweet_document_frequency)/(1+tdf.count)) as tfidf "
                 "from tweet_document_frequency tdf join token_id "
                 "on token_id.id = tdf.token "
                 "where token_id.token in (%s)")
            if len(params) == 0:
                return []
            rows = self.TimedQuery(q % ",".join(["%s" for _ in params]), 
                                   "TFIDF_tweet", *params)                
        return [(r["token"], float(r["tfidf"])) for r in rows]

    def DropTFIDFViews(self):
        bot_views = self.con.query("show tables like 'tfidf_bot_distance%'")
        for t in bot_views:
            k = t.keys()[0]
            if not t[k].endswith("internal"):
                self.con.query("drop view %s" % t[k])
                self.con.query("drop view if exists %s_internal" % t[k])            
        for v in ["tfidf_bot_distance_%s" % self.g_data.myName, "tfidf_bot_distance_%s_internal" % self.g_data.myName,
                  "tfidf_distance_view",
                  "tfidf_important_word_view","tfidf_important_word_view_internal",
                  "tfidf_distance_numerator_view",
                  "tfidf_norm_view","tfidf_user_norm_view",
                  "tfidf_view", 
                  "tfidf_view_internal", 
                  "num_docs_view","max_df_view"]:
            self.con.query("drop view if exists %s" % v)

    def MakeTFIDFViews(self):
        self.DropTFIDFViews()
        self.con.query("create view num_docs_view as "
                       "select count(distinct user_id) as val from user_token_frequency")
        self.con.query("create view max_df_view as "
                       "select max(count) as val from user_document_frequency")

        self.con.query("create view tfidf_view_internal as "
                       "select termfreq.token, termfreq.user_id, termfreq.count as tf, docfreq.count as df, "
                       "log(1+termfreq.count) * log((select val from max_df_view)/(1+docfreq.count)) as tfidf "
                       "from user_token_frequency termfreq join user_document_frequency docfreq "
                       "on termfreq.token = docfreq.token")

        self.con.query("create view tfidf_view as "
                       "select tid.token, tf.user_id, tf.tf, tf.df, tf.tfidf "
                       "from tfidf_view_internal tf join token_id tid "
                       "on tf.token = tid.id")

        self.con.query("create view tfidf_user_norm_view as "
                       "select user_id, sqrt(sum(tfidf * tfidf)) as norm "
                       "from tfidf_view_internal "
                       "group by user_id")
        self.con.query("create view tfidf_norm_view as select t.token, t.user_id, t.tf, t.df, t.tfidf, t.tfidf/u.norm as tfidf_norm "
                       "from tfidf_view_internal t join tfidf_user_norm_view u "
                       "on t.user_id = u.user_id")

        self.con.query("create view tfidf_distance_numerator_view as "
                       "select t1.user_id u1, t2.user_id u2, sum(t1.tfidf * t2.tfidf) as dist "
                       "from tfidf_view t1 join tfidf_view t2 "
                       "on t1.token = t2.token "
                       "group by t1.user_id, t2.user_id")

        self.con.query("create view tfidf_distance_view as "
                       "select t1.user_id u1, t2.user_id u2, sum(t1.tfidf_norm * t2.tfidf_norm) as dist "
                       "from tfidf_norm_view t1 join tfidf_norm_view t2 "
                       "on t1.token = t2.token "
                       "group by t1.user_id, t2.user_id")

        self.con.query("create view tfidf_important_word_view_internal as "
                       "select t1.user_id u1, t2.user_id u2, t1.token, t1.tfidf_norm * t2.tfidf_norm as dist, t1.df as df, "
                       "t1.tf as u1_tf, t1.tfidf as u1_tfidf, "
                       "t2.tf as u2_tf, t2.tfidf as u2_tfidf "
                       "from tfidf_norm_view t1 join tfidf_norm_view t2 "
                       "on t1.token = t2.token")
        self.con.query("create view tfidf_important_word_view as "
                       "select u1.screen_name u1, u2.screen_name u2, ti.token, f.dist, f.df, f.u1_tf, f.u1_tfidf, f.u2_tf, f.u2_tfidf "
                       "from tfidf_important_word_view_internal f join users u1 join users u2 join token_id ti "
                       "on f.u1 = u1.id and f.u2 = u2.id and f.token = ti.id")
        self.con.query("create view tfidf_bot_distance_view as "
                       "select t2.user_id, sum(t1.tfidf_norm * t2.tfidf)/sqrt(sum(t2.tfidf*t2.tfidf)) as dist "
                       "from artrat_tfidf t1 right join tfidf_view_internal t2 "
                       "on t1.token = t2.token "
                       "group by t2.user_id "
                       "having count(t1.token) > 0")



    def UpdateArtRatTFIDF(self):
        personality = self.g_data.SocialLogic().ArtRatPersonality()
        q = ("select tr.id as token, log(1 + count(*)) * log((select val from tiaraboom.max_df_view)/(1+udf.count)) as tfidf "
             "from artrat.%s_dependencies dp "
             "join tiaraboom.token_representatives tr "
             "join tiaraboom.user_document_frequency udf "
             "on dp.dependant = tr.token and tr.id = udf.token "
             "group by 1") % personality
        nq = "select token, tfidf/(select sqrt(sum(tfidf * tfidf)) from (%s) unv) as tfidf_norm from (%s) tb" % (q,q)
        vals = ["(%d,%s,%s)" % (self.GetUserId(), r["token"], r["tfidf_norm"]) for r in self.con.query(nq)]
        try:
            self.Begin()
            self.con.query("delete from artrat_tfidf where user_id = %d" % self.GetUserId())
            self.con.query("insert into artrat_tfidf values %s" % ",".join(vals))    
            self.updatedArtratTFIDF = True
            self.Commit()
        except Exception as e:
            self.g_data.TraceWarn("Rollback in UpdateArtatTFIDF")
            self.Rollback()
            raise e

    def ArtRatTFIDFNormQuery(self):
        return "select * from artrat_tfidf where user_id = %d" % self.GetUserId()
    
    def TFIDFNormQuery(self, uids=None, normalize=True):
        if uids is None:
            if normalize:
                return "select * from tfidf_norm_view"
            else:
                return "select * from tfidf_view_internal"
        if len(uids) == 1:
            norm = ("/(select sqrt(sum(s.tfidf * s.tfidf)) as norm from tfidf_view_internal s where user_id = %d)" % uids[0]) if normalize else ""
            return ("select t.token, t.user_id, t.tfidf%s as tfidf%s "
                    "from tfidf_view_internal t where user_id = %d") % (norm, "_norm" if normalize else "", uids[0])
        uids = ",".join(["%d" % u for u in uids])
        if normalize:
            return ("select t.token, t.user_id, t.tfidf/u.norm as tfidf_norm "
                    "from (select * from tfidf_view_internal  where user_id in (%s)) t "
                    "join (select * from tfidf_user_norm_view where user_id in (%s)) u "
                    "on t.user_id = u.user_id") % (uids,uids)
        else:
            return "select * from tfidf_view_internal where user_id in (%s)" % uids

    def TFIDFDistance(self, uids=None):
        if not self.updatedArtratTFIDF:
            self.UpdateArtRatTFIDF()
        q = ("select t2.user_id, sum(t1.tfidf_norm * t2.tfidf)/sqrt(sum(t2.tfidf*t2.tfidf)) as dist "
             "from (%s) t1 right join (%s) t2 "
             "on t1.token = t2.token "
             "group by t2.user_id "
             "having count(t1.token) > 0") % (self.ArtRatTFIDFNormQuery(),
                                              self.TFIDFNormQuery(uids, normalize=False))
        if uids is None:
            self.con.query("drop view if exists tfidf_bot_distance_%s" % self.g_data.myName)
            self.con.query("drop view if exists tfidf_bot_distance_%s_internal" % self.g_data.myName)
            self.con.query("create view tfidf_bot_distance_%s_internal as %s" % (self.g_data.myName, q))
            self.con.query("create view tfidf_bot_distance_%s as "
                           "select users.screen_name, td.dist "
                           "from users join tfidf_bot_distance_%s_internal td "
                           "on users.id = td.user_id " % (self.g_data.myName, self.g_data.myName))
        else:
            return { int(r["user_id"]) : float(r["dist"]) for r in self.TimedQuery(q, "TFIDFDistance") }

    def InsertTweetTokens(self, uid, tweet, single_xact=True):
        if single_xact:
            self.Begin()
        else:
            assert self.xact, "must have began xaction in InsertTweetTokens"
        try:
            tokens = [self.Feat2Id(a) for a in set(v.Vocab(self.g_data).Tokenize(tweet))]
            self.InsertTweetTokensById(uid, tokens)
            if single_xact:
                self.Commit()
        except Exception as e:
            self.g_data.TraceWarn("Rollback in InsertTweetTokens")
            print e
            self.Rollback()
            raise e

    def InsertTweetTokensById(self, uid, tokens):
        q = "insert into user_token_frequency (user_id, token, count) values (%d,%%s,1) on duplicate key update count = count + 1" % (uid)
        for t in tokens:
            rc = self.con.query(q % t)
            if rc == 1:
                self.Horde("user_document_frequency", "(%s,1)" % t)
            self.Horde("tweet_document_frequency", "(%s,1)" % t)
        self.HordeUpsert("user_document_frequency", "count=count+1")
        self.HordeUpsert("tweet_document_frequency","count=count+1")

    def InsertAllTweetTokens(self, blocksize = 1000, dbhost="127.0.0.1:3308"):
        self.con.query("truncate table user_token_frequency") # because fuck you thats why!
        self.con.query("truncate table user_document_frequency")
        self.con.query("truncate table tweet_document_frequency")
        lkt = { r["token"] : r["id"] for r in self.con.query("select * from token_id") }
        voc = v.Vocab(self.g_data)
        total_size = int(self.con.query("select max(user_id) as a from tweets_storage")[0]["a"])
        max_user = [0]
        lock = threading.Lock()
        def InsertAllTweetTokensWorker():
            mycon =  db.ConnectToMySQL(host=dbhost)
            mycon.query("use tiaraboom")
            while True:
                lock.acquire()
                users = [int(r['id']) for r in self.con.query("select id from users where id > %d order by id limit %d" % (max_user[0],blocksize))]
                if len(users) == 0:
                    return
                new_max_user = max(users)
                tweets = self.con.query("select user_id, body from tweets_storage where user_id > %d and user_id <= %d " % (max_user[0], new_max_user))
                max_user[0] = new_max_user
                print float(max_user[0])/total_size
                print "processing %d tweets" % len(tweets)
                lock.release()
                for i,r in enumerate(tweets): # am i insane or genious?
                    tokens = [lkt[a] for a in set(voc.Tokenize(r["body"]))]
                    q = "insert into user_token_frequency (user_id, token, count) values (%s,%%s,1) on duplicate key update count = count + 1" % (r["user_id"])
                    for t in tokens:
                        mycon.query(q,t)
        InsertAllTweetTokensWorker()
        self.RepairDocFreq()


    def RepairDocFreq(self):
        self.con.query("truncate table user_document_frequency")
        self.con.query("truncate table tweet_document_frequency")
        self.con.query("insert into user_document_frequency select token, count(*) from user_token_frequency group by 1")
        self.con.query("insert into tweet_document_frequency select token, sum(count) from user_token_frequency group by 1")

    def PushArticle(self, url, tweet_id, personality):
        q = "select * from articles where personality = %s and url = %s"
        arts = self.con.query(q, personality, url)
        if len(arts) == 0:
            q = ("insert into articles values(%d, NOW(), NULL, '%s', %%s)" % (tweet_id, personality))
            self.con.query(q,url)
            return True
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
            return False

    def PopArticle(self):
        q = "select * from articles where processed is null order by tweet_id desc limit 1"
        arts = self.TimedQuery(q,"PopArticle")
        if len(arts) == 0:
            return None
        assert len(arts) == 1, arts
        return arts[0]['url'], arts[0]['personality']

    def PopAllArticles(self):
        q = "select * from articles where processed is null"
        arts = self.TimedQuery(q,"PopAllArticles")
        return [(a["url"], a["personality"]) for a in arts]

    def FinishArticle(self, url, personality):
        q = "update articles set processed = NOW() where personality = %s and url = %s"
        self.TimedQuery(q, "FinishArticles", personality, url)

    def GetSource(self, personality, confirmed=True):
        confirmed = int(confirmed)
        q = "select user_id from sources where confirmed = %d and personality = '%s' order by updated limit 1" % (confirmed,personality)
        result = int(self.con.query(q)[0]['user_id'])
        self.con.query("update sources set updated=now() where user_id=%d and personality='%s'" % (result,personality))
        return result

    def AddSource(self, personality, user_id, confirmed=False):
        if not confirmed:
            unconfirmed = int(self.con.query("select count(*) as a from sources where personality = '%s' and confirmed=0")[0]['a'])
            if unconfirmed > 10:
                return False
        confirmed = int(confirmed)
        q = "insert into sources values ('%s', %d, %d, now())" % (personality, user_id, confirmed)
        try:
            self.con.query(q)
        except Exception as e:
            assert e[0] == 1062, e # dup key                    
        return True
        
    def ConfirmSource(self, personality, user_id, confirm=True):
        confirm = 1 if confirm else -1
        q = "update sources set confirmed = %d where personality = '%s' and user_id = %d" % (confirm,personality,user_id)
        assert self.con.query(q) == 1

    def Feat2Id(self, feature, allow_insert=True):
        q = "select id from token_id where token=%s"
        feat = self.con.query(q, feature)
        if len(feat) == 0:
            assert allow_insert, feature
            return int(self.con.execute("insert into token_id (token) values (%s)", feature))
        return feat[0]['id']
    
    def Id2Feat(self, fid, table_name="token_id"):
        return self.con.query("select token from %s where id = %d" % (table_name, fid))[0]['token']

    def IgnoreUser(self, user_name):
        self.con.query("insert into ignored_users select id from users where screen_name = '%s'" % user_name)

    def AddTargets(self, ids):
        values = ",".join(["(%d,%d,null)" % (i,self.GetUserId()) for i in ids])
        self.con.query("insert into target_candidates values %s on duplicate key update processed=processed" % values)

    def EnqueueFollower(self, uid):
        try:
            self.con.query("insert into follower_cursors values(%d,%d,-1,null)" % (uid, self.GetUserId()))
        except Exception as e:
            assert e[0] == 1062, e # dup key                    
    
    def ProcessFollowerCursors(self):
        while True:
            rows = self.con.query("select * from follower_cursors where bot_id = %d and processed is null limit 1" % self.GetUserId())
            if len(rows) == 0:
                return
            row = rows[0]
            result = self.ApiHandler().GetFollowerIDsPaged(user_id=int(rows[0]['id']), cursor=int(rows[0]['cursr']))
            if result is None:
                return
            ids, next_cursor = result
            try:
                self.Begin()
                if next_cursor != 0:
                    self.con.query("update follower_cursors set processed=now() where bot_id = %s and id = %s and cursr = %s" % (row["bot_id"],row["id"],row["cursr"]))
                self.con.query("insert into follower_cursors values(%s,%d,%d,null)" % (row["id"], self.GetUserId(), next_cursor))
                self.AddTargets(ids)
                self.Commit()
            except Exception as e:
                self.g_data.TraceWarn("Rollback in ProcessFollowerCursor")                
                self.Rollback()
                raise e
            if self.ApiHandler().last_call_rate_limit_remaining < 5:
                return
    
    def ProcessTargetCandidates(self, screen_name = None):
        q = "select id from target_candidates where bot_id = %d and processed is null limit 75" % self.GetUserId(screen_name)
        users = [int(r["id"]) for r in self.con.query(q)]
        for u in users:
            self.ApiHandler().ShowStatuses(user_id=u)
        if len(users) > 0:
            self.con.query("update target_candidates set processed = NOW() where bot_id = %d and id in (%s)" % (self.GetUserId(screen_name), ",".join(["%d" % u for u in users])))

    def CreateTargetCandidatesViews(self):
        for v in ["candidates_joined_filtered_view","candidates_joined_view"]:
            self.con.query("drop view if exists %s" % v)
        self.con.query("create view candidates_joined_view as "
                       "select users.screen_name, users.id as uid, users.num_followers, users.num_friends, users.language, "
                       "       ts.id as tid, ts.num_hashtags, ts.num_media, ts.num_user_mentions, ts.language as tweet_language, ts.is_retweet, ts.ts, "
                       "       tc.bot_id, tc.processed "
                       "from tweets_storage ts join users join target_candidates tc "
                       "on ts.user_id = users.id and users.id = tc.id "
                       "where ts.user_id in (select sql_small_result id from target_candidates where processed is not null)")
        self.con.query("create view candidates_joined_filtered_view as "
                       "select bot_id, screen_name, uid, num_followers, num_friends, processed, ts "
                       "from candidates_joined_view " 
                       "where num_user_mentions = 0 and num_media = 0 and num_hashtags <= 2 "
                       "and not is_retweet and ts > processed - interval 7 day "
                       "and num_followers <= 5000 and num_friends <= 5000 and num_followers >= 100 and num_friends >= 100 "
                       "and language like 'en%' and tweet_language like 'en%' ")
#        con.query("create view candidates_filtered_view as " 
#                  "select bot_id, screen_name, uid, num_followers, num_friends, count(*) as count, timestampdiff(minute, processed, min(ts)) as tweets_per_minute  "
#                  "from candidates_joined_filtered_view ")
        
    def Act(self):
        self.ProcessFollowerCursors()
        if self.shard % MODES == 0:
            self.UpdateUsers()
        elif self.shard % MODES == 1:
            self.UpdateTweets()
            if self.g_data.SocialLogic().IsArtRat():
                self.UpdateArtRatTFIDF()
        elif self.shard % MODES == 2:
            self.ProcessUnprocessedTweets()
            self.UpdateUsers()
        elif self.shard % MODES == 3:
            self.ProcessTargetCandidates()
        self.shard += 1
       
 
