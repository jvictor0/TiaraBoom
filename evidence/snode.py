import copy
import artrat.lispparse as lp

def Reload():
    pass

def Flatten(l):
    if isinstance(l, list):
        return [b for a in l for b in Flatten(a)]
    else:
        return [l]

ENTITY = "entity"
SUBJECT = "subject"
OBJECT = "object"
VERB = "verb"
FACT = "fact"
SENTENCE = "sentence"
PUNCT = "punct"
SYNTAX = "syntax"
PRONOUN = "pronoun"
    
class SNode:
    def __init__(self, tags, *children):
        self.tags = tags
        self.children = [c for c in Flatten(list(children)) if isinstance(c, str) or len(c.tags) > 0]
        if len(self.children) == 0:
            self.tags = {}

    def __getitem__(self, i):
        return self.children[i]

    def __len__(self):
        return len(self.children)
    
    def IsLeaf(self):
        return len(self) == 1 and isinstance(self[0], str)

    def Word(self):
        assert self.IsLeaf()
        return self[0]
    
    def Append(self, node):
        cs = copy.copy(self.chilrden)
        cs.append(node)
        return SNode(self.tags, *cs)

    def StrTags(self):
        newtags = copy.copy(self.tags)
        name = newtags["type"]
        del newtags["type"]
        if len(newtags) == 0:
            return name
        return "%s%s" % (name, str(newtags))        

    def Type(self):
        return self.tags["type"]
    
    def ToLisp(self):
        if self.IsLeaf():
            return lp.L(self.StrTags(), self[0])
        return lp.L(self.StrTags(), *[c.ToLisp() for c in self.children])

    def __str__(self):
        return str(self.ToLisp())
    
    def ToText(self):
        if self.IsLeaf():
            return self.Word()
        result = ""
        for i,c in enumerate(self.children):
            if i > 0 and c.tags["type"] != PUNCT:
                result += " "
            result += c.ToText()
        return result
