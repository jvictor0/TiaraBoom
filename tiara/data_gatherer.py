
import database as db
import vocab as v
import conversation

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

import tiara_ddl

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
        confs = json.load(f)
        dbhost = confs["dbHost"]
    return DataManager(FakeGData(name), dbhost, no_ddl = True)

class DataManager:
    def __init__(self, g_data, host, no_ddl=False):
        self.con = None
        self.g_data = g_data
        self.shard = 0
        self.con = db.ConnectToMySQL(host=host)
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
        self.apiHandler = g_data.ApiHandler()
        self.DDL()
        self.updatedArtratTFIDF = False
        try:
            self.con.query("insert into bots values (%d,'%s', 10)" % (self.GetUserId(), self.g_data.myName))
        except Exception as e:
            assert e[0] == 1062, e # dup key        

    def Begin(self):
        assert not self.xact
        self.xact = True
        self.con.query("begin")

    def Commit(self):
        assert self.xact
        self.xact = False        
        try:
            for k,val in self.horde.iteritems():
                if k in self.hordeUpserts:
                    values = ",".join(["(%s)" % ",".join([str(a) for a in ki + (vi,)]) 
                                       for ki,vi in val.iteritems()])
                    q = "insert into %s values %s" % (k, values)
                    if self.hordeUpserts[k] is not None:
                        q = q + " on duplicate key update " + self.hordeUpserts[k]
                else:
                    q = "insert into %s values %s" % (k,",".join(val))
                self.con.query(q)   
            self.con.query("commit")            
            self.horde = {}
            self.hordeUpserts = {}
            if self.needsUpdateBotTweets:
                self.UpdateConversationIds()
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

    def HordeUpsert(self, table, key, value, upsert):
        assert isinstance(key,tuple), key
        assert isinstance(value,int), value
        self.hordeUpserts[table] = upsert
        if table not in self.horde:
            self.horde[table] = {}
        if key not in self.horde[table]:
            self.horde[table][key] = value
        else:
            self.horde[table][key] += value

    def TimedQuery(self, q, name, *largs):
        t0 = time.time()
        result = self.con.query(q, *largs)
        if time.time() - t0 > self.timedQueryLimit:
            self.g_data.TraceInfo("%s took %f secs" % (name, time.time() - t0))
        return result
            
    def ApiHandler(self):
        return self.apiHandler
        
    def DDL(self):
        tiara_ddl.TiaraCreateTables(self.con)
        tiara_ddl.TiaraCreateViews(self.con)
                
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
        assert False, "broken by columnarize user_token_frequency"
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
        im_url = user.profile_image_url
        values = ",".join([uid, sn, folls, friens, language, "NOW()", "'%s'" % im_url])
        updates = ["num_followers = %s" % folls,
                   "num_friends = %s" % friens,
                   "screen_name = %s" % sn,
                   "language = %s" % language,
                   "image_url = values(image_url)",
                   "updated = NOW()"]
        q = "insert into users values (%s) on duplicate key update %s" % (values, ",".join(updates))
        self.con.query(q)

        following = "1" if user.following else "0"
        has_followed = following

        updates = ["following = %s" % following, "updated = NOW()"]
        if following == "1":
            updates.append("has_followed = 1")
        
        q = ("insert into user_following_status values (%s,%d,%s,%s,NOW()) "
             "on duplicate key update %s")
        q = q % (uid, self.GetUserId(), following, has_followed, ",".join(updates))
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
                               "where bot_id = %d and id = %d and has_followed = 1 and following = 0")
                              % (self.GetUserId(), uid))
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
        if "urls" in jsdict:
            jsdict["urls"] = [{"url": u, "expanded_url" : v} for u,v in jsdict['urls'].iteritems()] if 'urls' in jsdict else []
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
            inserted = self.con.query("insert into tweets(id,user_id,retweets,favorites) values (%d,%d,%d,%d) "
                                      "on duplicate key update "
                                      "favorites=values(favorites), retweets=values(retweets)" % (sid,uid,retweets, likes))
            assert inserted in [0,1,2], (inserted, sid)
            if inserted == 1:
                if s.GetUser().GetId() in self.GetBotIds() or s.GetInReplyToUserId() in self.GetBotIds():
                    self.needsUpdateBotTweets = True
                self.Horde("tweets_storage", values, body.encode("utf8"), json.dumps(jsdict).encode("utf8"))
                self.InsertTweetTokens(s.GetId(), s.GetUser().GetId(), s.GetText(), single_xact=False)
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
        jsdict['entities']['urls'] = jsdict['urls'] if 'urls' in jsdict else []
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
        user.profile_image_url = row["image_url"]
        if len(user.profile_image_url) == 0:
            user.profile_image_url = "https://abs.twimg.com/sticky/default_profile_images/default_profile_2_normal.png"
        if not ignore_following_status:
            q = "select * from user_following_status where bot_id = %d and id = %d" % (self.GetUserId(),user.GetId())
            if not days_old is None:
                q = q + " and updated > timestampadd(day, -%d, now())" % days_old
            row = self.con.query(q)
            if len(row) == 0:
                return None
            user.following = True if row[0]["following"] == "1" else False
        return user

    def EverFollowed(self, uid):
        res = self.con.query("select has_followed from user_following_status where bot_id = %d and id = %d" % (self.GetUserId(),uid))
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
            except Exception:
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
        

    def UpdateBotTweets(self):
        while True:
            # we first find all reachable tweets not in the bot_tweets table
            # obvious bot tweets must move!
            #
            bot_ids = ",".join([str(a) for a in self.GetBotIds()])
            q = (("select ts.user_id, ts.id "
                  "from tweets_storage ts "
                  "where (user_id in (%s) or parent_id in (%s)) "
                  "and not exists (select * from bot_tweets bs_inner where ts.user_id = bs_inner.user_id and ts.id = bs_inner.id)" % (bot_ids, bot_ids)))
            rows = self.con.query(q)
            self.MoveBotTweets(rows, "which by a bot or for a bot")
            
            # we find tweets whose parent is in the bot_tweets, but not it
            #
            q = (("select ts.user_id, ts.id "
                  "from tweets_storage ts join bot_tweets bt "
                  "on ts.parent = bt.id and ts.parent_id = bt.user_id "
                  "where not exists (select * from bot_tweets bs_inner where ts.user_id = bs_inner.user_id and ts.id = bs_inner.id)"))
            rows = self.con.query(q)
            if self.MoveBotTweets(rows, "which are replies to bot_tweets"):
                continue
            
            # we find bot_tweets which reply to tweets
            # we find tweets whose parent is in the bot_tweets, but not it
            #
            q = (("select t.user_id, t.id "
                  "from tweets t join bot_tweets bt "
                  "on bt.parent = t.id and bt.parent_id = t.user_id "
                  "where not exists (select * from bot_tweets bs_inner where t.user_id = bs_inner.user_id and t.id = bs_inner.id)"))
            rows = self.con.query(q)
            if self.MoveBotTweets(rows, "which are replies from bot_tweets"):
                continue
            
            break        

    def UpdateTargetingState(self, full):
        if full:
            self.con.query("delete from targeting_state")
        q = "insert into targeting_state select * from targeting_state_view on duplicate key update last_targeted=values(last_targeted), tweets_to=values(tweets_to)"
        self.TimedQuery(q, "UpdateTargetingState")

    def UpdateConversationIds(self):
        assert not self.xact
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
                    self.con.query("update bot_tweets set conversation_id = %s where user_id = %s and id = %s" % (r["conversation_id"], r["user_id"],r["id"]))
                continue
            break
        self.UpdateTargetingState(full=False)
        
    # Int -> [[Status]]
    def RecentConversations(self, args):
        limit  = LKDI(args, "limit", 10)
        offset = LKDI(args, "offset", 0)        
        convid = LKDI(args, "conversation_id", None)
        include_singletons = LKDB(args, "include_singletons", False)
        include_all        = LKDB(args, "include_all", False)
        include_favs       = LKDB(args, "include_favs", False)
        include_rts        = LKDB(args, "include_rts", False)
        order_by           = LKD(args, "order_by", "recent")
        if order_by not in ["recent","popular"]:
            order_by = "recent"
        if convid is None:

            if order_by == "recent":
                order_by = "order by max_id desc"
            elif order_by == "popular":
                order_by = "order by upvotes desc, max_id desc "

            or_preds = ["to_bots > 0","upvotes > 0"]            
            if include_singletons:
                or_preds.append("count = 1")
            if include_favs:
                pass
            if include_rts:
                pass
            if include_all:
                or_preds = ["true"]
            where_clause = " or ".join(or_preds)

        else:
            where_clause = "conversation_id=%d" % convid
            order_by_clause + ""
        q = ("""select *                                                           
                from bot_tweets_joined join                                        
                (
                      select conversation_id, max_id, upvotes
                      from conversations_view        
                      where %s
                      %s
                      limit %d, %d
                ) conversations                  
                on conversations.conversation_id=bot_tweets_joined.conversation_id 
                order by max_id desc, id""")
        q = q % (where_clause, offset, limit)
        rows = self.con.query(q)
        users = self.LookupUsers([r["user_id"] for r in rows], ignore_following_status=True)        
        result = []
        conversation_id = ""
        for r in rows:
            status = self.RowToStatus(r, users[int(r["user_id"])])
            if r["conversation_id"] != conversation_id:
                conversation_id = r["conversation_id"]
                result.append(conversation.Conversation(r))
            result[-1].tweets.append(status)
        return result

    def Upvote(self, user_id, convo_id, amount=1):
        self.con.query("insert into conversation_upvotes(user_id, conversation_id, upvotes) values (%d, %d, %d) on duplicate key update amount = values(amount)" % (user_id, convo_id, amount))

    def Downvote(self, user_id, convo_id):
        self.con.query("delete from conversation_upvotes where user_id = %d and conversation_id = %d" % (user_id, convo_id, amount))
    
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
             "where has_followed = 1 and bot_id = %d and "
             "id not in (select id from user_afflictions where affliction in (%d,%d)) "
             "order by updated limit 75")
        q = q % (self.GetUserId(), AFFLICT_SUSPENDED, AFFLICT_DEACTIVATED)
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

    def UpdateArtRatTFIDF(self):
        if self.g_data.SocialLogic().IsArtRat():
            min_normalizer = 0.0
            max_normalizer = None
            for i in xrange(10):
                maxdf = self.con.query("select val from max_df_view")[0]["val"]
                normalizer = float(self.con.query("select normalizer from bots where id = %d" % self.GetUserId())[0]['normalizer'])
                personality = self.g_data.SocialLogic().ArtRatPersonality()
                q = ("select tr.id as token, exp(log(1 + count(*)) * log(%s/(1+udf.count))/%f) as tfidf "
                     "from %s_dependencies dp "
                     "straight_join token_representatives tr "
                     "straight_join user_document_frequency udf "
                     "on dp.dependant = tr.token and tr.id = udf.token "
                     "group by 1") % (maxdf, normalizer, personality)
                nq = "select %d, token, tfidf/(select sqrt(sum(tfidf * tfidf)) from (%s) unv) as tfidf_norm from (%s) tb" % (self.GetUserId(), q,q)
                self.TimedQuery("insert into artrat_tfidf %s on duplicate key update tfidf_norm=values(tfidf_norm)" % nq, "UpdateArtRatTFIDF")
                self.updatedArtratTFIDF = True
                
                frac = float(self.con.query("select sqrt(sum(tfidf_norm * tfidf_norm)) as frac "
                                            "from (select tfidf_norm from artrat_tfidf where user_id=%d order by tfidf_norm desc limit 100) sub "
                                            % self.GetUserId())[0]['frac'])
                new_normalizer = None
                if frac < 0.45:
                    max_normalizer = normalizer
                    new_normalizer = (normalizer + min_normalizer)/2
                elif frac > 0.55:
                    min_normalizer = normalizer
                    if max_normalizer is None:
                        new_normalizer = 2 * normalizer
                    else:
                        new_normalizer = (normalizer + max_normalizer)/2                        
                else:
                    break
                self.con.query("update bots set normalizer = %f where id = %d" % (new_normalizer, self.GetUserId()))
                
        q = ("insert into artrat_tfidf(user_id, token, tfidf_norm) select %d, id, 0 from token_id on duplicate key update tfidf_norm=tfidf_norm" 
             % (self.GetUserId()))
        self.con.query(q)
            
    def TFIDFDistance(self, uids=None):
        if not self.updatedArtratTFIDF:
            self.UpdateArtRatTFIDF()
        if uids is None:
            uidpred = ""
        elif len(uids) == 1:
            uidpred = "and t2.user_id = %d" % uids[0]
        else:
            uidpred = "and t2.user_id in (%s)" % ",".join(map(str,uids))
        q = ("select t2.user_id, sum(t1.tfidf_norm * t2.tfidf)/sqrt(sum(t2.tfidf*t2.tfidf)) as dist "
             "from artrat_tfidf t1 right join tfidf_view_internal t2 "
             "on t1.token = t2.token "
             "where t1.user_id = %d %s "
             "group by t2.user_id "
             "having count(t1.token) > 0") % (self.GetUserId(),uidpred)
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

    def InsertTweetTokens(self, tid, uid, tweet, single_xact=True):
        if single_xact:
            self.Begin()
        else:
            assert self.xact, "must have began xaction in InsertTweetTokens"
        try:
            tokens = [self.Feat2Id(a) for a in set(v.Vocab(self.g_data).Tokenize(tweet))]
            self.InsertTweetTokensById(tid, uid, tokens)
            if single_xact:
                self.Commit()
        except Exception as e:
            self.g_data.TraceWarn("Rollback in InsertTweetTokens")
            print e
            self.Rollback()
            raise e

    def InsertTweetTokensById(self, tid, uid, tokens):
        for t in tokens:
            self.Horde("tweet_tokens","(%s,%s,%s)" % (uid,tid,t))
            self.HordeUpsert("user_token_frequency", (uid, int(t)), 1, None)
            self.HordeUpsert("tweet_document_frequency", (int(t),), 1, "count=count+values(count)")

    def TweetTokenBackgroundMerger(self):
        while True:
            if not self.TweetTokenBackgroundMergerIteration():
                time.sleep(60 * 5)

    def TweetTokensBackgroundMergerIteration(self):
        self.Begin()
        try:            
            row = self.con.query("select user_id, token, sum(count) as tt from user_token_frequency "
                                 "group by 1, 2 "
                                 "having count(*) > 1 "
                                 "limit 1")
            if len(row) == 0:
                return False
            tt = int(row[0]["tt"])
            tti = tt
            assert tt > 0, row
            while tt > 0:
                tt -= self.con.query("update user_token_frequency set count = count - 1 "
                                     "where count > 0 and user_id = %s and token = %s "
                                     "limit %d " % (row[0]["user_id"], row[0]["token"], tt))
                assert tt >= 0, tt
            assert tti > 0, row
            self.con.query("insert into user_token_frequency (user_id, token, count) values (%s,%s,%d)" % (row[0]["user_id"], row[0]["token"], tti))
            self.con.query("delete from user_token_frequency where count = 0")
            self.Commit()
            return True
        except Exception as e:
            self.Rollback()
            raise e

    def InsertAllTweetTokens(self, blocksize = 1000):
        self.con.query("delete from tweet_tokens") # because fuck you thats why!
        lkt = { r["token"] : r["id"] for r in self.con.query("select * from token_id") }
        voc = v.Vocab(self.g_data)
        total_size = int(self.con.query("select max(user_id) as a from tweets_storage")[0]["a"])
        max_user = [0]
        if True:
            while True:
                users = [int(r['id']) for r in self.TimedQuery("select id from users where id > %d order by id limit %d" % (max_user[0],blocksize), "getusers")]
                if len(users) == 0:
                    return
                new_max_user = max(users)
                tweets = self.TimedQuery("select id, user_id, body from tweets_storage where user_id > %d and user_id <= %d " % (max_user[0], new_max_user), "get tweets")
                max_user[0] = new_max_user
                print float(max_user[0])/total_size
                print "processing %d tweets" % len(tweets)
                values = []
                t0 = time.time()
                for i,r in enumerate(tweets): # am i insane or genious?
                    tokens = [lkt[a] for a in set(voc.Tokenize(r["body"]))]
                    for t in tokens:
                        values.append("(%s,%s,%s)" % (r["id"],r["user_id"],t))
                tt = time.time() - t0
                print "created insert of length %d in %f secs (%f rps, %f tps)" % (len(values), tt, len(tweets)/tt, len(values)/tt)
                self.TimedQuery("insert into tweet_tokens(id,user_id,token) values %s" % ",".join(values), "do insert")


    def RepairDocFreq(self):
        self.con.query("truncate table tweet_document_frequency")
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
        values = ",".join(["(%d,%d,null,0)" % (i,self.GetUserId()) for i in ids])
        self.con.query("insert into target_candidates(id, bot_id, processed, eliminated) values %s on duplicate key update processed=processed" % values)

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
                self.con.query("update follower_cursors set processed=now() where bot_id = %s and id = %s and cursr = %s" % (row["bot_id"],row["id"],row["cursr"]))
                if next_cursor != 0:
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

    def EliminateTargetCandidates(self):
        rows = ",".join([a["uid"] for a in self.con.query("select uid from candidates_predictors_no_distance_view")])
        if len(rows) != 0:
            self.con.query("update target_candidates set eliminated=1 where processed is not null and id not in (%s)" % rows)

    def NextTargetCandidate(self):
        if not self.updatedArtratTFIDF:
            self.UpdateArtRatTFIDF()
        q = "select uid from candidates_scored_view where bot_id = %d order by score desc limit 1" % (self.GetUserId())
        rows = self.TimedQuery(q, "NextTargetCandidate")
        if len(rows) == 0:
            return None
        return int(rows[0]['uid'])

    def NextTargetStatus(self, user_id=None):
        if not self.updatedArtratTFIDF:
            self.UpdateArtRatTFIDF()
        q = "select user_id, id from botherable_tweets_scored_view_internal where bot_id = %d %s order by score desc limit 1" 
        q = q % (self.GetUserId(), "" if user_id is None else ("and user_id = %d" % user_id))
        rows = self.TimedQuery(q, "NextTargetStatus")
        if len(rows) == 0:
            return None
        return self.LookupStatus(int(rows[0]["id"]), int(rows[0]["user_id"]))

    def Act(self):
        self.ProcessFollowerCursors()
        if self.shard % MODES == 0:
            self.UpdateUsers()
        elif self.shard % MODES == 1:
            self.UpdateTweets()
            self.UpdateArtRatTFIDF()
        elif self.shard % MODES == 2:
            self.ProcessUnprocessedTweets()
            self.UpdateUsers()
        elif self.shard % MODES == 3:
            self.ProcessTargetCandidates()
        self.shard += 1
       
 
