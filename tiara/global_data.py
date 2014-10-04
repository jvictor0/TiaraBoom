from sentence_gen import Sentence
from util import *
import json
import sys
import os

class GlobalData:
    def __init__(self):
        abs_prefix = os.path.join(os.path.dirname(__file__), "../data")
        with open(abs_prefix + '/english_families.json',"r") as f:
            self.englishFamilies = DictToSortedTuple(json.load(f))
        with open(abs_prefix + '/english_pos.json',"r") as f:
            self.englishPos = DictToSortedTuple(json.load(f))
        with open(abs_prefix + '/cooccuring.json',"r") as f:
            self.cooccuring = DictToSortedTuple(json.load(f))

        print "size of english_famlies.json in memory is %d, len = %d" % (sys.getsizeof(self.englishFamilies),len(self.englishFamilies))
        print "size of english_pos.json in memory is %d, len = %d" % (sys.getsizeof(self.englishPos),len(self.englishPos))
        print "size of coocurring.json in memory is %d, len = %d" % (sys.getsizeof(self.cooccuring),len(self.cooccuring))

                
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

