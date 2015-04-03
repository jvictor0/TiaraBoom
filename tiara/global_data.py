from util import *
import json
import sys
import os
import logging
import logging.handlers
import api_handler
import random
import social_logic
import string
import data_gatherer
import enchant

class EmptySocialLogic:
    def Act(self):
        pass

class GlobalData:
    def __init__(self, g_data=None, conf=None, name=None):

        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        if conf is None:
            with open(abs_prefix + '/config.json','r') as f:
                confs = json.load(f)["bots"]
                if not g_data is None:
                    name = g_data.myName
                if name is None:
                    conf = confs[0]
                else:
                    conf = [c for c in confs if c["twitter_name"] == name][0]
                
        self.invalid = False
        
        if not g_data is None:
            self.englishFamilies = g_data.englishFamilies
            self.englishPos = g_data.englishPos
            self.cooccuring = g_data.cooccuring
            self.similar = g_data.similar
            self.logger = g_data.logger
        else:            
            with open(abs_prefix + '/english_families.json',"r") as f:
                self.englishFamilies = DictToSortedTuple(json.load(f))
            with open(abs_prefix + '/english_pos.json',"r") as f:
                self.englishPos = DictToSortedTuple(json.load(f))
            with open(abs_prefix + '/cooccuring.json',"r") as f:
                self.cooccuring = DictToSortedTuple(json.load(f))
            with open(abs_prefix + '/similar.json',"r") as f:
                self.similar = DictToSortedTuple(json.load(f))

        self.enchantDict = enchant.Dict("en_US")

        if g_data is None:
            log_format = '%(levelname)s %(asctime)s: %(message)s'
            logging.basicConfig(format=log_format)

            self.logger = logging.getLogger('TiaraBoom')
            self.logger.setLevel(logging.DEBUG)
            
            two_fifty_six_meg = 256000000
        
            handler = logging.handlers.RotatingFileHandler(abs_prefix + "/tiaraboom_log", 
                                                           maxBytes=two_fifty_six_meg, 
                                                           backupCount=4)
            handler.setFormatter(logging.Formatter(log_format,"%Y-%m-%d %H:%M:%S"))
            self.logger.addHandler(handler)
            
            
        self.password       = conf['password']
        self.myName         = conf['twitter_name']
        self.authentication = conf["authentication"]
        self.apiHandler = api_handler.ApiHandler(self, self.authentication)
        self.read_only_mode = conf["read_only_mode"] if "read_only_mode" in conf else False
        if self.read_only_mode:
            self.TraceInfo("In Read Only Mode!")
        self.dbmgr = data_gatherer.DataManager(self, conf)
        
        self.socialLogic = social_logic.SocialLogic(self, conf["social_logic"])
        if self.socialLogic.invalid:
            self.invalid = True
        
        self.TraceDebug("size of english_famlies.json in memory is %d, len = %d" % (sys.getsizeof(self.englishFamilies),len(self.englishFamilies)))
        self.TraceDebug("size of english_pos.json in memory is %d, len = %d" % (sys.getsizeof(self.englishPos),len(self.englishPos)))
        self.TraceDebug("size of coocurring.json in memory is %d, len = %d" % (sys.getsizeof(self.cooccuring),len(self.cooccuring)))
        self.TraceDebug("size of similar.json in memory is %d, len = %d" % (sys.getsizeof(self.similar),len(self.similar)))


    def TraceDebug(self, msg):
        self.logger.debug(("(%s)" % self.myName) + Indentation() + msg)
    def TraceInfo(self, msg):
        self.logger.info( ("(%s)" % self.myName) + Indentation() + msg)
    def TraceWarn(self, msg):
        self.logger.warn( ("(%s)" % self.myName) + Indentation() + msg)
    def TraceError(self, msg):
        self.logger.error(("(%s)" % self.myName) + Indentation() + msg)

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

    def IsWord(self, word):
        try:
            result = self.enchantDict.check(word)
            return result
        except Exception as e:
            return False

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
