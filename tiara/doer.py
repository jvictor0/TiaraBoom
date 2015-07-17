import global_data as g
import sys

if __name__ == "__main__":
    g_data = g.GlobalData()
    if sys.argv[1] == "tweet_tokens":
        g_data.dbmgr.InsertAllTweetTokens()
    
