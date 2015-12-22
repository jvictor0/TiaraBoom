import artrat.lispparse as lisp
import random

class ExpansionKey:
    def __init__(self, parent, pos, brother_symbol, brother_text):
        assert isinstance(parent,str)
        assert isinstance(pos,str)
        assert isinstance(brother_symbol,str) or brother_symbol == None, type(brother_symbol)
        assert isinstance(brother_text,str) or brother_text == None, type(brother_text)
        self.parent = parent
        self.pos = pos
        self.brother_symbol = brother_symbol
        self.brother_text = brother_text

    def __hash__(self):
        return (self.parent, self.pos, self.brother_symbol, self.brother_text).__hash__()
    
    def __eq__(self, ok):
        return (self.parent, self.pos, self.brother_symbol, self.brother_text) == (ok.parent, ok.pos, ok.brother_symbol, ok.brother_text)

    def __str__(self):
        return "ExpansionKey(%s,%s,%s,%s)" % (self.parent, self.pos, self.brother_symbol, self.brother_text)
        
class ExpandableLeaf:
    def __init__(self, pos, word):
        self.pos = pos
        self.word = word
    
    def IsLeaf(self):
        return True
    
    def Lisp(self):
        return lisp.L(self.pos, self.word)

    def __str__(self):
        return "Leaf(%s,%s)" % (self.pos, self.word)

class ExpandableNode:
    def __init__(self, pos):
        self.pos = pos
    
    def IsLeaf(self):
        return False
    
    def __str__(self):
        return self.pos
    
class ExpansionUnit:
    def __init__(self, parent, pos, brother_symbol, brother_text, children):
        self.key = ExpansionKey(parent, pos, brother_symbol, brother_text)
        self.children = children

    def __str__(self):
        return "%s ->\n  (%s)" % (self.key, ", ".join(map(str,self.children)))

    def Expand(self, ctx):
        result = []
        print map(str,self.children)
        for i in xrange(len(self.children)):
            print i, len(self.children)
            if self.children[i].IsLeaf():
                result.append(self.children[i].Lisp())
                print result[-1]
            else:
                pos = self.children[i].pos
                last_pos = None if i == 0 else result[-1].POS()
                last_text = None if i == 0 else result[-1].ToText()
                if i > 0:
                    print result[-1]
                key = ExpansionKey(self.key.pos, pos, last_pos, last_text)
                lku = ctx.Lookup(key)
                result.append(lku.Expand(ctx.Down()))
        return lisp.L(self.key.pos, *result)

def FromPenn(lisp):
    result = []
    if lisp.IsLeaf():
        return []
    for i in xrange(len(lisp)):
        if lisp.At(i).IsLeaf():
            continue
        children = []
        for j in xrange(len(lisp.At(i))):
            if lisp.At(i).At(j).IsLeaf():
                children.append(ExpandableLeaf(lisp.At(i).At(j).POS(), lisp.At(i).At(j).ToText()))
            else:
                children.append(ExpandableNode(lisp.At(i).At(j).POS()))
        if i == 0:
            result.append(ExpansionUnit(lisp.POS(), lisp.At(i).POS(), None, None, children))
        else:
            result.append(ExpansionUnit(lisp.POS(), lisp.At(i).POS(), lisp.At(i-1).POS(), lisp.At(i-1).ToText(), children))
        result.extend(FromPenn(lisp.At(i)))
    return result

class CannotExpandException:
    def __init__(self, err):
        self.err = err

    def __str__(self):
        return "CannotExpandException(%s)" % self.err

def ToyContextFromLisps(lisps):
    result = ToyContext()
    for l in lisps:
        for eu in FromPenn(l):
            result.Insert(eu)
    return result

class ToyContext:
    def __init__(self):
        self.dct = {}
        self.height = 0
        
    def Insert(self, eu):
        if eu.key not in self.dct:
            self.dct[eu.key] = []
        self.dct[eu.key].append(eu)

    def Lookup(self, key):
        print "Lookup(%s)" % key
        if key in self.dct:
            result = random.choice(self.dct[key])
            print result
            return result
        raise CannotExpandException("Lookup(%s)" % key)

    def Down(self):
        result = ToyContext()
        result.dct = self.dct
        result.height = self.height + 1
        return result

    def Generate(self):
        return self.Lookup(random.choice(self.dct.keys())).Expand(self)
