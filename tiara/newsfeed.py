import data_gatherer as dg


class NewsFeedGenerator(object):
    def __init__(self, bots, database):
        self.bots = bots
        self.database = database

    def GetConversations(self):
        convos = []
        for b in self.bots:
            convos.extend(dg.MakeFakeDataMgr(b, self.database).RecentConversations(100))
            convos[-1].sort(key = lambda b: b.GetId())
        convos.sort(key = lambda c: -c[-1].GetId())
        return convos

    
