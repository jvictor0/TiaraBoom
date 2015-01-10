import random
import time
import logging
import logging.handlers
import os

class Ticker(object):
    def __init__(self, tix):
        self.time = 0
        self.last_time = time.time()
        self.limit = tix * 60
        self.avg_limit = tix * 60

    def Tick(self):
        t = time.time()
        self.time += (t - self.last_time)
        self.last_time = t
        while self.time > self.limit:
            self.Tock()
            self.time -= self.limit

    def Tock(self):
        pass

class VerboseExpTicker(object):
    def __init__(self, g_data, tix, name='action'):
        self.time = 0
        self.last_time = time.time()
        self.avg_limit = tix * 60
        self.g_data = g_data
        self.name = name
        self.limit = random.expovariate(1.0/self.avg_limit)
        self.g_data.TraceInfo("Startup! %f minutes until first %s." % (self.limit/60, name))

    def Tick(self):
        t = time.time()
        self.time += (t - self.last_time)
        self.last_time = t
        while self.time > self.limit:
            self.Tock()
            self.time -= self.limit
            self.limit = random.expovariate(1.0/self.avg_limit)
            self.g_data.TraceInfo("Action Performed! %f minutes until next %s." % (self.limit/60, self.name))
            return


    def Tock(self):
        pass

class LambdaTicker(VerboseExpTicker):
    def __init__(self, g_data, tix, fun, name='action'):
        super(LambdaTicker,self).__init__(g_data, tix, name),
        self.fun = fun

    def Tock(self):
        self.fun()

class LambdaStraightTicker(Ticker):
    def __init__(self, tix, fun):
        super(LambdaStraightTicker,self).__init__(tix),
        self.fun = fun

    def Tock(self):
        self.fun()


class StatsLogger(Ticker):
    def __init__(self, g_data, tix):
        super(StatsLogger,self).__init__(tix)
        self.g_data = g_data
        self.logger = logging.getLogger('Status')
        self.logger.setLevel(logging.DEBUG)
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        handler = logging.FileHandler(abs_prefix + "/status_log")
        handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s', "%Y-%m-%d %H:%M:%S"))
        self.logger.addHandler(handler)

    def Tock(self):
        me = self.g_data.ApiHandler().ShowUser(screen_name = self.g_data.myName, cache=False)
        if me is not None:
            self.logger.info("%d %d" % (me.GetFriendsCount(), me.GetFollowersCount()))
