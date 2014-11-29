from util import *
import json
import sys
import os
import logging
import logging.handlers
import api_handler
import random
import social_logic
import socialbot
import string

class GlobalData:
    def __init__(self):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + '/english_families.json',"r") as f:
            self.englishFamilies = DictToSortedTuple(json.load(f))
        with open(abs_prefix + '/english_pos.json',"r") as f:
            self.englishPos = DictToSortedTuple(json.load(f))
        with open(abs_prefix + '/cooccuring.json',"r") as f:
            self.cooccuring = DictToSortedTuple(json.load(f))
        with open(abs_prefix + '/similar.json',"r") as f:
            self.similar = DictToSortedTuple(json.load(f))
            
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

        with open(abs_prefix + '/config.json','r') as f:
            conf = json.load(f)
            self.password       = conf['password']
            self.myName         = conf['twitter_name']
            self.authentication = conf["authentication"]
            self.apiHandler = api_handler.ApiHandler(self)
            self.read_only_mode = conf["read_only_mode"] if "read_only_mode" in conf else False

            sl_name             = conf['social_logic']['name']
            if sl_name == "TiaraBoom":
                self.socialLogic = social_logic.SocialLogic(self, conf["social_logic"])
            elif sl_name == "FollowBack":
                self.socialLogic = social_logic.FollowBackLogic(self, conf["social_logic"])
            elif sl_name == "SocialBot":
                self.socialLogic = socialbot.SocialBotLogic(self, conf["social_logic"])
            else:
                assert False
        
        self.TraceDebug("size of english_famlies.json in memory is %d, len = %d" % (sys.getsizeof(self.englishFamilies),len(self.englishFamilies)))
        self.TraceDebug("size of english_pos.json in memory is %d, len = %d" % (sys.getsizeof(self.englishPos),len(self.englishPos)))
        self.TraceDebug("size of coocurring.json in memory is %d, len = %d" % (sys.getsizeof(self.cooccuring),len(self.cooccuring)))
        self.TraceDebug("size of similar.json in memory is %d, len = %d" % (sys.getsizeof(self.similar),len(self.similar)))


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
    
    def RandomEnglishWord(self):
        return random.choice(self.englishFamilies)[0] 

    def DictLookup(self, word):
        res = BinarySearch(self.englishPos,word)
        if res:
            return res
        return []

    def EnglishWord(self, i):
        return self.englishPos[i][0]

    def NumEnglishWords(self):
        return len(self.englishPos)

    def LetterRange(self, a):
        if a == 'z':
            return BinarySearch(self.englishPos, 'z',True), self.NumEnglishWords()
        elif a == 'Z':
            return BinarySearch(self.englishPos, 'Z', True), BinarySearch(self.englishPos, 'a', True)
        elif a.islower():
            a_plus_1 = string.lowercase[ord(a)+1-ord('a')]
        else:
            a_plus_1 = string.uppercase[ord(a)+1-ord('A')]
        return BinarySearch(self.englishPos, a, True), BinarySearch(self.englishPos, a_plus_1, True)

    def FamilyRepresentative(self, word):
        res = BinarySearch(self.englishFamilies,word.lower())
        if res:
            if not isinstance(res, list):
                return res
            return word
        return None

    def WordFamily(self, word):
        res = BinarySearch(self.englishFamilies,word.lower())
        if res:
            if not isinstance(res, list):
                res = BinarySearch(self.englishFamilies, res)
            return res
        return []

    def FamilyLookup(self, word):
        return [(w,s) for w in self.WordFamily(word) for s in self.DictLookup(w)]

    def Cooccuring(self, word):
        res = BinarySearch(self.cooccuring, word.lower())
        if res:
            return res
        return []

    def Similar(self, word):
        res = BinarySearch(self.similar, word.lower())
        if res:
            return res
        return ""
