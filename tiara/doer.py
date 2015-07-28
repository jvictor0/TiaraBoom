import global_data as g
import sys

if __name__ == "__main__":
    g_data = g.GlobalData()
    if len(sys.argv) == 1:
        sys.exit(0)
    if sys.argv[1] == "tweet_tokens":
        g_data.dbmgr.InsertAllTweetTokens()
    
