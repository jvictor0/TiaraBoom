import database as db
import persisted as p
import ticker as t
import random
import json
from twitter.status import Status
from twitter.user import User

MODES=2

# looks like Fri Jan 02 03:14:31 +0000 2015
def TwitterTimestampToMySQL(ts):
    ts = ts.split()
    assert ts[0] in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], ts
    mon = str(1 + ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(ts[1]))
    day = ts[2]
    time = ts[3]
    assert ts[4] == "+0000", ts
    year = ts[5]
    return "%s-%s-%s %s" % (year,mon,day,time)

class DataManager:
    def __init__(self, g_data, config):
        self.con = None
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
                assert not self.LookupStatus(s) is None

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
        count = 30
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
            self.InsertTweetById(long(random.choice(tweets)["parent"]))

    def InsertTweetById(self, tid):
        s = self.apiHandler.ShowStatus(tid, cache=False)
        if not s is None:
            self.InsertTweet(s)
            return True
        else:
            if self.apiHandler.errno in [34,179,63]: # not found, not allowed, suspended
                self.InsertUngettable(tid, self.apiHandler.errno)
                return True
            self.g_data.TraceWarn("Unhandled error in InsertTweetById %d" % self.apiHandler.errno)
            assert False
            return None

    def InsertUngettable(self, tid, errno):
        if self.con is None:
            return
        self.con.query("insert into ungettable_tweets values (%d,%d) on duplicate key update errorcode=errorcode" % (tid,errno))

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

    def GetUnprocessed(self, user=None):
        query = ("select tl.id, tl.parent, tl.parent_name, tl.parent_id "
                 "from tweets tl left join tweets tr "
                 "on tr.id = tl.parent "
                 "where tr.id is null and tl.parent is not null and (tl.user_name = '%s' or tl.parent_name = '%s') " 
                 "and not exists(select * from ungettable_tweets where id = tl.parent)")
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
        s.SetUser(User())
        s.GetUser().SetScreenName(row['user_name'])
        s.GetUser().SetId(long(row['user_id']))
        return s

    def LookupStatuses(self, tid, field = "id"):
        rows = self.Lookup(tid,field)
        return [self.RowToStatus(r) for r in rows if not r["json"] is None]

    def LookupStatus(self, tid, field = "id"):
        statuses = self.LookupStatuses(tid, field)
        if len(statuses) == 0:
            return None
        return statuses[0]
            
    def Act(self):
        if self.shard % MODES == 0:
            self.UpdateTweets()
        elif self.shard % MODES == 1:
            self.ProcessUnprocessedTweets()
        self.shard += 1
