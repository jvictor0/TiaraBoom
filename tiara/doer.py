import global_data as g
import sys
from util import *
import server
import data_gatherer
import database
import tiara_ddl

if __name__ == "__main__":
    g_data = g.GlobalData()
    if len(sys.argv) == 1:
        sys.exit(0)
    elif sys.argv[1] == "tweet_tokens":
        g_data.dbmgr.InsertAllTweetTokens()
    elif sys.argv[1] == "source":
        while True:
            src = g_data.dbmgr.GetSource(sys.argv[2], confirmed = False)
            user = g_data.ApiHandler().ShowUser(user_id=src)
            print user.GetLang()
            if user.GetLang() != 'en':
                continue
            statuses = g_data.ApiHandler().ShowStatuses(user_id=src)
            break
        print "do you like the following account?"
        print "twitter.com/%s" % user.GetScreenName()
        count = 0
        for s in statuses:
            for url in (s.urls if not s.urls is None else []):
                count += 1
                print GetURL(s)
                break
            if count > 5:
                break
        print "(y/n)"
        while True:
            response = raw_input()
            if response in "yn":
                g_data.dbmgr.ConfirmSource(sys.argv[2],src,confirm=response=="y")
                break
            print "didnt understand that gbop"
    elif sys.argv[1] == "add_source":
        uid = g_data.ApiHandler().ShowUser(screen_name = sys.argv[3]).GetId()
        g_data.dbmgr.AddSource(sys.argv[2], uid, confirmed=True)
    elif sys.argv[1] == "drop_views":
        tiara_ddl.DropViews(g_data.dbmgr.con)
    elif sys.argv[1] == "new_ddl":
        tiara_ddl.DropViews(g_data.dbmgr.con)
        print "alter table"
        g_data.dbmgr.con.query("alter table %s rename %s_bak" % (sys.argv[2],sys.argv[2]))
        print "ddl"
        tiara_ddl.TiaraCreateTables(g_data.dbmgr.con)
        print "insert select"
        cols = ",".join([c['column_name'] for c in g_data.dbmgr.con.query("select column_name from information_schema.columns where table_name ='%s' and table_schema='tiaraboom' and extra != 'computed'" % sys.argv[2])])
        q = "insert into %s(%s) select %s from %s_bak" % (sys.argv[2], cols, cols, sys.argv[2])
        g_data.dbmgr.con.query(q)
        # for c in g_data.dbmgr.con.query("show partitions"):
        #     print c["Ordinal"]
        #     con = database.ConnectToMySQL("%s:%s" % (c["Host"],c["Port"]))
        #     con.query("use tiaraboom_%s" % c["Ordinal"])
        #     con.query(q)
        print "did not drop %s_bak" % sys.argv[2]
    elif sys.argv[1] == "add_fc":
        uid = g.GlobalData(name=sys.argv[2]).ApiHandler().ShowUser(screen_name = sys.argv[3]).GetId()
        g_data.dbmgr.EnqueueFollower(uid)
    elif sys.argv[1] == "insert_all_tweet_tokens":
        g_data.dbmgr.InsertAllTweetTokens()
    elif sys.argv[1] == "upvote":
        g_data.dbmgr.Upvote(-1, int(sys.argv[2]), 1)
    elif sys.argv[1] == "downvote":
        g_data.dbmgr.PinDownvote(int(sys.argv[2]))
    elif sys.argv[1] == "update_users":
        g.GlobalData(name=sys.argv[2]).dbmgr.UpdateUsers()
    elif sys.argv[1] == "process_tc":
        g.GlobalData(name=sys.argv[2]).dbmgr.ProcessTargetCandidates()
    elif sys.argv[1] == "follow":
        uid = g.GlobalData(name=sys.argv[2]).SocialLogic().Follow()
    elif sys.argv[1] == "bother_random":
        uid = g.GlobalData(name=sys.argv[2]).SocialLogic().Bother()
    elif sys.argv[1] == "manage_db":
        uid = g.GlobalData(name=sys.argv[2]).dbmgr.Act()
    elif sys.argv[1] == "candidate_daemon":
        g_datas = server.GDatas()
        data_gatherer.ProcessCandidatesLoop([gd.dbmgr for gd in g_datas], sys.argv[2])
    else:
        assert False
