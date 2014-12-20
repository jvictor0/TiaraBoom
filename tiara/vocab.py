import random
import re
from util import *

class Vocab:
    def __init__(self, g_data):
        self.dict = { }
        self.g_data = g_data
        self.used = []
        self.found_alliteration = False
        self.alliteration_count = 10

    def DeHashtagify(self, word):
        result = []
        for start in xrange(1, len(word)):
            for end in xrange(start, len(word)):
                if self.g_data.IsWord(word[start:end])
                result.append(word)
        return result

    def Add(self, tweet, addSimilar = False):
        words = re.split(r"[^a-zA-Z\'\-#]", tweet)
        result = 0
        for w in words:
            if w[0] == '#':
                Add(' '.join(self.DeHashtagify(w)))
                continue
            rep = self.g_data.FamilyRepresentative(w)
            if not rep is None and rep not in self.used:
                if addSimilar:
                    result += self.Add(self.g_data.Similar(rep))
                else:
                    for word, part in self.g_data.FamilyLookup(rep):
                        if not self.found_alliteration or self.IsAlliteration(word):
                            ListInsert(self.dict, part, word)
                            result += 1
        return result

    def BeginAlliterationMode(self, letter):
        self.found_alliteration = True
        self.alliteration = letter[0].lower()
        for k in self.dict.keys():
            self.dict[k] = [w for w in self.dict[k] if self.IsAlliteration(w)]

    def Register(self, word):
        rep = self.g_data.FamilyRepresentative(word)
        if rep is None:
            return
        self.used.append(rep)
        for w, part in self.g_data.FamilyLookup(rep):
            if part in self.dict:
                self.dict[part] = filter(lambda v: v != w, self.dict[part])
        for coWord, pres in self.g_data.Cooccuring(rep):
            if not self.found_alliteration or self.IsAlliteration(coWord):
                for i in xrange(pres):
                    self.Add(coWord)
    
    def __getitem__(self, part):
        if part in ["(_Kvt)","(_Kvf)"]: # verber
            result = self.Verber(part[4])
        elif part in self.dict:
            entries = self.dict[part]
            if len(entries) == 0:
                result = None
            else:
                result = random.choice(entries)
        else:
            result = None
        return result

    def AddAlliterations(self, num):
        self.alliteration_count -= 1
        if self.alliteration_count == 0:
            self.alliteration_count = 10
            self.found_alliteration = False
        if not self.found_alliteration:
            return
        word_start_range = self.g_data.LetterRange(self.alliteration)
        word_start_cap_range = self.g_data.LetterRange(self.alliteration.upper())
        word_start = random.randrange(*word_start_range)
        word_start_cap = random.randrange(*word_start_cap_range)
        for i in xrange(num):
            ix = word_start+i if i%3 != 0 else word_start_cap+i
            wsr = word_start_range if i%3 !=0 else word_start_cap_range
            if not wsr[0] <= ix < wsr[1]:
                continue
            w = self.g_data.EnglishWord(word_start+i if i%3 != 0 else word_start_cap+i)
            self.Add(w)
            

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

    def IsAlliteration(self, word):
        return word[0].lower() == self.alliteration
