import random
import time
import logging
import logging.handlers
import os

class Ticker(object):
    def __init__(self, g_data, tix, fun, name='action', exponential=True, verbose = True, min_time=15):
        self.fun = fun
        self.time = 0
        self.last_time = time.time()
        self.min_time = min_time
        self.exponential = exponential
        self.SetLimit(tix)
        self.g_data = g_data
        self.name = name
        self.verbose = verbose
        if self.verbose:
            self.g_data.TraceInfo("Startup! %f minutes until first %s." % (self.limit/60, name))

    def SetLimit(self, new_avg=None):
        if not new_avg is None:
            self.avg_limit = new_avg * 60
        self.limit =  max(self.min_time, random.expovariate(1.0/self.avg_limit) if self.exponential else float(self.avg_limit))
        self.time = 0
        self.last_time = time.time()
    
    def Tick(self):
        t = time.time()
        self.time += (t - self.last_time)
        self.last_time = t
        if self.time > self.limit:
            if self.verbose:
                self.g_data.TraceInfo("Performing %s." % (self.name))
            t0 = time.time()
            self.fun()
            time_taken = time.time() - t0
            self.SetLimit()
            if self.verbose:
                self.g_data.TraceInfo("Action Performed (%f secs)! %f minutes until next %s." % (time_taken, self.limit/60, self.name))

