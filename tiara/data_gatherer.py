import database as db
import persisted as p
import ticker as t
import random

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

class DataGatherer:
    def __init__(self, g_data, config):
        self.con = None
        self.tweets_to_process = p.PersistedSet('tweets_to_process')
        self.g_data = g_data
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
                        
                        "ts timestamp not null,"
                        
                        "index(user_id),"
                        "index(parent),"
                        "index(parent_id))"
                        "default charset = utf8mb4"))
                
    def UpdateTweets(self):
        max_id = None
        while True:
            statuses = self.apiHandler.ShowStatuses(screen_name=self.g_data.myName,
                                                    max_id=max_id)
            if statuses is None:
                self.g_data.TraceWarn("Failed to update tweets")
                return None
            if len(statuses) == 0:
                break
            max_id = min([s.GetId() for s in statuses]) - 1
                       
            for s in statuses:
                self.InsertTweet(s)

    def RemoveProcessedTweets(self):
        for tid in list(self.tweets_to_process.Get()):
            if (not self.Lookup(tid,"parent") is None) or (not self.Lookup(tid) is None):
                print "deleting %d" % tid
                self.tweets_to_process.Delete(tid)
            else:
                print "keeping %d" % tid

    def ProcessUnprocessedTweets(self):
        count = 60
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
        s = self.apiHandler.ShowStatus(tid)
        if not s is None:
            self.InsertTweet(s)
            return True
        else:
            if self.apiHandler.errno in [34,179,63]: # not found, not allowed, suspended
                self.con.query("insert into ungettable_tweets values (%d,%d) on duplicate key update errorcode=errorcode" % (tid,self.apiHandler.errno))
                return True
            self.g_data.TraceWarn("Unhandled error in InsertTweetById %d" % self.apiHandler.errno)
            assert False
            return None

    def InsertTweet(self, s):
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
        values = [sid, parent, name.encode("utf8"), uid, parent_name.encode("utf8"), parent_id, "%s", retweets, likes, timestamp.encode("utf8")]
        values = ",".join(values)
        query = "insert into tweets values (%s) on duplicate key update favorites = %s, retweets = %s" % (values, likes, retweets)
        self.con.query(query, body.encode("utf8"))
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
        res = self.con.query("select * from tweets where %s = %d" % (field,tid))
        if len(res) == 0:
            return None
        return res

    def FixTimestampBug(self):
        rows = [int(a["id"]) for a in self.con.query("select id from tweets where ts > '2015-01-03 00:00:00'")]
        for tid in rows:
            s = self.apiHandler.ShowStatus(tid)
            timestamp = "'%s'" % TwitterTimestampToMySQL(s.GetCreatedAt())
            self.con.query("update tweets set ts = %s where id = %d" % (timestamp.encode("utf8"), tid))
                
