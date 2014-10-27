import random
import re
from util import *

class Vocab:
    def __init__(self, g_data):
        self.dict = { }
        self.g_data = g_data
        self.used = []

    def Add(self, tweet, addSimilar = False):
        words = re.split(r"[^a-zA-Z\'\-]", tweet)
        for w in words:
            rep = self.g_data.FamilyRepresentative(w)
            if not rep is None and rep not in self.used:
                if addSimilar:
                    self.Add(self.g_data.Similar(rep))
                else:
                    for word, part in self.g_data.FamilyLookup(rep):
                        ListInsert(self.dict, part, word)

    def Register(self, word):
        rep = self.g_data.FamilyRepresentative(word)
        if rep is None:
            return
        self.used.append(rep)
        for w, part in self.g_data.FamilyLookup(rep):
            if part in self.dict:
                self.dict[part] = filter(lambda v: v != w, self.dict[part])
        for coWord, pres in self.g_data.Cooccuring(rep):
            for i in xrange(pres):
                self.Add(coWord)
    
    def __getitem__(self, part):
        if part in ["(_Kvt)","(_Kvf)"]: # verber
            return self.Verber(part[4])
        if part in self.dict:
            entries = self.dict[part]
            if len(entries) == 0:
                return None
            return random.choice(entries)
        return None


    def Shuffled(self, part):
        if part in self.dict:
            entries = self.dict[part]
            random.shuffle(entries)
            return entries
        return []
        
    def Verber(self, pl):
        for v in self.Shuffled("(Ht)") + self.Shuffled("(It)"):
            for vr in [v + "er", v + "r", v[:-1] + "ier", v + v[-1] + "er"]:
                if pl == 'f':
                    vr += "s"
                if "(K" + pl + ")" in self.g_data.DictLookup(vr) and not vr in self.used:
                    return vr        
        return None

