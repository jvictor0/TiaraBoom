import global_data as g
import sys
from util import *
import server

if __name__ == "__main__":
    g_data = g.GlobalData()
    if len(sys.argv) == 1:
        sys.exit(0)
    if sys.argv[1] == "tweet_tokens":
        g_data.dbmgr.InsertAllTweetTokens()
    if sys.argv[1] == "source":
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
    if sys.argv[1] == "add_source":
        uid = g_data.ApiHandler().ShowUser(screen_name = sys.argv[3]).GetId()
        g_data.dbmgr.AddSource(sys.argv[2], uid, confirmed=True)
    if sys.argv[1] == "add_sources_from_config":
        for g_data in server.GDatas():
            if g_data.SocialLogic().IsArtRat():
                for sn in g_data.SocialLogic().params["reply"]["sources"]:
                    uid = g_data.ApiHandler().ShowUser(screen_name = sn)
                    if uid is None:
                        print "problem with " + sn
                        continue
                    uid = uid.GetId()
                    g_data.dbmgr.AddSource(g_data.SocialLogic().params["reply"]["personality"], uid, confirmed=True)
    if sys.argv[1] == "drop_tfidf_views":
        g_data.dbmgr.DropTFIDFViews()
    if sys.argv[1] == "tfidf_distance_view":
        g.GlobalData(name=sys.argv[2]).dbmgr.TFIDFDistance()
