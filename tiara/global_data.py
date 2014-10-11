from sentence_gen import Sentence
from util import *
import json
import sys
import os
import logging
import logging.handlers
import api_handler
import social_logic

class GlobalData:
    def __init__(self, read_only_mode = False):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + '/english_families.json',"r") as f:
            self.englishFamilies = DictToSortedTuple(json.load(f))
        with open(abs_prefix + '/english_pos.json',"r") as f:
            self.englishPos = DictToSortedTuple(json.load(f))
        with open(abs_prefix + '/cooccuring.json',"r") as f:
            self.cooccuring = DictToSortedTuple(json.load(f))

        self.read_only_mode = read_only_mode

        log_format = '%(levelname)s %(asctime)s: %(message)s'
        logging.basicConfig(format=log_format)

        self.logger = logging.getLogger('TiaraBoom')
        self.tweetLogger = logging.getLogger('TiaraBoomTweets')

        self.logger.setLevel(logging.DEBUG)
        self.tweetLogger.setLevel(logging.DEBUG)
            
        two_fifty_six_meg = 256000000
        
        handler = logging.handlers.RotatingFileHandler(abs_prefix + "/tiaraboom_log", 
                                                       maxBytes=two_fifty_six_meg, 
                                                       backupCount=4)
        handler.setFormatter(logging.Formatter(log_format,"%Y-%m-%d %H:%M:%S"))
        self.logger.addHandler(handler)

        tweetHandler = logging.FileHandler(abs_prefix + "/tweet_log")
        tweetHandler.setFormatter(logging.Formatter('%(asctime)s: %(message)s', "%Y-%m-%d %H:%M:%S"))
        self.tweetLogger.addHandler(tweetHandler)

        
        self.TraceDebug("size of english_famlies.json in memory is %d, len = %d" % (sys.getsizeof(self.englishFamilies),len(self.englishFamilies)))
        self.TraceDebug("size of english_pos.json in memory is %d, len = %d" % (sys.getsizeof(self.englishPos),len(self.englishPos)))
        self.TraceDebug("size of coocurring.json in memory is %d, len = %d" % (sys.getsizeof(self.cooccuring),len(self.cooccuring)))

        self.apiHandler = api_handler.ApiHandler(self)
        self.socialLogic = social_logic.SocialLogic(self)

    def TraceDebug(self, msg):
        self.logger.debug(Indentation() + msg)
    def TraceInfo(self, msg):
        self.logger.info(Indentation() + msg)
    def TraceWarn(self, msg):
        self.logger.warn(Indentation() + msg)
    def TraceError(self, msg):
        self.logger.error(Indentation() + msg)

    def LogTweet(self, user, body, id, reply):
        self.tweetLogger.debug("%s, %d, %s, %s" % (user,id,reply,body.replace("\n"," ")))

    def ApiHandler(self):
        return self.apiHandler

    def SocialLogic(self):
        return self.socialLogic

    def NextSentence(self, query):
        return Sentence()
    
    def DictLookup(self, word):
        res = BinarySearch(self.englishPos,word)
        if res:
            return res
        return []

    def FamilyRepresentative(self, word):
        res = BinarySearch(self.englishFamilies,word)
        if res:
            if not isinstance(res, list):
                return res
            return word
        return []

    def WordFamily(self, word):
        res = BinarySearch(self.englishFamilies,word)
        if res:
            if not isinstance(res, list):
                res = BinarySearch(self.englishFamilies, res)
            return res
        return []

    def FamilyLookup(self, word):
        return [(w,s) for w in self.WordFamily(word) for s in self.DictLookup(w)]

    def Cooccuring(self, word):
        res = BinarySearch(self.cooccuring,word)
        if res:
            return res
        return []
