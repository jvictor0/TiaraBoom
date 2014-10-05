import random
import re
from util import *

class Vocab:
    def __init__(self, g_data):
        self.dict = { }
        self.g_data = g_data
        self.used = []

    def Add(self, tweet):
        words = re.split(r"[^a-zA-Z\'\-]", tweet)
        for w in words:
            rep = self.g_data.FamilyRepresentative(w)
            if rep not in self.used:  
                for word, part in self.g_data.FamilyLookup(rep):
                    ListInsert(self.dict, part, word)

    def Register(self, word):
        rep = self.g_data.FamilyRepresentative(word)
        self.used.append(rep)
        for w, part in self.g_data.FamilyLookup(rep):
            if part in self.dict:
                self.dict[part] = filter(lambda v: v != w, self.dict[part])
        for coWord, pres in self.g_data.Cooccuring(rep):
            for i in xrange(pres):
                self.Add(coWord)
    
    def __getitem__(self, part):
        if part in self.dict:
            entries = self.dict[part]
            if len(entries) ==0:
                return None
            return random.choice(entries)
        return None

