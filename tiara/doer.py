import global_data as g
import sys
from util import *
import server
import database

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
    elif sys.argv[1] == "add_sources_from_config":
        for g_data in server.GDatas():
            if g_data.SocialLogic().IsArtRat():
                for sn in g_data.SocialLogic().params["reply"]["sources"]:
                    uid = g_data.ApiHandler().ShowUser(screen_name = sn)
                    if uid is None:
                        print "problem with " + sn
                        continue
                    uid = uid.GetId()
                    g_data.dbmgr.AddSource(g_data.SocialLogic().params["reply"]["personality"], uid, confirmed=True)
    elif sys.argv[1] == "drop_views":
        g_data.dbmgr.DropViews()
    elif sys.argv[1] == "tfidf_distance_view":
        dbmgr = g.GlobalData(name=sys.argv[2]).dbmgr
        dbmgr.UpdateArtRatTFIDF()
        dbmgr.TFIDFDistance()
    elif sys.argv[1] == "new_ddl":
        g_data.dbmgr.DropViews()
        print "alter table"
        g_data.dbmgr.con.query("alter table %s rename %s_bak" % (sys.argv[2],sys.argv[2]))
        print "ddl"
        g_data.dbmgr.DDL()
        print "insert select"
        cols = ",".join([c['column_name'] for c in g_data.dbmgr.con.query("select column_name from information_schema.columns where table_name ='%s' and table_schema='tiaraboom' and extra != 'computed'" % sys.argv[2])])
        q = "insert into %s(%s) select %s from %s_bak" % (sys.argv[2], cols, cols, sys.argv[2])
        for c in g_data.dbmgr.con.query("show partitions"):
            con = database.ConnectToMySQL("%s:%s" % (c["Host"],c["Port"]))
            con.query("use tiaraboom_%s" % c["Ordinal"])
            con.query(q)
        print "did not drop %s_bak" % sys.argv[2]
    elif sys.argv[1] == "add_fc":
        uid = g.GlobalData(name=sys.argv[2]).ApiHandler().ShowUser(screen_name = sys.argv[3]).GetId()
        g_data.dbmgr.EnqueueFollower(uid)
    elif sys.argv[1] == "target_views":
        g_data.dbmgr.CreateTargetCandidatesViews()
    else:
        assert False
