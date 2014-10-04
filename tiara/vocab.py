import random
import re
import util

class Vocab:
    def __init__(self, g_data):
        self.dict = { }
        self.g_data = g_data
        self.used = []

    def Add(self, tweet):
        words = re.split(r"[^a-zA-Z\'\-]", tweet)
        for w in words:
            for word, part in self.g_data.DictLookup(w):
                if word not in self.used:
                    ListInsert(self.dict, part, word)
    
    def Register(self, word):
        usedWords = self.g_data.DictLookup(word):
        for part, w in newWords:
            if w not in self.used:
                self.used.append(w)
            self.dict[part] = filter(lambda v: v != w, self.dict[part])
        for coWord, pres in self.g_data.CoOccuring(word):
            for i in xrange(pres):
                self.Add(coWord)
    
    def __getitem__(self, part):
        if part in self.dict:
            return random.choice(self.dict[part])
        return None

