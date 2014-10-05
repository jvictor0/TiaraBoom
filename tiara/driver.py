import social_logic as sl
import global_data as g
import time

if __name__ == '__main__':
    g_data = g.GlobalData()

    g_data.TraceInfo("Starting up Tiara Boom Server!")

    while True:
        print "awake"
        sl.Reply(g_data)
        time.sleep(60)
