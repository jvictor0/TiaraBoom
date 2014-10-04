import random

class GlobalData:
    def __init__(self):
        self.coOccuring = {}
        self.englishDict = {}
        self.sentences = []
        
                
    def NextSentence(self, query):
        return random.choice(self.sentences)
    
    def DictLookup(self, word):
        return self.englishDict[word] if word in self.englishDict else []

    def CoOccuring(self, word)
        return self.coOccuring[word] if word in self.englishDict else []
